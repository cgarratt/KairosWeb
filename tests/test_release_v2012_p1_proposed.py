from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_identity_and_health_markers_in_release():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert "APP_VERSION = '2.0.14'" in app
    assert "'buy_p1p2_anchors':" in app and "'buy_p1p2_policy':" in app
    template=(ROOT/'templates/trade_sim.html').read_text(encoding='utf-8')
    engine=(ROOT/'buy_weekly_policy.py').read_text(encoding='utf-8')
    assert '<th>P1</th>' in template and '<th>P2</th>' in template
    assert 'pivot-anchor-dot' in template
    assert 'def select_p1_p2_buy_impulse(' in engine
    assert 'P1_ADMITIDO_P2_MAXIMO_SEMANAL_POSTERIOR' in engine

def test_pivot_anchor_status_semaphore_and_no_execution():
    template=(ROOT/'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'pivot-propuesto{background:#e54357}' in template
    assert 'pivot-validado{background:#f0a92b}' in template
    assert 'pivot-confirmado{background:#20bb73}' in template
    engine=(ROOT/'buy_weekly_policy.py').read_text(encoding='utf-8')
    assert "'simulation_only':True" in engine
    assert "'operational_blocked':True" in engine
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert "'/api/orders/place'" not in app and "'/api/orders/cancel'" not in app


def test_release_2014_matrix_ventas_forecast_and_orders_views():
    html=(ROOT/'templates/trade_sim.html').read_text(encoding='utf-8')
    forecast=(ROOT/'templates/forecast.html').read_text(encoding='utf-8')
    orders=(ROOT/'templates/ordenes.html').read_text(encoding='utf-8')
    assert 'Matriz de precios Fibo - Onda 2' in html
    assert '<th>P1</th><th>P2</th>' in html
    assert html.count('<th>% Peso</th>') == 4
    assert 'o2-drift-dot drift-' not in html  # los precios Fibo ya no llevan indicador
    assert 'correctP2=high.date&&historical.estimated_o1_date===high.date' in html
    assert "dollar(P*target/100)+' ('+target.toFixed(1)+'%)'" in html
    assert 'Simulación - Ondas Elliott' in forecast
    assert '<th>O5 (SH3)</th><th>Estado</th>' not in forecast
    assert 'rowspan="2"' not in forecast.split("$('waves-body').innerHTML=")[1].split(');',1)[0]
    for marker in ['Listado de próximas órdenes a ejecutar','Precios O2','Precios Binance',
                   'Precios T1','id="orders-group"','id="orders-tier"','data-orders-tier']:
        assert marker in orders
    assert 'FASE 1 · SOLO PROPUESTAS' in orders
    assert 'No colocada' in orders
