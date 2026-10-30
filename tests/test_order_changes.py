from unittest.mock import patch
import pytest
from orders_workflow import WorkflowError
import app
from orders_workflow import purchase_order_states, validate_transition

def test_states_include_canonical_and_journal_without_balancer_leak():
    book={'records':[{'lado':'BUY','token':'PUMP','tramo':'O2C2','estado':'CONFIRMADA'}, {'lado':'BUY','token':'SOL','tramo':'BALANCER','estado':'EJECUTADA'}], 'canonical_rows':[[],['Binance','id','LINK','BUY','LIMIT','O2C2',1,1,1,0,0,'FILLED']]}
    states=purchase_order_states(book)
    assert states['PUMP']['O2C2']=='CONFIRMADA'
    assert states['LINK']['O2C2']=='FILLED'
    assert 'O2C2' not in states['SOL']

def test_proposed_to_confirmed_and_executed_requires_evidence():
    p=validate_transition('PROPUESTA',dict(token='SOL',side='BUY',source='ESTRUCTURA',stage='O2C2',venue='Binance',planned_units=2,planned_usdt=20))
    p.update(kairos_order_id='test-order',revision=1)
    data=dict(exchange_order_id='12345',planned_units=2,planned_usdt=20,evidence='Comprobante',executed_units=2,executed_usdt=20,fee_units=.002,fee_quote=0)
    confirmed=validate_transition('CONFIRMADA',data,p)
    assert confirmed['conciliacion']=='PENDIENTE_FILL'
    assert validate_transition('EJECUTADA',data,p)['estado']=='EJECUTADA'
    assert validate_transition('EJECUTADA',data,confirmed)['conciliacion']=='PENDIENTE_CONCILIACION'

def test_endpoint_reaches_journal_without_balance_mutation():
    with app.app.test_request_context('/api/orders/manage',method='POST',json=dict(side='BUY',stage='O2C2',expected_snapshot_id='test',action='EJECUTADA',kairos_order_id='test-order')):
        with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.dict('os.environ',{'KAIROS_GOOGLE_WRITER_JSON':'test'}),patch('orders_workflow.write_event',return_value={'status':'OK','balances_updated':False}) as writer:
            response=app.manage_order_lifecycle()
            assert response.json['status']=='OK'
            writer.assert_called_once()

def test_templates_parse():
    for name in ('ordenes.html','trade_sim.html'):app.app.jinja_env.get_template(name)

@pytest.mark.parametrize('action',['PROPUESTA','CONFIRMAR_RECOMENDACION','EJECUTAR_RECOMENDACION'])
def test_web_rejects_proposal_creation_and_confirmation(action):
    with app.app.test_request_context('/api/orders/manage',method='POST',json=dict(side='BUY',stage='O2C2',action=action)):
        with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.dict('os.environ',{'KAIROS_GOOGLE_WRITER_JSON':'test'}),patch('orders_workflow.write_event') as writer:
            response,status=app.manage_order_lifecycle()
            assert status==409
            writer.assert_not_called()

def test_web_requires_authentication():
    with app.app.test_request_context('/api/orders/manage',method='POST',json={}):
        with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=False):
            assert app.manage_order_lifecycle()[1]==403

@pytest.mark.parametrize('old_status',['PROPUESTA','EJECUTADA'])
def test_persisted_state_is_checked_before_any_write(old_status):
    from orders_workflow import write_event, TAB, HEADERS, to_sheet_row
    rec=validate_transition('PROPUESTA',dict(token='SOL',side='BUY',source='ESTRUCTURA',stage='O2C2',venue='Binance',planned_units=2,planned_usdt=20))
    rec.update(kairos_order_id='test-order',event_id='event1',revision=1,estado=old_status)
    response={'valueRanges':[{'values':[list(HEADERS),to_sheet_row(rec)]}]}
    with patch('google_sheets_master.get_state',return_value={'control':{'snapshot_id':'test'}}),patch('kairos_sheets_features._sheet_ids',return_value={TAB:1}),patch('kairos_sheets_features._api',return_value=response) as api:
        with pytest.raises(WorkflowError,match='CONFIRMADA'):
            write_event(dict(kairos_order_id='test-order',action='EJECUTADA',_web_confirmed_only=True),expected_snapshot_id='test')
        assert all(call.args[0]=='GET' for call in api.call_args_list)

@pytest.mark.parametrize('action',['NO_APLICA','CONFIRMADA','PARCIAL','EJECUTADA'])
def test_web_new_states_pass_authenticated_endpoint(action):
    body=dict(side='BUY',stage='O2C2',action=action)
    with app.app.test_request_context('/api/orders/manage',method='POST',json=body):
        with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.dict('os.environ',{'KAIROS_GOOGLE_WRITER_JSON':'test'}),patch('orders_workflow.write_event',return_value={'status':'OK','balances_updated':False}) as writer:
            assert app.manage_order_lifecycle().json['status']=='OK'
            assert writer.call_args.args[0]['action']==action

@pytest.mark.parametrize('action',['NO_APLICA','CONFIRMADA','PARCIAL','EJECUTADA'])
def test_atomic_new_recommendation_transition(action):
    from orders_workflow import write_event,TAB,HEADERS,events_from_rows
    data=dict(_web_transition=True,action=action,token='SOL',side='BUY',stage='O2C2',source='ESTRUCTURA',venue='Binance',planned_units=2,planned_usdt=20,executed_units=1 if action=='PARCIAL' else 2,executed_usdt=10 if action=='PARCIAL' else 20,exchange_order_id='order123',evidence='Comprobante real')
    def api(method,*args,**kwargs):
        if method=='GET':return {'valueRanges':[{'values':[list(HEADERS)]}]}
        return {}
    state={'control':{'snapshot_id':'test'},'snapshot':{'liquidity_venues_USDT':{'Binance':100}}}
    with patch('google_sheets_master.get_state',return_value=state),patch('google_sheets_master.invalidate_cache'),patch('kairos_sheets_features._sheet_ids',return_value={TAB:1}),patch('kairos_sheets_features._api',side_effect=api) as mocked:
        result=write_event(data,expected_snapshot_id='test')
        assert result['order']['estado']==action
        assert result['balances_updated'] is False
        posts=[c for c in mocked.call_args_list if c.args[0]=='POST'];assert len(posts)==1
        rows=posts[0].kwargs['payload']['requests'][-1]['appendCells']['rows']
        assert len(rows)==2
        assert rows[0]['values'][10]['userEnteredValue']['stringValue']=='PROPUESTA'
        assert rows[1]['values'][10]['userEnteredValue']['stringValue']==action
        assert result['order']['revision']==2

def test_direct_execution_requires_real_evidence():
    p=validate_transition('PROPUESTA',dict(token='SOL',side='BUY',source='ESTRUCTURA',stage='O2C2',venue='Binance',planned_units=2,planned_usdt=20))
    p['kairos_order_id']='test'
    with pytest.raises(WorkflowError):validate_transition('EJECUTADA',dict(planned_units=2,planned_usdt=20,executed_units=2,executed_usdt=20,exchange_order_id='ord123'),p)

def test_orders_render_candidate_controls_and_one_indicator():
    item=dict(token='SOL',venue='Binance',side='BUY',stage='O2C2',limit=90,usdt=180,quantity=2,quote_currency='USDT',display_status='PROPUESTA')
    with app.app.test_request_context('/'):
        html=app.render_template('ordenes.html',master='3.0.24',snapshot='test',managed_orders={'records':[]},inbox={'candidates':[item]},tier_by_token={'SOL':'T1'},error=None)
    assert 'data-order=' in html
    assert 'value="NO_APLICA"' in html and 'value="PARCIAL"' in html
    assert 'span hidden class="order-traffic' not in html
    assert '🟡 PROPUESTA' in html

def test_pri_explanation_tracks_top_contributors():
    rows=[{'value':1,'target':1/12} for _ in range(12)]
    result=app.executive_risk_index(rows,100)
    assert result['label']=='Bajo' and 'bajo' in result['explanation']
    assert 'concentración' in result['explanation']
