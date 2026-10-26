"""Release regression for a single portfolio dashboard and verified BTC denomination."""
from pathlib import Path
from math import isclose
import pytest
from portfolio_unrealized import btc_equivalent, portfolio_allocation

ROOT=Path(__file__).resolve().parents[1]

def test_physical_cash_and_trading_reserve_not_double_counted():
    btc_price=100000.
    rows=[{'token':x,'value':float(i+1)} for i,x in enumerate(('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PLUME','VIRTUAL','PEPE'))]
    crypto=sum(r['value'] for r in rows)
    physical_usdt=22545.
    qf=7225.
    alloc=portfolio_allocation(rows,physical_usdt)
    assert alloc['total']==crypto+physical_usdt
    assert alloc['physical_cash']==physical_usdt
    assert isclose(btc_equivalent(alloc['total'],btc_price), (crypto+physical_usdt)/btc_price)
    assert not isclose(btc_equivalent(alloc['total'],btc_price), (crypto+physical_usdt+qf)/btc_price)

def test_btc_quote_fail_closed():
    for total,quote in ((100,0),(100,-1),(100,float('nan')),(-3,50000),('100',50000),(100,'50000')):
        with pytest.raises(ValueError):btc_equivalent(total,quote)
    assert btc_equivalent(0,100000)==0.0

def test_single_navigation_and_routes():
    app=(ROOT/'app.py').read_text()
    nav=(ROOT/'templates/base.html').read_text()
    assert 'return redirect(url_for(\'integral_portfolio_page\')' in app
    assert '@app.route(\'/mode/portafolio\')' in app
    assert not (ROOT/'templates/index.html').exists()
    assert '>Dashboard</a>' not in nav
    assert "'name':'Portafolio'" in app
    assert "'total_btc_equivalent':total_btc_equivalent" in app
    assert "'btc_usdt_spot':btc_usdt_spot" in app

def test_replaced_history_with_bsi_and_token_classification():
    html=(ROOT/'templates/portfolio_integral.html').read_text()
    assert html.count('data-bsi-chart="archived"')==1
    assert 'BTC Strength Index (BSI)' in html
    assert 'BSI SELL BLOQUEADO' in html
    assert '09_BSI' in html
    assert 'data-history-chart' not in html
    assert 'history-chart-surface' not in html
    assert '/api/portfolio-repricing' not in html
    assert '<details' not in html
    assert 'data-portfolio-executive="12"' in html
    assert 'data-status=' in html
    assert 'port-coin-logo' in html
    assert 'btc-portfolio-total' in html
    assert 'Equivalencia total BTC' in html

def test_deployed_asset_contract_prevents_stale_dashboard():
    app=(ROOT/'app.py').read_text()
    assert "APP_VERSION = '2.0.55'" in app
    assert 'consolidated_dashboard_v2027' in app
    assert 'fixed_basket_repricing_ui' not in app
    assert "@app.route('/api/portfolio-repricing')" not in app
    assert "row['status']='SOBRE'" in app
    assert "else 'NEUTRAL'" in app
