"""Browser-origin and login-CSRF regression tests (no real credentials)."""
from pathlib import Path
from admin_origin import same_origin_allowed

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
