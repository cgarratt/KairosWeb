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
    assert "APP_VERSION = '2.0.21'" in app
    assert "g.kairos_state['custody_policy']" in app
    assert "compare_custody(custody_positions" in app
    assert "'custody_comparison':custody_comparison" in app
    assert "'balancer_custody_engine':" in app
    assert "'balancer_custody_ui':" in app
    assert 'id="custody-balancer"' in html
    assert 'Movimientos propuestos' in html
    assert 'r.ideal_feasible[c]' in html and 'r.ideal_nominal[c]' in html
    from jinja2 import Environment
    Environment().parse(html)
