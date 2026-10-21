"""Regression guard for Configuration's one-time admin entry and mobile-only tooltip removal."""
from pathlib import Path
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]


def test_entire_configuration_requires_one_administrator_login():
    app = (ROOT / 'app.py').read_text(encoding='utf-8')
    js = (ROOT / 'static/settings_master.js').read_text(encoding='utf-8')
    html = (ROOT / 'templates/admin_login.html').read_text(encoding='utf-8')
    assert "@app.route('/settings')" in app
    assert "if not _admin_authorized():\n        tab = request.args.get('tab', '')" in app
    assert "return redirect(url_for('admin_login'" in app
    assert "@app.route('/api/settings/data')\ndef get_settings_data():\n    if not _admin_authorized():" in app
    assert "return redirect(_settings_destination(selected_tab))" in app
    assert "session['csrf_token']=secrets.token_urlsafe(32)" in app
    assert 'settings-admin-link' not in js
    assert "window.location.replace('/admin/login?tab='+encodeURIComponent(tab))" in js
    assert "window.location.assign('/admin/login')" in js
    assert 'name="login_csrf"' in html
    assert 'Volver a Portafolio' in html
    assert "url_for('admin_login', tab=settings_tab)" in html


def test_mobile_tooltips_disabled_but_desktop_restores():
    js=(ROOT/'static/tooltips.js').read_text(encoding='utf-8')
    css=(ROOT/'static/theme.css').read_text(encoding='utf-8')
    assert "(hover: none) and (pointer: coarse)" in js
    assert '(max-width: 680px)' in js
    assert 'node.removeAttribute(\'title\')' in js
    assert "node.setAttribute('title',previousTitles.get(node))" in js
    assert 'if(isMobile()){hide();return;}' in js
    assert '.kairos-tap-tooltip{display:none!important}' in css
    assert "node.getAttribute('aria-label')" in js  # preserved for screen readers


def test_login_template_is_valid_jinja():
    Environment().parse((ROOT/'templates/admin_login.html').read_text(encoding='utf-8'))
