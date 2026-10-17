"""v1.8.0 acceptance: executable behavior changes and display-only privacy."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
def test_dashboard_fields_and_price_precision():
    html=(ROOT/'templates/index.html').read_text()
    heads=re.findall(r'<thead><tr>(.*?)</tr></thead>',html,re.S)
    assert heads
    assert re.findall(r'<th>([^<]+)</th>',heads[-1])==[
        'Token','Estado','Unidades','Peso','Target','Precio Spot','Valor USDT','Valor BTC','Precio Medio','Rentabilidad']
    assert 'data-public-price="true"' in html
    assert 'maximumFractionDigits:5' in html
    app=(ROOT/'app.py').read_text()
    assert "'avg_cost':float(COST_BASIS[market_key])" in app
    assert "'pnl_pct':(price/float(COST_BASIS[market_key])-1)*100" in app

def test_settings_pivots_six_and_historic_reference_preserved_in_backend():
    js=(ROOT/'static/settings_master.js').read_text()
    m=re.search(r"pivots:\[(.*?)\]\};",js,re.S)
    assert m,m
    assert len(re.findall(r"\['(?:cycle_low|o[1-5])'",m.group(1)))==6
    assert "['c1_reference'" not in m.group(1)
    assert "['c2_reference'" not in m.group(1)
    back=(ROOT/'kairos_sheets_features.py').read_text()
    assert "('c1_reference',11)" in back and "('c2_reference',12)" in back

def test_buy_cards_only_fibo_tranches_and_sales_below_charts():
    html=(ROOT/'templates/trade_sim.html').read_text()
    assert 'id="buy-stage1"' not in html and 'id="buy-stage2"' not in html
    for j in range(4):assert f'id="buy-tranche-{j}"' in html
    assert html.index('id="alloc-chart"') < html.index('id="after-cash"') < html.index('<h2>Candidatos SELL</h2>')
    assert 'Etapa 1 (balanceo)' in html # calculation explanatory text remains

def test_privacy_toggle_all_pages_no_write():
    base=(ROOT/'templates/base.html').read_text()
    js=(ROOT/'static/privacy.js').read_text()
    assert 'id="privacy-toggle"' in base
    assert 'filename=\'privacy.js\'' in base
    assert 'sessionStorage' in js and 'MutationObserver' in js
    assert '*****' in js and 'data-public-price' in js
    assert 'fetch(' not in js

def test_version():
    text=(ROOT/'app.py').read_text()
    assert 'APP_VERSION = "1.9.0"' in text
    assert "'version':APP_VERSION" in text
