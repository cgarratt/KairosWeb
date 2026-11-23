"""WebAuthn for the PWA's single portfolio account."""
import hashlib
import json
import os
from functools import lru_cache
from urllib.parse import urlsplit

import psycopg
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


def public_origin():
    origin = os.getenv('KAIROS_PUBLIC_ORIGIN') or (
        'https://' + os.environ['RENDER_EXTERNAL_HOSTNAME']
        if os.getenv('RENDER_EXTERNAL_HOSTNAME') else ''
    )
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return None
    if (parsed.scheme == 'https' and parsed.hostname and parsed.netloc == parsed.hostname
            and parsed.path in ('', '/') and not parsed.query and not parsed.fragment):
        return 'https://' + parsed.hostname
    return None


def enabled():
    return bool(os.getenv('KAIROS_PASSKEY_DATABASE_URL') and public_origin())


@lru_cache(maxsize=1)
def _initialize(database_url):
    with psycopg.connect(database_url, connect_timeout=4) as db:
        db.execute('SELECT pg_advisory_xact_lock(43891274)')
        db.execute('''CREATE TABLE IF NOT EXISTS kairos_pwa_passkeys (
            account text PRIMARY KEY, credential_id bytea NOT NULL,
            public_key bytea NOT NULL, sign_count bigint NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS kairos_pwa_passkey_challenges (
            account text NOT NULL, binding text NOT NULL, action text NOT NULL,
            challenge bytea NOT NULL, expires_at timestamptz NOT NULL,
            PRIMARY KEY (account, binding, action)
        )''')


def _connect():
    database_url = os.environ['KAIROS_PASSKEY_DATABASE_URL']
    _initialize(database_url)
    return psycopg.connect(database_url, connect_timeout=4)


class PasskeyUnavailable(ValueError):
    pass


class Passkeys:
    def __init__(self, origin, credential_tag, binding):
        self.origin = origin
        self.rp_id = urlsplit(origin).hostname
        self.account = hashlib.sha256(f'{origin}|{credential_tag}'.encode()).hexdigest()
        self.binding = binding

    def _lock(self, db):
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s)::bigint)', (self.account,))

    def options(self, action, username):
        with _connect() as db:
            self._lock(db)
            db.execute('DELETE FROM kairos_pwa_passkey_challenges WHERE expires_at <= now()')
            row = db.execute(
                'SELECT credential_id FROM kairos_pwa_passkeys WHERE account = %s', (self.account,)
            ).fetchone()
            descriptors = [PublicKeyCredentialDescriptor(id=row[0])] if row else []
            if action == 'register':
                options = generate_registration_options(
                    rp_id=self.rp_id, rp_name='Kairos', user_name=username,
                    user_id=bytes.fromhex(self.account), timeout=120000,
                    exclude_credentials=descriptors,
                    authenticator_selection=AuthenticatorSelectionCriteria(
                        authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                        resident_key=ResidentKeyRequirement.REQUIRED,
                        user_verification=UserVerificationRequirement.REQUIRED,
                    ),
                )
            else:
                if not row:
                    raise PasskeyUnavailable('Activa primero una llave de acceso desde Portafolio.')
                options = generate_authentication_options(
                    rp_id=self.rp_id, allow_credentials=descriptors, timeout=120000,
                    user_verification=UserVerificationRequirement.REQUIRED,
                )
            db.execute('''INSERT INTO kairos_pwa_passkey_challenges
                          (account, binding, action, challenge, expires_at)
                          VALUES (%s, %s, %s, %s, now() + interval '2 minutes')
                          ON CONFLICT (account, binding, action) DO UPDATE
                          SET challenge = EXCLUDED.challenge, expires_at = EXCLUDED.expires_at''',
                       (self.account, self.binding, action, options.challenge))
        return json.loads(options_to_json(options))

    def verify(self, action, credential):
        failure = None
        with _connect() as db:
            self._lock(db)
            challenge = db.execute('''DELETE FROM kairos_pwa_passkey_challenges
                 WHERE account = %s AND binding = %s AND action = %s AND expires_at > now()
                 RETURNING challenge''', (self.account, self.binding, action)).fetchone()
            if challenge is None:
                raise PasskeyUnavailable('La solicitud caducó. Vuelve a intentarlo.')
            try:
                self._verify_credential(db, action, challenge[0], credential)
            except (WebAuthnException, ValueError, KeyError, TypeError) as exc:
                # Commit challenge consumption even after a rejected assertion.
                failure = exc
        if failure is not None:
            raise failure

    def _verify_credential(self, db, action, challenge, credential):
        if not isinstance(credential, dict):
            raise ValueError('Missing credential')
        checks = dict(credential=credential, expected_challenge=challenge,
                      expected_rp_id=self.rp_id, expected_origin=self.origin,
                      require_user_verification=True)
        if action == 'register':
            result = verify_registration_response(**checks)
            db.execute('''INSERT INTO kairos_pwa_passkeys VALUES (%s, %s, %s, %s)
                          ON CONFLICT (account) DO UPDATE SET credential_id = EXCLUDED.credential_id,
                          public_key = EXCLUDED.public_key, sign_count = EXCLUDED.sign_count''',
                       (self.account, result.credential_id, result.credential_public_key, result.sign_count))
            return
        row = db.execute('''SELECT credential_id, public_key, sign_count
                            FROM kairos_pwa_passkeys WHERE account = %s''', (self.account,)).fetchone()
        if not row or row[0] != base64url_to_bytes(credential['rawId']):
            raise PasskeyUnavailable('Llave de acceso desconocida.')
        result = verify_authentication_response(**checks, credential_public_key=row[1],
                                                credential_current_sign_count=row[2])
        db.execute('UPDATE kairos_pwa_passkeys SET sign_count = %s WHERE account = %s',
                   (result.new_sign_count, self.account))

    def revoke(self):
        with _connect() as db:
            self._lock(db)
            db.execute('DELETE FROM kairos_pwa_passkey_challenges WHERE account = %s', (self.account,))
            db.execute('DELETE FROM kairos_pwa_passkeys WHERE account = %s', (self.account,))
