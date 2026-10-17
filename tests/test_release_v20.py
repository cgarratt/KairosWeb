from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_v20_version_and_purchase_table_location():
    app=(R/'app.py').read_text();buy=(R/'templates/trade_sim.html').read_text();forecast=(R/'templates/forecast.html').read_text()
    assert 'APP_VERSION = "2.0.0"' in app
    assert '<h2>Asignación USDT para referencias Fibonacci O2</h2>' in buy
    assert '<h2>Asignación USDT para referencias Fibonacci O2</h2>' not in forecast
    assert buy.index('Liquidez post-escenario')<buy.index('id="o2-fibonacci-panel"')
    assert '<th>Token</th><th>Spot</th>' in buy
    assert 'renderO2Fibonacci(allocated)' in buy
    assert 'const forbidden=budget<=.000001' in buy
    assert 'const css=forbidden?' in buy
    assert '<td class="${css}">${fibPrice(level)}</td><td class="${css}">${dollar(amount)}</td>' in buy
    assert 'class="sim-warn" id="caution"' not in buy
    assert '<strong>Alcance de la simulación</strong>' not in buy
    assert 'max_percent=(100*max(0.0,cash-trading)/p)' in app
