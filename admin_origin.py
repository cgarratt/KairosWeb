"""Strict, proxy-aware origin policy for KairosWeb administrative requests.

A browser may suppress Origin/Referer due to privacy settings.  In that
case only a login POST carrying an independent, same-session CSRF token is
allowed; a cross-site Fetch Metadata header remains an unconditional reject.
"""
from urllib.parse import urlsplit
import secrets


def allowed_origin_hosts(request_host, *, render_host=None, public_origin=None):
    hosts = set()
    raw = [request_host, render_host]
    if public_origin:
        raw.append(public_origin)
    for item in raw:
        item = (item or '').strip()
        if not item:
            continue
        try:
            url = urlsplit(item if '://' in item else 'https://' + item)
            if url.username or url.password or not url.hostname:
                continue
            host = url.netloc.lower()
            # The configured public URL cannot broaden acceptance to HTTP.
            if url.scheme in ('http', 'https'):
                hosts.add(host)
        except ValueError:
            continue
    return hosts


def same_origin_allowed(*, request_host, origin='', referer='', fetch_site='',
                        render_host=None, public_origin=None,
                        csrf_protected_login=False):
    """Return whether a write came from the same site, without bypassing CSRF.

    For endpoints with no CSRF token, an explicit matching Origin/Referer or
    the browser-controlled Sec-Fetch-Site:same-origin is required.  The lone
    exception is the login form, protected with a one-time session CSRF token,
    when browsers omit or redact the optional origin metadata.
    """
    site = (fetch_site or '').strip().lower()
    if site in ('cross-site', 'same-site'):
        return False
    hosts = allowed_origin_hosts(request_host, render_host=render_host,
                                  public_origin=public_origin)
    if not hosts:
        return False

    def is_ours(raw):
        try:
            u = urlsplit(raw)
        except ValueError:
            return False
        if not u.netloc or u.username or u.password:
            return False
        if u.netloc.lower() not in hosts:
            return False
        if u.scheme == 'https':
            return True
        return u.scheme == 'http' and (u.hostname in ('localhost', '127.0.0.1'))

    ori = (origin or '').strip()
    ref = (referer or '').strip()
    # A real, explicit mismatch is never overruled by Referer or Fetch Metadata.
    if ori and ori.lower() != 'null':
        return is_ours(ori)
    if ref:
        return is_ours(ref)
    if site == 'same-origin':
        return True
    # Only a form carrying an authenticated, same-session login CSRF token may
    # fall back when *all* provenance metadata is missing or redacted.
    return bool(csrf_protected_login and site in ('', 'none'))


def valid_logout_csrf(expected, submitted):
    """A separate, same-session HTML form CSRF gate for portfolio logout."""
    return bool(expected and submitted and secrets.compare_digest(expected, submitted))
