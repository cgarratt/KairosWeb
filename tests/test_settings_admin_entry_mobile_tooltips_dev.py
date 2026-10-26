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


def test_two_tier_session_and_guest_redaction_on_server():
    script=(ROOT/'app.py').read_text(encoding='utf-8')
    guest=(ROOT/'templates/guest_portfolio.html').read_text(encoding='utf-8')
    login=(ROOT/'templates/portfolio_login.html').read_text(encoding='utf-8')
    base=(ROOT/'templates/base.html').read_text(encoding='utf-8')
    assert "if path in ('/', '/mode/portafolio'):" in script
    assert "return render_template('guest_portfolio.html'" in script
    assert 'PORTFOLIO_AUTH_REQUIRED' in script
    assert "if not _portfolio_authorized():" in script
    assert "session['kairos_portfolio'] = True" in script
    assert "session['kairos_admin']=True" in script
    assert "_portfolio_authorized() and app.secret_key" in script
    assert "admin_login_at" in script
    assert "request.form.get('login_csrf'" in script
    assert "secrets.compare_digest(password, expected_password)" in script
    assert 'WWW-Authenticate' not in script  # no browser-level Basic prompt
    assert 'Requiere acceso de usuario' in guest
    assert 'SALDOS OCULTOS' in guest
    assert 'spot' not in guest.lower()
    assert 'g.kairos_state' not in guest
    assert 'name="username"' in login and 'name="password"' in login
    assert "if portfolio_authenticated" in base
    assert "@app.route('/logout', methods=['GET', 'POST'])" in script
    assert "session.pop('kairos_admin', None)" in script
    for t in ['portfolio_login.html','guest_portfolio.html','portfolio_integral.html','base.html']:
        Environment().parse((ROOT/'templates'/t).read_text())

def test_portfolio_title_single_word_and_http_diagnostics():
    script=(ROOT/'app.py').read_text(encoding='utf-8')
    html=(ROOT/'templates/portfolio_integral.html').read_text(encoding='utf-8')
    assert '<h2>Portafolio</h2>' in html
    assert 'http_status' in html
    assert "'http_status':info.get('http_status')" in script


# Legacy release contracts consolidated to keep GitHub ZIP <= 100 files.

def test_release_v2019_identity_and_preserved_functions():
    source=(ROOT/'app.py').read_text()
    assert "APP_VERSION = '2.0.54'" in source
    assert "'portfolio_unrealized_chart':" in source
    assert "'sales_optimizer_engine':" in source
    assert "'sales_optimizer_ui':" in source
    assert "'buy_postweight_color_ui':" in source
    assert "'SELL_REST_MINIMIZE_SQUARED_PP_DRIFT'" in source
    assert "request.args.get('usdt_pct')" in source
    assert (ROOT/'static/sales_optimizer.js').exists()


def test_sales_proposal_without_redundant_weight_table():
    view=(ROOT/'templates/trade_sim.html').read_text()
    assert 'Pesos antes / objetivo / después (12 tokens)' not in view
    assert 'sell-weight-body' not in view
    assert 'id="sim-body"' in view and 'sell-plan-status' in view
    assert 'p.after_pct.toFixed(2)' in view
    from jinja2 import Environment
    Environment().parse(view)


# Consolidated settings token/logo regression tests (archive test path removed only).

def test_logos_for_all_tokens_and_alias_only():
    js = (ROOT/'static/settings_master.js').read_text()
    for code in ('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PUMPFUN','PLUME','PEPE','VIRTUAL'):
        assert code+':' in js
    assert 'settingsTokenLabel(rec.token)' in js
    assert "(tab==='units'||tab==='targets')&&entry.token" in js
    assert "img.addEventListener('error'" in js
    assert "else primary.append(el('strong','token-name',tab==='capital_targets'" in js

def test_styles_are_shared_with_dark_mode():
    css=(ROOT/'static/theme.css').read_text()
    assert '.settings-token-identity' in css
    assert '.settings-coin-icon' in css
    assert '.settings-pivot-token' in css
