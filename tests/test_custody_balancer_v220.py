from custody_balancer import compare_custody, CustodyError

def test_custody_balancer_publicado_math_parity():
    policy={'T1':{'hodl':.4,'core':.3,'exchange':.3},
            'T2':{'hodl':0,'core':.3,'exchange':.7},
            'T3':{'hodl':0,'core':0,'exchange':1}}
    r=compare_custody({'SOL':{'tier':'T1','hodl':15,'core':15,'exchange':29.94},
                       'PUMPFUN':{'tier':'T2','hodl':0,'core':125000,'exchange':455124}},policy)
    assert r['status']=='SIMULACION_NO_EJECUTADA'
    assert [(m['token'],m['destination'],m['units']) for m in r['transfers']]==[
        ('SOL','HODL','8.976'),('SOL','Core','2.982'),('PUMPFUN','Core','49037.2')]

def test_release_ui_has_live_sheet_adapter_and_health_markers():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text()
    html=(root/'templates/balancer.html').read_text()
    assert "APP_VERSION = '2.0.43'" in app
    assert "g.kairos_state['custody_policy']" in app
    assert "compare_custody(custody_positions" in app
    assert "'custody_comparison':custody_comparison" in app
    assert "'balancer_custody_engine':" in app
    assert "'balancer_custody_ui':" in app
    assert 'id="custody-balancer"' in html
    assert 'Movimientos y distribución posterior' in html
    assert 'r.feasible_pct.hodl' in html and 'cust.transfers if m.token == r.token' in html
    from jinja2 import Environment
    Environment().parse(html)


def test_published_master_custody_list_shape_renders_without_mode_render():
    # Real parse_master emits list/tuple ratios; using dicts only was an incomplete test.
    from google_sheets_master import parse_master
    from test_google_sheets_master import fake_master
    state = parse_master(fake_master())
    assert state['custody_policy']['T1'] == [0.4, 0.3, 0.3]
    rows={
        'SOL': {'tier':'T1', 'units':59.94, 'hodl':15, 'core':15, 'exchange':29.94},
        'PUMPFUN': {'tier':'T2', 'units':580124, 'hodl':0, 'core':125000, 'exchange':455124},
    }
    report = compare_custody(rows, state['custody_policy'])
    assert report['transfer_count'] == 3
    assert report['transfers'][0]['units'] == '8.976'
    assert report['status'] == 'SIMULACION_NO_EJECUTADA'


def test_policy_list_wrong_shape_fails_closed():
    import pytest
    with pytest.raises(CustodyError):
        compare_custody({'SOL': {'tier':'T1','units':1,'hodl':0,'core':0,'exchange':1}},
                        {'T1':[0.4,0.3]})

# v2.0.26: exact financial-contract regression shared by Balancer and Orders.
def _policy_rows():
    tokens=['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PLUME','VIRTUAL','PEPE']
    units=[.12681,3.62437,59.94,398.9885,182.5,52812,3139.4,6775.75,580124,100887,2252.54,376765766]
    exchange=[.02681,.62437,29.94,98.9885,32.5,33747,1807.4,3559.95,455124,86420,2252.54,222423248]
    prices=[82808.12,2449.24,106.28,12.351,81.64,.08347,1.0273,.4525,.004774,.01823,.6794,.00000449]
    targets=[.2,.15,.15,.1,.1,.05,.05,.05,.05,.05,.025,.025]
    rows=[{'token':x,'units':units[i], 'exchange_units':exchange[i], 'price':prices[i],
           'tier':('T1' if i<5 else 'T2' if i<10 else 'T3'), 'target':targets[i],
           'value':units[i]*prices[i]} for i,x in enumerate(tokens)]
    crypto=sum(r['value'] for r in rows)
    for r in rows:
        r['weight']=r['value']/crypto
        r['drift_pp']=100*(r['weight']-r['target'])
    return rows


def test_v2026_buy_does_not_overshoot_or_spend_unneeded_usdt():
    from orders_inbox import allocate_infra_buys
    rows=_policy_rows()
    crypto=sum(r['value'] for r in rows)
    for budget in (0,1,100,1000,5000,100000,1000000):
        buys=allocate_infra_buys(rows,budget,.5)
        spent=sum(x['value'] for x in buys)
        assert spent <= budget+1e-6
        assert all(x['drift']<-.5 and x['value']>=0 for x in buys)
        total_after=crypto+spent
        by_token={x['token']:x['value'] for x in buys}
        for row in rows:
            assert (row['value']+by_token.get(row['token'],0.))/total_after <= row['target']+1e-8 or row['token'] not in by_token
    assert sum(x['value'] for x in allocate_infra_buys(rows,1e6,.5))<1e6


def test_v2026_sell_tier_and_reserved_units_apply_to_balancer():
    from orders_inbox import sell_capacity_usdt,overweight_sell_plan
    rows=_policy_rows()
    hype=next(r for r in rows if r['token']=='HYPE')
    assert abs(sell_capacity_usdt(hype)-32.5*hype['price'])<1e-6
    hype['reserved_sell_units']=20
    assert abs(sell_capacity_usdt(hype)-12.5*hype['price'])<1e-6
    plan=overweight_sell_plan(rows,.5)
    assert all(x['value']<=x['cap_usdt']+1e-6 for x in plan)
    assert sum(x['value'] for x in plan if x['token']=='BTC')==0
    assert next(x for x in plan if x['token']=='HYPE')['units']<=12.5+1e-8


def test_v2026_missing_or_inconsistent_exchange_inventory_blocks_sells():
    import pytest
    from orders_inbox import sell_capacity_usdt
    rows=_policy_rows()
    bad=dict(rows[2],tier='T9')
    with pytest.raises(ValueError,match='Tier'):sell_capacity_usdt(bad)
    bad=dict(rows[2],exchange_units=1000)
    with pytest.raises(ValueError,match='custodias'):sell_capacity_usdt(bad)
    bad=dict(rows[2],reserved_sell_units=1000)
    with pytest.raises(ValueError,match='custodias'):sell_capacity_usdt(bad)
    assert sell_capacity_usdt(rows[0])==0


def test_v2026_drift_semantics_and_tradingbot_universe_from_master():
    import pytest
    from orders_inbox import drift_tone,tradingbot_tokens
    assert drift_tone(.5,.5)=='ok'
    assert drift_tone(-.5,.5)=='ok'
    assert drift_tone(.50001,.5)=='danger'
    assert drift_tone(-.50001,.5)=='warn'
    tiers={t:'T1' for t in ('BTC','ETH','SOL','LINK','HYPE')}
    tiers['HBAR']='T2'
    assert tradingbot_tokens('T1_ONLY:BTC,ETH,SOL,LINK,HYPE',tiers)==('BTC','ETH','SOL','LINK','HYPE')
    with pytest.raises(ValueError):tradingbot_tokens('T1_ONLY:BTC,ETH,SOL,LINK,HBAR',tiers)
    with pytest.raises(ValueError):tradingbot_tokens('T1_ONLY:BTC,ETH,SOL,LINK',tiers)


def test_v2026_javascript_stage1_parity_with_python():
    import json,shutil,subprocess
    import pytest
    from pathlib import Path
    from orders_inbox import overweight_sell_plan
    if shutil.which('node') is None:pytest.skip('Node not available')
    rows=_policy_rows()
    py={x['token']:x['value'] for x in overweight_sell_plan(rows,.5)}
    root=Path(__file__).resolve().parents[1]
    script="const fs=require('fs'),vm=require('vm');let g={};vm.runInNewContext(fs.readFileSync('static/sales_optimizer.js','utf8'),g);let inp=JSON.parse(fs.readFileSync(0,'utf8'));let v=g.KairosSalesOptimizer.calculate(inp,22545,40,.5,7225);console.log(JSON.stringify(v.positions.map(x=>[x.token,x.stage1_usdt])))"
    payload=json.dumps([{k:r[k] for k in ('token','units','exchange_units','price','tier','target')} for r in rows])
    output=subprocess.run(['node','-e',script],input=payload,text=True,cwd=root,capture_output=True,check=True)
    js=dict(json.loads(output.stdout))
    for t in js:
        assert abs(js[t]-py.get(t,0.))<0.02,(t,js[t],py.get(t,0))


def test_v2026_balancer_and_orders_same_sell_limits():
    from orders_inbox import overweight_sell_plan, portfolio_candidates
    rows=_policy_rows()
    plan=overweight_sell_plan(rows,.5)
    d={'rows':rows}
    inbox=portfolio_candidates(d,{'buys':[],'sells':plan},.5)
    by_token={x['token']:x['usdt'] for x in inbox}
    for item in plan:
        if item['value']>=.005:
            assert abs(item['value']-by_token[item['token']])<1e-6


# v2.0.28 custody compact option B regression (same test module, GitHub 99-file limit)
from pathlib import Path
from jinja2 import Environment
ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT/'templates/balancer.html').read_text(encoding='utf-8')
START = TEMPLATE.index('{% if payload.custody_comparison is defined and payload.custody_comparison %}')
END = TEMPLATE.index('{% endif %}', TEMPLATE.index('</section>', START)) + len('{% endif %}')
SECTION = TEMPLATE[START:END]
POLICY = {'T1': [0.4, 0.3, 0.3], 'T2': [0, 0.3, 0.7], 'T3': [0, 0, 1]}


def _option_b_report():
    return compare_custody({
        'BTC':{'tier':'T1','hodl':.1,'core':0,'exchange':.02681},
        'SOL':{'tier':'T1','hodl':15,'core':15,'exchange':29.94},
        'PUMPFUN':{'tier':'T2','hodl':0,'core':125000,'exchange':455124},
        'PLUME':{'tier':'T2','hodl':0,'core':14467,'exchange':86420},
        'VIRTUAL':{'tier':'T3','hodl':0,'core':0,'exchange':2252.54},
    }, POLICY)


def _option_b_render(report):
    return Environment(autoescape=True).from_string(SECTION).render(payload={'custody_comparison': report})


def test_b_model_groups_four_moves_in_three_tokens_and_keeps_units():
    report = _option_b_report()
    assert report['transfer_count'] == 4
    assert report['tokens_with_moves'] == 3
    html = _option_b_render(report)
    assert html.count('class="custody-row" data-custody-token=') == 3
    assert html.count('class="custody-transfer"') == 4
    assert html.count('data-custody-token="SOL"') == 1
    assert '8.976' in html and '2.982' in html
    assert '49037.2' in html and '15799.1' in html
    assert 'H 40.00%' in html and 'C 30.00%' in html and 'E 30.00%' in html
    assert 'H 0.00%' in html and 'C 30.00%' in html and 'E 70.00%' in html
    assert 'Mostrar 2 tokens sin movimientos sugeridos' in html
    assert 'Ideal nominal (uds.)' not in html
    assert 'Distribución exacta por token · tres custodias' not in html
    assert 'SIN TRANSFERENCIAS' in html


def test_b_model_when_no_safe_transfers():
    report = compare_custody({'BTC':{'tier':'T1','hodl':.1,'core':0,'exchange':.02681}}, POLICY)
    assert report['transfer_count'] == 0
    html = _option_b_render(report)
    assert 'No hay transferencias seguras' in html
    assert 'Mostrar 1 tokens sin movimientos sugeridos' in html
    assert 'H 78.86%' in html or 'Sin movimiento permitido' in html


def test_b_model_does_not_change_engine_or_execute_anything():
    source = (ROOT/'custody_balancer.py').read_text(encoding='utf-8')
    assert 'suggested[\'exchange\']-=move' in source
    assert 'reserved_exchange' in source
    assert 'Sin movimientos ejecutados' not in SECTION or 'SIN TRANSFERENCIAS' in SECTION
    assert 'fetch(' not in SECTION and 'POST' not in SECTION


def test_b_model_is_responsive_and_accessible():
    assert 'role="img"' in TEMPLATE
    assert 'aria-label="{{' in TEMPLATE
    assert '@media(max-width:550px)' in TEMPLATE
    assert 'custody-plot' in TEMPLATE
    assert 'custody-more' in TEMPLATE

# v2.0.32: the Balancer sell candidates table displays the already capped SELL
# units; it does not recompute from a second price source or fabricate fills.
def test_v2032_balancer_sell_units_column_renders_model_quantities():
    from pathlib import Path
    from types import SimpleNamespace
    from jinja2 import Environment
    root=Path(__file__).resolve().parents[1]
    html=(root/'templates/balancer.html').read_text()
    start=html.index('<section class="panel span-6"><h2>4. Candidatos de venta')
    end=html.index('</section>',start)+len('</section>')
    snippet=html[start:end]
    payload=SimpleNamespace(sells=[
        {'token':'HYPE','value':2653.30,'weight':.23,'target':.10,'units':32.5},
        {'token':'HBAR','value':1405.90,'weight':.069,'target':.05,'units':16843.17120163},
    ])
    markup=Environment().from_string(snippet).render(payload=payload)
    assert '<th>Unidades</th>' in markup
    assert '32.5' in markup and '16,843.17' in markup
    assert markup.count('data-private="units"')==2
    assert 'TOTAL VENTAS USDT' in markup and 'SIMULACIÓN' in markup
    assert '2,653.30' not in markup  # USD reference remains rounded visually.
    assert '4,059' in markup


def test_v2032_balancer_units_show_dash_when_zero_and_never_sum_tokens():
    from pathlib import Path
    from types import SimpleNamespace
    from jinja2 import Environment
    root=Path(__file__).resolve().parents[1]
    html=(root/'templates/balancer.html').read_text()
    start=html.index('<section class="panel span-6"><h2>4. Candidatos de venta')
    end=html.index('</section>',start)+len('</section>')
    payload=SimpleNamespace(sells=[{'token':'HYPE','value':0,'weight':.23,'target':.1,'units':0}])
    markup=Environment().from_string(html[start:end]).render(payload=payload)
    assert '>—</td>' in markup
    assert '<th>Unidades</th>' in markup
    assert '<td>—</td><td>SIMULACIÓN</td>' in markup
