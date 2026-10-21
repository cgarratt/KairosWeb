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

def test_layout_one_history_and_btc_kpi():
    html=(ROOT/'templates/portfolio_integral.html').read_text()
    assert html.count('id="history-chart-surface"')==1
    assert 'tracking-chart-surface' not in html
    assert 'data-history-display="percent"' in html
    assert 'data-history-display="usdt"' in html
    assert 'data-portfolio-executive="12"' in html
    assert 'btc-portfolio-total' in html
    assert 'Equivalencia total BTC' in html
    assert 'data-bsi-summary="informative"' in html
    assert 'Presupuesto O2C2</small>' not in html
