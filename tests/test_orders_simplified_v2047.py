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
    assert 'data-manage="PARCIAL"' in s

def test_confirmation_atomic_contract():
    s=(ROOT/'orders_workflow.py').read_text()
    assert "if action=='CONFIRMAR_RECOMENDACION':" in s
    assert 'initial_event' in s
    assert 'revision=(2 if initial_event' in s
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
