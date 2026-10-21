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
    start=source.index('<section class="port-card" data-portfolio-chart="unrealized">')
    end=source.index('</section>',start)+len('</section>')
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
    assert "pnl_report = summarize_unrealized(portfolio_rows)" in script
    assert 'pnl_report=pnl_report' in script
    assert "'portfolio_unrealized_chart':" in script
    assert "'portfolio_unrealized_calc':" in script


from portfolio_unrealized import portfolio_allocation, category_allocation, pri_valuation_history


def test_allocation_13_components_cash_once_sorted():
    tokens='BTC ETH SOL LINK HYPE HBAR SUI ONDO PUMP PLUME VIRTUAL PEPE'.split()
    rows=[{'token':token,'value':(i+1)*10,'tier':('T1' if i<5 else 'T2' if i<10 else 'T3'),
           'target':(.1 if i<5 else .05 if i<10 else .125)} for i,token in enumerate(tokens)]
    out=portfolio_allocation(rows,100)
    assert len(out['items'])==13
    assert {x['token'] for x in out['items']}==set(tokens)|{'USDT'}
    assert sum(x['value'] for x in out['items'])==out['total']
    assert sum(x['pct'] for x in out['items'])==100
    assert out['items']==sorted(out['items'],key=lambda x:(-x['value'],x['token']))
    assert len({x['color'] for x in out['items']})==13
    categories=category_allocation(rows)
    assert len(categories)==3
    assert abs(sum(c['actual'] for c in categories)-100)<1e-9


def test_pri_only_validated_flow_unadjusted_history():
    heading=['Spot UTC','Estado','Patrimonio USD','USDT físico','Valor cripto USD']
    data=[heading,
          ['2026-10-18T15:00:00Z','DATA_ERROR_PARCIAL',1000,250,750],
          ['2026-10-19T15:00:00Z','OK',1000,250,750],
          ['2026-10-19T17:00:00Z','OK',1100,275,825],
          ['2026-10-20T17:00:00Z','OK',1120,300,820],
          ['2026-10-21T15:00:00Z','OK',1400,250,700]]
    result=pri_valuation_history(data)
    assert [p['day'] for p in result]==['2026-10-19','2026-10-20']
    assert result[0]['total']==1100
    assert not pri_valuation_history([heading,['2026-10-21T12:00:00Z','DATA_ERROR_PARCIAL',800,200,600]])


def test_portfolio_approved_four_row_layout():
    html=(ROOT/'templates/portfolio_integral.html').read_text()
    rows=[html.index('data-layout-row="'+str(i)+'"') for i in range(1,5)]
    assert rows==sorted(rows)
    first=html[rows[0]:rows[1]]
    assert first.index('data-capital-chart="donut"')<first.index('data-allocation-chart="13"')
    second=html[rows[1]:rows[2]]
    assert second.index('data-history-chart="returns"')<second.index('data-portfolio-chart="unrealized"')
    third=html[rows[2]:rows[3]]
    assert third.index('data-category-chart="tier"')<third.index('data-composition-chart="tokens"')
    assert 'data-tracking-chart="portfolio"' in html[rows[3]:]
    assert 'history_points|tojson' in html
    assert 'Historial insuficiente' in html


def test_template_full_render_with_certified_sample_and_missing_values():
    from types import SimpleNamespace
    tokens='BTC ETH SOL LINK HYPE HBAR SUI ONDO PUMP PLUME VIRTUAL PEPE'.split()
    rows=[{'token':t,'units':1.0,'price':i+1.0,'avg_cost':i+.5,
           'value':i+1.0,'weight':(i+1)/78,'target':.05,'tier':('T1' if i<5 else 'T2' if i<10 else 'T3')} for i,t in enumerate(tokens)]
    ctx={'g':SimpleNamespace(kairos_state={'control':{'fecha_corte':'2026-10-19'}}),
         'base':150000.0,'segments':[{'key':'hodl_core','actual_usdt':100000.0,'target_usdt':100000.0,'name':'HODL + Core'},
                                    {'key':'lost','actual_usdt':50000.0,'target_usdt':50000.0,'name':'Lost'}],
         'spot':{'total':sum(r['value'] for r in rows)+200,'liquidity':100,'trading':100},
         'spot_observed':'2026-10-21T11:00:00Z','pnl_report':summarize_unrealized(rows),
         'allocation':portfolio_allocation(rows,200),'categories':category_allocation(rows),
         'portfolio_rows':rows,'o2c2_reference':100,'history_points':[],
         'history_note':'Sin historia', 'source_note':'Master publicado'}
    env=Environment(loader=FileSystemLoader(ROOT/'templates'))
    template=(ROOT/'templates/portfolio_integral.html').read_text()
    region=template[template.index('<div class="port-page">'):template.index('{% endblock %}',template.index('<div class="port-page">'))]
    markup=env.from_string(region).render(**ctx)
    assert 'data-allocation-token="USDT"' in markup
    assert markup.count('data-allocation-token=')==13
    assert markup.count('data-pnl-token=')==12
    assert 'Seguimiento del portafolio' in markup
    assert 'N/D' in markup
