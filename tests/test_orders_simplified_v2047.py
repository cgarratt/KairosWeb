from pathlib import Path
from orders_workflow import validate_transition, WorkflowError
ROOT=Path(__file__).resolve().parents[1]

def test_single_table_and_filters():
    s=(ROOT/'templates/ordenes.html').read_text()
    assert s.count('id="orders-list"')==1
    assert 'Backlog de Ordenes Compra / Venta' not in s
    assert 'Próximas órdenes por Token' not in s
    assert 'orders-status' in s
    assert 'data-manage="CONFIRMAR_RECOMENDACION"' in s
    assert 'data-manage="PARCIAL"' not in s

def test_confirmation_atomic_contract():
    s=(ROOT/'orders_workflow.py').read_text()
    assert "if action in ('CONFIRMAR_RECOMENDACION','EJECUTAR_RECOMENDACION'):" in s
    assert 'initial_event' in s
    assert 'revision=(3 if confirmed_event else 2 if initial_event' in s
    assert "'rows':[{'values':[_sval(x) for x in to_sheet_row(x)]}" in s

def test_security_guards_unchanged():
    s=(ROOT/'app.py').read_text()
    assert 'if not _admin_authorized() or not _csrf_ok()' in s
    assert "@app.route('/api/orders/manage',methods=['POST'])" in s
    assert 'No se pudo certificar la escritura' in s
    assert 'send_order' not in (ROOT/'templates/ordenes.html').read_text()

def test_btc_sell_rejected():
    try:
        validate_transition('PROPUESTA',dict(token='BTC',side='SELL',source='BALANCE',stage='O3V1',venue='Binance',planned_units=1,planned_usdt=50000))
    except WorkflowError as exc: assert exc.code=='POLICY_BLOCK'
    else: raise AssertionError('BTC SELL must be blocked')
from pathlib import Path
import pytest
from order_image_extract import extract_image, ImageExtractError
ROOT=Path(__file__).resolve().parents[1]

def test_image_rejects_wrong_magic_and_oversize():
    with pytest.raises(ImageExtractError):extract_image(b'not a png','image/png')
    with pytest.raises(ImageExtractError):extract_image(b'\x89PNG\r\n\x1a\n'+b'0'*(5*1024*1024),'image/png')

def test_without_key_manual_fallback(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(ImageExtractError,match='no configurada'):
        extract_image(b'\x89PNG\r\n\x1a\n123','image/png')

def test_only_two_actions_for_unregistered_recommendations():
    template=(ROOT/'templates/ordenes.html').read_text()
    assert 'data-manage="PROPUESTA"' not in template
    assert 'data-manage="CONFIRMAR_RECOMENDACION"' in template
    assert 'data-manage="EJECUTAR_RECOMENDACION"' in template
    assert 'type="file"' in template

def test_extraction_admin_guard_and_no_automatic_fill():
    app=(ROOT/'app.py').read_text()
    assert "@app.route('/api/orders/extract-image', methods=['POST'])" in app
    assert 'if not _admin_authorized() or not _csrf_ok()' in app
    assert 'write_event(' not in app.split("@app.route('/api/orders/extract-image'",1)[1].split("@app.route('/api/orders/manage'",1)[0]

def test_direct_execution_three_events_atomic():
    source=(ROOT/'orders_workflow.py').read_text()
    assert "action=='EJECUTAR_RECOMENDACION'" in source
    assert "revision=(3 if confirmed_event else 2 if initial_event" in source
    assert "([confirmed_event] if confirmed_event else [])" in source
