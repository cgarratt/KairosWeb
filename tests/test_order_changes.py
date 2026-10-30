from unittest.mock import patch
import pytest
import app
from orders_workflow import validate_transition,WorkflowError,HEADERS,TAB,to_sheet_row,write_event

def proposal(state='PROPUESTA'):
 p=validate_transition('PROPUESTA',dict(token='SOL',side='BUY',source='ESTRUCTURA',stage='O2C2',venue='Binance',planned_units=2,planned_usdt=20))
 p.update(kairos_order_id='test-order',revision=1,event_id='event1',estado=state)
 if state in ('CONFIRMADA','EJECUTADA','PARCIAL'):p['exchange_order_id']='ord123'
 return p

def evidence():return dict(exchange_order_id='ord123',planned_units=2,planned_usdt=20,evidence='Captura verificada',executed_units=2,executed_usdt=20,fee_units=.002,fee_quote=0)

@pytest.mark.parametrize('old',['NO_APLICA','PROPUESTA','CONFIRMADA','EJECUTADA','PARCIAL'])
@pytest.mark.parametrize('new',['NO_APLICA','PROPUESTA','CONFIRMADA','EJECUTADA','PARCIAL'])
@pytest.mark.parametrize('channel',['WEB','GPT'])
def test_complete_normal_transition_matrix(old,new,channel):
 allowed=(old=='NO_APLICA' and new=='PROPUESTA') or (old=='PROPUESTA' and new=='CONFIRMADA' and channel=='GPT') or (old=='CONFIRMADA' and new=='EJECUTADA' and channel=='WEB') or (old==new=='PROPUESTA' and channel=='WEB')
 if allowed:assert validate_transition(new,evidence(),proposal(old),channel=channel,image_verified=True)['estado']==new
 else:
  with pytest.raises(WorkflowError):validate_transition(new,evidence(),proposal(old),channel=channel,image_verified=True)

def test_gpt_confirmation_requires_verified_image():
 for verified in (False,None,'true'):
  with pytest.raises(WorkflowError):validate_transition('CONFIRMADA',evidence(),proposal(),image_verified=verified)
 with pytest.raises(WorkflowError):validate_transition('CONFIRMADA',{**evidence(),'evidence':''},proposal(),image_verified=True)

@pytest.mark.parametrize('new',['NO_APLICA','PROPUESTA','CONFIRMADA','PARCIAL','EJECUTADA'])
def test_explicit_gpt_prompt_changes_state_without_altering_finances(new):
 old=proposal('EJECUTADA');old.update(unidades_ejecutadas=2,importe_ejecutado=20,comision_token=.002,conciliacion='CONCILIADA_EN_05',evidencia='Original')
 r=validate_transition(new,{},old,channel='GPT',prompt_override=True,prompt_instruction='Corregir el estado explícitamente')
 assert r['estado']==new and 'PROMPT EXPLÍCITO' in r['observaciones']
 for k in ('unidades_ejecutadas','importe_ejecutado','comision_token','conciliacion','evidencia','exchange_order_id'):assert r[k]==old[k]
 with pytest.raises(WorkflowError):validate_transition(new,{},old,channel='WEB',prompt_override=True,prompt_instruction='ignorar')
 with pytest.raises(WorkflowError):validate_transition(new,{},old,channel='GPT',prompt_override=True)

def test_web_execution_edits_data_and_rejects_ledger_duplicate():
 r=validate_transition('EJECUTADA',{**evidence(),'planned_units':3,'executed_units':3,'planned_usdt':30,'executed_usdt':30,'exchange_order_id':'ord456'},proposal('CONFIRMADA'),channel='WEB')
 assert r['unidades_previstas']==3 and r['importe_ejecutado']==30 and r['exchange_order_id']=='ord456'
 with pytest.raises(WorkflowError):validate_transition('EJECUTADA',evidence(),proposal('CONFIRMADA'),existing_exchange=[('Binance','ord123')],channel='WEB')

@pytest.mark.parametrize('old,new',[('NO_APLICA','PROPUESTA'),('CONFIRMADA','EJECUTADA')])
def test_persisted_revision_atomic_write(old,new):
 rec=proposal(old)
 state={'control':{'snapshot_id':'test'},'snapshot':{'liquidity_venues_USDT':{'Binance':100}}}
 def api(method,*args,**kwargs):
  if method=='GET':return {'valueRanges':[{'values':[list(HEADERS),to_sheet_row(rec)]}]} if '26_' in str(kwargs) else {'valueRanges':[{'values':[[]]}]}
  return {}
 with patch('google_sheets_master.get_state',return_value=state),patch('google_sheets_master.invalidate_cache'),patch('kairos_sheets_features._sheet_ids',return_value={TAB:1}),patch('kairos_sheets_features._api',side_effect=api) as mock:
  r=write_event({**evidence(),'action':new,'kairos_order_id':'test-order','expected_revision':1},expected_snapshot_id='test')
  assert r['order']['revision']==2 and r['order']['estado']==new and not r['balances_updated']
  assert len([c for c in mock.call_args_list if c.args[0]=='POST'])==1

@pytest.mark.parametrize('old,new',[('PROPUESTA','CONFIRMADA'),('PROPUESTA','EJECUTADA'),('EJECUTADA','PROPUESTA'),('PARCIAL','EJECUTADA')])
def test_invalid_persisted_change_cannot_write(old,new):
 rec=proposal(old)
 with patch('google_sheets_master.get_state',return_value={'control':{'snapshot_id':'test'}}),patch('kairos_sheets_features._sheet_ids',return_value={TAB:1}),patch('kairos_sheets_features._api',return_value={'valueRanges':[{'values':[list(HEADERS),to_sheet_row(rec)]}]}) as api:
  with pytest.raises(WorkflowError):write_event({**evidence(),'kairos_order_id':'test-order','action':new,'expected_revision':1,'prompt_override':True,'channel':'GPT','image_verified':True},expected_snapshot_id='test')
  assert all(c.args[0]=='GET' for c in api.call_args_list)

@pytest.mark.parametrize('action',['CONFIRMADA','PARCIAL','NO_APLICA','EJECUTAR_RECOMENDACION'])
def test_endpoint_rejects_non_web_actions(action):
 with app.app.test_request_context('/api/orders/manage',method='POST',json=dict(side='BUY',stage='O2C2',action=action)):
  with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.dict('os.environ',{'KAIROS_GOOGLE_WRITER_JSON':'test'}),patch('orders_workflow.write_event') as writer:
   assert app.manage_order_lifecycle()[1]==409;writer.assert_not_called()

def test_endpoint_never_accepts_prompt_override():
 with app.app.test_request_context('/api/orders/manage',method='POST',json=dict(side='BUY',stage='O2C2',action='EJECUTADA',prompt_override=True,prompt_instruction='spoof',image_verified=True,channel='GPT')):
  with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.dict('os.environ',{'KAIROS_GOOGLE_WRITER_JSON':'test'}),patch('orders_workflow.write_event',return_value={'status':'OK'}) as writer:
   assert app.manage_order_lifecycle().json['status']=='OK'
   assert 'prompt_override' not in writer.call_args.args[0] and 'channel' not in writer.call_args.args[0]

def test_web_requires_authentication():
 with app.app.test_request_context('/api/orders/manage',method='POST',json={}):
  with patch.object(app,'_same_origin',return_value=True),patch.object(app,'_admin_authorized',return_value=False):assert app.manage_order_lifecycle()[1]==403

def test_render_only_no_aplica_or_confirmed_have_controls():
 for state,button in [('PROPUESTA',False),('NO_APLICA',True),('EJECUTADA',False)]:
  item=dict(token='SOL',venue='Binance',side='BUY',stage='O2C2',limit=90,usdt=180,quantity=2,quote_currency='USDT',display_status=state)
  with app.app.test_request_context('/'):
   html=app.render_template('ordenes.html',master='3.0.26',snapshot='test',managed_orders={'records':[]},inbox={'candidates':[item]},tier_by_token={'SOL':'T1'},error=None)
  assert ('data-order=' in html)==button
  assert 'span hidden class="order-traffic' not in html
  assert html.count('id="orders-save-all"')==1
  assert '>Cambiar estado</button>' not in html
  assert 'Validar datos</button>' in html
  if button:assert 'class="orders-manage orders-next-state"' in html
  assert '<option value="PARCIAL">Parcial</option></select></label>' not in html

def test_pri_names_overweight_token_and_reference_amount():
 rows=[{'token':'HYPE' if i==0 else 'TOKEN'+str(i),'value':200 if i==0 else 100,'target':.1 if i==0 else .9/11} for i in range(12)]
 r=app.executive_risk_index(rows,100)
 assert 'HYPE' in r['explanation'] and '$70.00' in r['explanation']
 assert '10.0%' in r['explanation'] and 'referencial' in r['explanation']
 for row in rows:row['value']=100;row['target']=1/12
 assert 'No hay tokens' in app.executive_risk_index(rows,100)['explanation']
