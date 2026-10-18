"""Release 2.0.9: read-only Orders page must ship with new build markers."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def test_release_version_and_orders_route():
    app=(R/'app.py').read_text()
    assert "APP_VERSION = '2.0.10'" in app
    assert "@app.route('/mode/ordenes')" in app
    assert "'orders_page':" in app and "'orders_engine':" in app and "'orders_filters':" in app
    assert "'/api/orders/place'" not in app and "'/api/orders/cancel'" not in app

def test_orders_readonly_and_two_strategies():
    page=(R/'templates/ordenes.html').read_text()
    engine=(R/'orders_inbox.py').read_text()
    assert "('ESTRUCTURA','Estructura de precio" in page
    assert "('BALANCE','Balance de portafolio" in page
    assert 'FASE 1 · SOLO PROPUESTAS' in page
    assert 'BTC NEVER SELL' in page
    assert "VENUES = {" in engine and "'HYPE':'Hyperliquid'" in engine
    assert 'actionable_alert' in engine and 'PROPUESTA_NO_COLOCADA' in engine
    assert "'/api/orders/place'" not in page
