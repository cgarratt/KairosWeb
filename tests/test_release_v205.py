"""Accumulative release 2.0.5 source contract checks (without live credentials)."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(name):return (ROOT/name).read_text(encoding='utf-8')

def test_release_version_and_runtime_asset_diagnostics():
    app=read('app.py')
    assert "APP_VERSION = '2.0.5'" in app
    assert 'def _deployed_asset_status()' in app
    assert "'release_assets': assets" in app
    assert "'DEGRADED'" in app
    assert "'sha256_12'" in app

def test_trade_sim_all_accumulated_changes():
    page=read('templates/trade_sim.html')
    assert '<h2>Asignación USDT para referencias Fibonacci O2</h2>' in page
    assert page.index('Liquidez post-escenario')<page.index('id="o2-fibonacci-panel"')
    assert 'data-o2-ui-version="{{ master }}"' in page
    assert 'value="{{ payload.current.max_percent if mode.slug==' in page
    assert 'const historical=source.o2_histories?' in page
    assert 'const css=historicalStatus===' in page
    assert 'o2-drift-dot drift-${status.toLowerCase()}' in page
    assert 'class="${css}" title="${historicalTitle}"' in page
    assert 'level-blocked' not in page[page.index('function renderO2Fibonacci(sim)'):page.index('function paint()')]
    assert "filename='o2_sequential.js'" in page

def test_1h_4h_1d_bell_and_ledger_preserve_safety():
    core=read('kairos_sheets_features.py')
    ui=read('static/alert_bell.js')
    assert "ALERT_TIMEFRAMES = frozenset(('1H', '4H', '1D'))" in core
    for alert in ('NIVEL_PROXIMO','FILL_','BREAK_BAJISTA','NUEVA_ESTRUCTURA','NUEVA_ONDA','BSI_ACCION','LIQUIDEZ_CRITICA'):
        assert alert in core
    assert 'def mark_alert_read(' in core and 'def mark_all_alerts_read(' in core
    assert 'READ_LOCK' not in core or 'WRITE_LOCK' in core
    assert 'alert-timeframe' in ui and "'/api/alerts/read'" in ui
    assert 'INFORMATIVA' in ui and 'No constituye orden ni fill verificado' in ui
