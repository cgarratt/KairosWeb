"""Synthetic numerical and HTML regression tests: never screenshot-derived balances."""
import math
from pathlib import Path
import sys
from jinja2 import Environment, FileSystemLoader
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio_unrealized import summarize_unrealized

ROOT=Path(__file__).resolve().parents[1]


def synthetic_rows():
    return [
        {'token': 'BTC', 'units': 2.0, 'price': 120, 'avg_cost': 100},
        {'token': 'ETH', 'units': 4.0, 'price': 40, 'avg_cost': 50},
        {'token': 'SOL', 'units': 0.0, 'price': 80, 'avg_cost': None},
    ]


def test_unrealized_signs_and_cash_not_counted():
    report=summarize_unrealized(synthetic_rows())
    assert report['status']=='OK'
    assert [x['token'] for x in report['items']]==['BTC','ETH','SOL']
    assert [x['pnl_usdt'] for x in report['items']]==[40.0,-40.0,0.0]
    assert report['cost_open_usdt']==400.0
    assert report['total_usdt']==0.0
    assert report['total_pct']==0.0
    assert report['items'][0]['bar_pct']==100
    assert report['items'][1]['bar_pct']==100
    assert report['items'][2]['status']=='ZERO'


def test_unrealized_total_not_sum_of_rounded_token_rows():
    rows=[{'token':'A', 'units':.01, 'price':1.2, 'avg_cost':1},
          {'token':'B', 'units':.01, 'price':1.2, 'avg_cost':1},
          {'token':'C', 'units':.01, 'price':1.2, 'avg_cost':1}]
    summary=summarize_unrealized(rows)
    assert summary['total_usdt']==0.01  # Accumulate precise P&L then round once
    assert all(x['pnl_usdt']==0.0 for x in summary['items'])


def test_missing_cost_is_not_interpreted_as_zero_pnl():
    rows=synthetic_rows()
    rows[1]['avg_cost']=None
    report=summarize_unrealized(rows)
    assert report['status']=='PARCIAL'
    assert report['total_usdt'] is None
    assert report['total_pct'] is None
    assert report['items'][1]['pnl_usdt'] is None
    assert report['missing_tokens']==['ETH']


def test_invalid_nonfinite_quotes_do_not_create_bars():
    rows=synthetic_rows()
    rows[0]['price']=math.inf
    rows[1]['avg_cost']=float('nan')
    rows[2]['units']=-1
    report=summarize_unrealized(rows)
    assert report['status']=='PARCIAL'
    assert report['missing_tokens']==['BTC','ETH','SOL']
    assert not any(x['bar_pct'] for x in report['items'])


def test_all_twelve_tokens_represented_in_master_order():
    tokens='BTC ETH SOL LINK HYPE HBAR SUI ONDO PUMP PLUME VIRTUAL PEPE'.split()
    report=summarize_unrealized([
        {'token':t, 'units':1, 'price':i+2., 'avg_cost':i+1.} for i,t in enumerate(tokens)])
    assert report['status']=='OK'
    assert len(report['items'])==12
    assert [x['token'] for x in report['items']]==tokens
    assert report['total_usdt']==12


def chart_section():
    source=(ROOT/'templates/portfolio_integral.html').read_text()
    start=source.index('<section class="panel span-12" data-portfolio-chart="unrealized">')
    end=source.index('<section class="span-12"><div class="integral-grid">',start)
    return Environment(loader=FileSystemLoader(ROOT/'templates')).from_string(source[start:end])


def test_chart_template_positive_negative_zero_and_fallback():
    t=chart_section()
    rendered=t.render(pnl_report=summarize_unrealized(synthetic_rows()),spot_observed='2026-10-20T12:00:00Z')
    assert rendered.count('data-pnl-token=')==3
    assert 'Resultado no realizado por token' in rendered
    assert 'integral-pnl-bar gain' in rendered and 'integral-pnl-bar loss' in rendered
    assert '>+40<' in rendered and '>-40<' in rendered
    assert 'Ganancia no realizada' in rendered and 'Pérdida no realizada' in rendered
    assert '02_POSICIONES' in rendered and 'Binance MCP' in rendered
    fallback=t.render(pnl_report=None,spot_observed=None)
    assert 'Datos MCP no disponibles' in fallback
    assert 'data-pnl-token=' not in fallback


def test_chart_missing_cost_displays_nd_not_total():
    rows=synthetic_rows();rows[0]['avg_cost']=None
    html=chart_section().render(pnl_report=summarize_unrealized(rows),spot_observed='OBSERVED')
    assert 'Costos incompletos: total no verificable' in html
    assert 'Sin costo/precio verificable: BTC' in html
    assert 'data-pnl-token="BTC"' in html


def test_portfolio_route_wired_to_live_dashboard_and_health():
    script=(ROOT/'app.py').read_text()
    assert "pnl_report = summarize_unrealized(live['rows'])" in script
    assert 'pnl_report=pnl_report' in script
    assert "'portfolio_unrealized_chart':" in script
    assert "'portfolio_unrealized_calc':" in script
