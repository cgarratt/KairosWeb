"""Browser-origin and login-CSRF regression tests (no real credentials)."""
from pathlib import Path
from admin_origin import same_origin_allowed, valid_logout_csrf

HOST='kairos-web-zddl.onrender.com'
ORIGIN='https://kairos-web-zddl.onrender.com'


def test_normal_chrome_post_with_origin():
    assert same_origin_allowed(request_host=HOST,origin=ORIGIN,fetch_site='same-origin')


def test_browser_post_with_only_referer():
    assert same_origin_allowed(request_host=HOST,referer=ORIGIN+'/admin/login',fetch_site='same-origin')


def test_browser_private_no_referer_but_fetch_metadata():
    assert same_origin_allowed(request_host=HOST,origin='null',fetch_site='same-origin')


def test_csrf_protected_login_allows_privacy_redacted_headers():
    assert same_origin_allowed(request_host=HOST,origin='null',csrf_protected_login=True)
    assert not same_origin_allowed(request_host=HOST,origin='null')


def test_cross_site_never_allowed_even_with_csrf():
    assert not same_origin_allowed(request_host=HOST,origin='https://evil.example',referer=ORIGIN,fetch_site='same-origin',csrf_protected_login=True)
    assert not same_origin_allowed(request_host=HOST,origin=ORIGIN,fetch_site='cross-site',csrf_protected_login=True)
    assert not same_origin_allowed(request_host=HOST,fetch_site='same-site',csrf_protected_login=True)


def test_unrelated_forged_referer_rejected():
    assert not same_origin_allowed(request_host=HOST,referer='https://evil.example/login',fetch_site='same-origin')


def test_reverse_proxy_internal_host_accepts_render_public_host():
    assert same_origin_allowed(request_host='localhost:10000',origin=ORIGIN,render_host=HOST,fetch_site='same-origin')


def test_api_write_with_no_provenance_remains_rejected():
    assert not same_origin_allowed(request_host=HOST)
    assert not same_origin_allowed(request_host=HOST,origin='null')


def test_http_external_rejected():
    assert not same_origin_allowed(request_host=HOST,origin='http://'+HOST)


def test_admin_login_form_uses_csrf_and_referrer_policy():
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text(encoding='utf-8')
    html=(root/'templates/admin_login.html').read_text(encoding='utf-8')
    assert 'name="login_csrf"' in html
    assert "session['login_csrf']=login_csrf" in app
    assert 'secrets.compare_digest(saved_token,supplied_token)' in app
    assert "resp.headers['Referrer-Policy'] = 'same-origin'" in app
    assert 'session[\'csrf_token\']=secrets.token_urlsafe(32)' in app


def test_logout_csrf_is_not_the_api_header_only_gate():
    assert valid_logout_csrf('token-123', 'token-123')
    assert not valid_logout_csrf('token-123', 'different')
    assert not valid_logout_csrf('token-123', '')
    assert not valid_logout_csrf('', 'token-123')

def test_logout_post_is_guarded_and_independent_of_sheets():
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text(encoding='utf8')
    base=(root/'templates/base.html').read_text(encoding='utf8')
    assert "@app.route('/logout', methods=['GET', 'POST'])" in app
    assert "request.form.get('csrf'" in app
    assert 'valid_logout_csrf(saved, given)' in app
    assert "session['logout_csrf'] = secrets.token_urlsafe(32)" in app
    assert "if not _same_origin() or not valid_logout_csrf(saved, given):" in app
    assert "return redirect(url_for('integral_portfolio_page'), code=303)" in app
    assert "('/login','/logout','/admin/login','/api/admin/session')" in app
    assert "('/login', '/logout', '/api/modes')" in app
    assert 'name="csrf" value="{{ portfolio_csrf }}"' in base

def test_admin_origin_remains_strict_for_logout_form():
    assert same_origin_allowed(request_host=HOST, origin=ORIGIN, fetch_site='same-origin')
    assert not same_origin_allowed(request_host=HOST, origin='https://attacker.example', fetch_site='cross-site')


def test_real_logout_handler_control_flow_without_external_flask():
    # Exercise the real handler's AST with narrow fakes, not a copied reimplementation.
    import ast
    from types import SimpleNamespace
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'app.py').read_text(encoding='utf8')
    module=ast.parse(source)
    fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='portfolio_logout')
    fn.decorator_list=[]
    env={'valid_logout_csrf':valid_logout_csrf, 'url_for':lambda n:'/',
         'jsonify':lambda value:value, 'redirect':lambda target,code=302:('redirect',target,code)}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'logout_real_handler','exec'),env)
    handler=env['portfolio_logout']
    # A successful same-origin form POST invalidates both user and admin sessions.
    data={'kairos_portfolio':True,'kairos_admin':True,'logout_csrf':'secret'}
    env.update({'session':data,'request':SimpleNamespace(method='POST',form={'csrf':'secret'}),
                '_portfolio_authorized':lambda:True, '_same_origin':lambda:True})
    assert handler()==('redirect','/',303)
    assert data=={}
    # Forgery, even with a valid cookie, never clears a session.
    data={'kairos_portfolio':True,'logout_csrf':'secret'}
    env.update({'session':data,'request':SimpleNamespace(method='POST',form={'csrf':'wrong'})})
    assert handler()==({'status':'FORBIDDEN','reason':'LOGOUT_CSRF_OR_ORIGIN'},403)
    assert data['kairos_portfolio']
    # GET never logs out (regardless of origins).
    env.update({'session':data,'request':SimpleNamespace(method='GET',form={})})
    assert handler()==('redirect','/',302)
    assert data['kairos_portfolio']
    # Old v2.0.36 sessions fall back to the previous csrf_token.
    data={'kairos_portfolio':True,'csrf_token':'legacy'}
    env.update({'session':data,'request':SimpleNamespace(method='POST',form={'csrf':'legacy'})})
    assert handler()==('redirect','/',303)
    assert data=={}


def _auth_functions():
    """Run the real authorization functions without requiring a Flask import."""
    import ast
    from types import SimpleNamespace
    import math
    import time
    import hashlib
    import hmac
    module = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf8'))
    defs = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in
            {'_session_time_valid', '_portfolio_authorized', '_admin_authorized', '_credential_tag'}]
    scope = {'math': math, 'time': time, 'os': __import__('os'), 'hmac': hmac, 'hashlib': hashlib,
             'app': SimpleNamespace(secret_key='stable-test-signing-key')}
    exec(compile(ast.Module(body=defs, type_ignores=[]), 'auth_real_handlers', 'exec'), scope)
    scope.update(PORTFOLIO_IDLE_SECONDS=30*24*3600,
                 PORTFOLIO_SESSION_ONLY_IDLE_SECONDS=12*3600,
                 SESSION_ACTIVITY_WRITE_SECONDS=3600, ADMIN_ELEVATION_SECONDS=1800)
    return scope


def test_remembered_login_30_days_idle_and_rolling_renewal(monkeypatch):
    from types import SimpleNamespace
    scope = _auth_functions()
    monkeypatch.setenv('KAIROS_WEB_PASSWORD', 'fake-password')
    start = 1_800_000_000.0
    cookies = {'kairos_portfolio': True, 'portfolio_remember_me': True,
               'portfolio_credential_tag': scope['_credential_tag']('portfolio'),
               'portfolio_login_at': start, 'portfolio_seen_at': start}
    scope['session'] = cookies
    scope['time'] = SimpleNamespace(time=lambda: start + 25*24*3600)
    assert scope['_portfolio_authorized']() is True
    assert cookies['portfolio_seen_at'] == start+25*24*3600  # rolling activity
    scope['time'] = SimpleNamespace(time=lambda: start + 55*24*3600 + 2)
    assert scope['_portfolio_authorized']() is False  # >30d since last activity
    assert cookies == {}
    cookies.update(kairos_portfolio=True, portfolio_remember_me=True,
                   portfolio_credential_tag=scope['_credential_tag']('portfolio'),
                   portfolio_login_at=start, portfolio_seen_at=start+89*24*3600)
    scope['time'] = SimpleNamespace(time=lambda: start+90*24*3600)
    assert scope['_portfolio_authorized']() is True  # active users remain signed in


def test_session_only_expires_after_12_hours(monkeypatch):
    from types import SimpleNamespace
    scope = _auth_functions()
    monkeypatch.setenv('KAIROS_WEB_PASSWORD', 'fake-password')
    start = 1_800_000_000.0
    session_data = {'kairos_portfolio': True, 'portfolio_remember_me': False,
                    'portfolio_credential_tag': scope['_credential_tag']('portfolio'),
                    'portfolio_login_at': start, 'portfolio_seen_at': start}
    scope['session'] = session_data
    scope['time'] = SimpleNamespace(time=lambda: start+13*3600)
    assert not scope['_portfolio_authorized']()
    assert session_data == {}


def test_admin_elevation_independent_and_expired(monkeypatch):
    from types import SimpleNamespace
    scope = _auth_functions()
    monkeypatch.setenv('KAIROS_WEB_PASSWORD', 'fake-password')
    monkeypatch.setenv('KAIROS_SETTINGS_ADMIN_KEY', 'fake-admin-password')
    start = 1_800_000_000.0
    session_data = {'kairos_portfolio': True, 'portfolio_remember_me': True,
                    'portfolio_credential_tag': scope['_credential_tag']('portfolio'),
                    'admin_credential_tag': scope['_credential_tag']('admin'),
                    'portfolio_login_at': start, 'portfolio_seen_at': start,
                    'kairos_admin': True, 'admin_login_at': start}
    scope['session'] = session_data
    scope['time'] = SimpleNamespace(time=lambda: start+1799)
    assert scope['_admin_authorized']()
    scope['time'] = SimpleNamespace(time=lambda: start+1801)
    assert not scope['_admin_authorized']()
    assert 'kairos_admin' not in session_data
    assert scope['_portfolio_authorized']() is True


def test_remember_checkbox_and_secure_cookie_rules():
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text(encoding='utf8')
    login=(root/'templates/portfolio_login.html').read_text(encoding='utf8')
    assert 'name="remember_me" value="on" checked' in login
    assert "session.permanent = remember" in app
    assert "session.permanent=True\n            session['kairos_admin']" not in app
    assert 'SESSION_REFRESH_EACH_REQUEST=True' in app
    assert 'PERMANENT_SESSION_LIFETIME=timedelta(days=30)' in app
    assert "SESSION_COOKIE_SECURE=True" in app
    assert "SESSION_COOKIE_HTTPONLY=True" in app
    assert "SESSION_COOKIE_SAMESITE='Strict'" in app
    assert "session.clear()  # Both user and admin levels are invalidated." in app


def test_password_rotation_revokes_remembered_cookie(monkeypatch):
    from types import SimpleNamespace
    scope = _auth_functions()
    monkeypatch.setenv('KAIROS_WEB_PASSWORD','old-secret-not-a-real-password')
    issued = 1_800_000_000.0
    cookie = {'kairos_portfolio':True, 'portfolio_remember_me':True,
              'portfolio_credential_tag': scope['_credential_tag']('portfolio'),
              'portfolio_login_at':issued, 'portfolio_seen_at':issued}
    scope['session'] = cookie
    scope['time'] = SimpleNamespace(time=lambda: issued+300)
    assert scope['_portfolio_authorized']() is True
    monkeypatch.setenv('KAIROS_WEB_PASSWORD','new-secret-not-a-real-password')
    assert scope['_portfolio_authorized']() is False
    assert cookie == {}
