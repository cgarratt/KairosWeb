"""Release 2.0.9: read-only Orders page must ship with new build markers."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def test_release_version_and_orders_route():
    app=(R/'app.py').read_text()
    assert "APP_VERSION = '2.0.16'" in app
    assert "@app.route('/mode/ordenes')" in app
    assert "'orders_page':" in app and "'orders_engine':" in app and "'orders_filters':" in app
    assert "'/api/orders/place'" not in app and "'/api/orders/cancel'" not in app

def test_orders_readonly_and_two_strategies():
    page=(R/'templates/ordenes.html').read_text()
    engine=(R/'orders_inbox.py').read_text()
    assert "item.category=='ESTRUCTURA'" in page
    assert "item.category=='ESTRUCTURA' else 'BALANCE'" in page
    assert 'FASE 1 · SOLO PROPUESTAS' in page
    assert 'BTC NEVER SELL' in page
    assert "VENUES = {" in engine and "'HYPE':'Hyperliquid'" in engine
    assert 'actionable_alert' in engine and 'PROPUESTA_NO_COLOCADA' in engine
    assert "'/api/orders/place'" not in page


def test_nearest_technical_table_title_and_column_order():
    import re
    page = (R/'templates/ordenes.html').read_text()
    assert '<h3>Próximas órdenes por Token</h3>' in page
    top = page.split('id="orders-nearest"', 1)[1].split('</table>', 1)[0]
    headers = re.findall(r'<th>(.*?)</th>', top)
    assert headers == ['Token', 'Exchange', 'Origen', 'Nivel', 'Spot', 'Dirección',
                       'Objetivo cercano', 'Distancia', 'USDT compra', 'Unidades venta', 'Estado']
    # Each row must have the same data order as its heading.
    cells = re.findall(r'<td(?:\s[^>]*)?>(.*?)</td>', top, flags=re.S)
    assert len(cells) == len(headers)
    assert "{{ c.origin }}" in cells[2]
    assert "{{ c.stage or 'N/D' }}" in cells[3]
    assert 'c.spot' in cells[4]
    assert 'c.side' in cells[5]
    assert 'c.limit' in cells[6]
    assert 'c.distance_pct' in cells[7]
    assert 'c.buy_usdt' in cells[8]
    assert 'c.sell_units' in cells[9]
    assert 'c.status' in cells[10]


def test_generic_levels_explain_ratio_without_mislabeling_elliott():
    page=(R/'templates/ordenes.html').read_text()
    assert "'C2':'50%'" in page and "'C4':'78.6%'" in page
    assert "'EXT1W1':'1.618'" in page
    assert '· retroceso alcista' in page and '· extensión 1W' in page


def test_orders_level_filter_and_factual_size_columns():
    page=(R/'templates/ordenes.html').read_text()
    js=(R/'static/orders_inbox.js').read_text()
    assert '<select id="orders-level"' in page
    assert 'data-stage="{{ item.stage }}"' in page
    assert 'orders-level' in js and 'row.dataset.stage===level' in js
    assert '<th>USDT compra</th><th>Unidades venta</th>' in page
    assert "c.buy_usdt" in page and "c.sell_units" in page
    assert 'POR DEFINIR' in page  # No fabricated structural SELL size
