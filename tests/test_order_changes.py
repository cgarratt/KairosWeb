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

@pytest.mark.parametrize('mode,prefix',[('O2','O2'),('RETROCESO_ALCISTA','O2'),(None,'O2'),('O4','O4')])
def test_funded_generic_retracements_survive_cycle_filter(mode,prefix):
 from test_zero_fibo import payload
 from orders_inbox import staged_buy_candidates,classify_purchase_views,visible_order_rows
 b=payload()
 for context in b['weekly_context'].values():context['mode']=mode
 candidates,_=staged_buy_candidates(b,100)
 classify_purchase_views(b,candidates)
 visible,_=visible_order_rows(candidates,[])
 assert {r['stage'] for r in visible}=={prefix+'C2',prefix+'C3',prefix+'C4'}
 assert all(app._cycle_order_allowed(r['side'],r['stage']) for r in visible)
 assert all(r['usdt']>0 for r in visible)
 with app.app.test_request_context('/'):
  html=app.render_template('ordenes.html',master='3.0.28',snapshot='test',managed_orders={'records':[]},inbox={'candidates':visible},tier_by_token={'SOL':'T1'},error=None)
 for stage in [prefix+'C2',prefix+'C3']:assert 'data-stage="'+stage+'"' in html
 assert html.count('id="orders-save-all"')==1


def test_zero_visibility_preserves_journal_and_displays_real_receipts():
 from copy import deepcopy
 from orders_inbox import visible_order_rows
 candidates=[dict(token='SOL',side='BUY',usdt=v) for v in [0,None,.004,10]]
 candidates.append(dict(token='ETH',side='SELL',usdt=None))
 records=[dict(proposal(state),effective_status=state,importe_previsto=planned,importe_ejecutado=actual,unidades_ejecutadas=2)
          for state,planned,actual in [('PROPUESTA',0,0),('NO_APLICA',20,0),('CONFIRMADA',20,0),('EJECUTADA',0,30),('EJECUTADA',0,0),('PARCIAL',100,10)]]
 before=deepcopy((candidates,records))
 visible,registered=visible_order_rows(candidates,records)
 assert [r['usdt'] for r in visible]==[10,None]
 assert [r['display_usdt'] for r in registered]==[20,30,10]
 assert (candidates,records)==before
 with app.app.test_request_context('/'):
  html=app.render_template('ordenes.html',master='3.0.28',snapshot='test',managed_orders={'records':registered},inbox={'candidates':[]},tier_by_token={'SOL':'T1'},error=None)
 assert '30.00 USDT' in html and '10.00 USDT' in html
 assert html.count('data-stage="O2C2"')==3


def test_orders_route_classifies_then_hides_zero_without_changing_source():
 from copy import deepcopy
 from flask import g
 from test_zero_fibo import payload
 b=payload()
 for ctx in b['weekly_context'].values():ctx['mode']='RETROCESO_ALCISTA'
 source={'records':[dict(proposal('EJECUTADA'),importe_previsto=0,importe_ejecutado=0,conciliacion='CONCILIADA_EN_05')],'historical':[]}
 original=deepcopy(source)
 d={'rows':[{'token':'SOL','tier':'T1'}]}
 from orders_inbox import staged_buy_candidates
 candidates,_=staged_buy_candidates(b,100)
 with app.app.test_request_context('/mode/ordenes'):
  g.kairos_state={'control':{'snapshot_id':'test'},'wave_pivots':{}}
  with patch('orders_workflow.registered_orders',return_value=deepcopy(source)),patch.object(app,'load_live_dashboard',return_value=('test',d)),patch.object(app,'balancer_report',return_value={}),patch.object(app,'build_mode_payload',return_value=b),patch('wave_macro_context.published_wave_levels',return_value={}),patch('orders_inbox.build_order_inbox',return_value={'candidates':candidates}):
   html=app.orders_inbox_page()
 assert 'data-stage="O2C2"' in html and 'data-stage="O2C3"' in html
 assert 'data-stage="O2C1"' not in html
 assert '0.00 USDT</td>' not in html
 assert source==original


def multiscale_buy_fixture():
 # Mixed quote scales make stale-loop-variable regressions observable.
 tokens=[dict(token='BTC',price=70000,current_usdt=100,target=.4),
         dict(token='ETH',price=2000,current_usdt=100,target=.3),
         dict(token='LINK',price=10,current_usdt=9700,target=.275),
         dict(token='PEPE',price=.000004,current_usdt=100,target=.025)]
 weights=[0,40,40,20]
 return dict(tokens=tokens,o2_levels={t['token']:dict(zip(('ref382','c1','c2','ref786'),[t['price']*x for x in (.95,.9,.8,.7)])) for t in tokens},
             buy_eligibility={t['token']:True for t in tokens},forecast_o2_allocation=weights,
             buy_stage_weights={t['token']:weights for t in tokens},
             weekly_context={t['token']:{'mode':'O2'} for t in tokens},drift_band_pp=.5,
             buy_order_states={})


@pytest.mark.parametrize('last',['BTC','ETH','LINK','PEPE'])
def test_each_token_uses_own_spot_independent_of_list_order(last):
 from orders_inbox import staged_buy_candidates,classify_purchase_views,visible_order_rows
 b=multiscale_buy_fixture()
 def run():
  rows,_=staged_buy_candidates(b,1000);classify_purchase_views(b,rows)
  return {(r['token'],r['stage']):r['usdt'] for r in visible_order_rows(rows,[])[0]}
 baseline=run()
 assert baseline[('BTC','O2C2')]>0 and baseline[('ETH','O2C3')]>0
 b['tokens'].sort(key=lambda t:t['token']==last)
 assert run()==pytest.approx(baseline)


@pytest.mark.parametrize('state',['CONFIRMADA','EJECUTADA','FILLED','NO_APLICA'])
def test_last_token_order_state_does_not_block_other_tokens(state):
 from orders_inbox import staged_buy_candidates
 b=multiscale_buy_fixture();b['buy_order_states']={'PEPE':{'O2C2':state},'BTC':{'O2C3':state}}
 rows,_=staged_buy_candidates(b,1000)
 amounts={(r['token'],r['stage']):r['usdt'] for r in rows if r['usdt']>0}
 assert amounts[('BTC','O2C2')]>0 and amounts[('ETH','O2C2')]>0
 assert ('PEPE','O2C2') not in amounts and ('BTC','O2C3') not in amounts
 assert amounts[('BTC','O2C4')]>0


def test_orders_python_matches_purchase_javascript_multiscale():
 import json,subprocess
 from orders_inbox import staged_buy_candidates
 b=multiscale_buy_fixture()
 b['buy_order_states']={'BTC':{'O2C3':'FILLED'},'PEPE':{'O2C2':'NO_APLICA'}}
 rows,remaining=staged_buy_candidates(b,1000)
 source="""const fs=require('fs'),b=JSON.parse(fs.readFileSync(0,'utf8'));
 const sim=require('./static/o2_sequential.js').calculate(b.tokens,b.o2_levels,b.forecast_o2_allocation,1000,b.drift_band_pp,{requireEligibility:true,eligibility:b.buy_eligibility,weightsByToken:b.buy_stage_weights,orderStates:b.buy_order_states,modes:Object.fromEntries(Object.keys(b.weekly_context).map(t=>[t,'O2']))});
 console.log(JSON.stringify(sim));"""
 result=subprocess.run(['node','-e',source],input=json.dumps(b),capture_output=True,text=True,check=True)
 sim=json.loads(result.stdout);amounts={(r['token'],r['stage']):r['usdt'] for r in rows}
 for i,t in enumerate(b['tokens']):
  for j in range(4):assert amounts.get((t['token'],'O2C'+str(j+1)),0)==pytest.approx(sim['amounts'][i][j])
 assert remaining==pytest.approx(sim['cash'])

@pytest.mark.parametrize('status',[418,429])
def test_binance_pause_prevents_network_retries_and_preserves_expiry(status):
 from datetime import datetime,timezone,timedelta
 from unittest.mock import AsyncMock
 until=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
 app._MCP_PAUSES.clear()
 try:
  with patch.object(app,'call_mcp',new=AsyncMock(return_value={'status':'DATA_ERROR','http_status':status,'retry_at_utc':until} )) as net,patch.object(app.time,'sleep') as sleep:
   for _ in range(2):
    with pytest.raises(app.MCPRateLimitError) as err:app._call_mcp_with_retries('BINANCE_MCP_URL','get_kairos_spot_prices',{})
   assert net.call_count==1;sleep.assert_not_called()
   diag=app.diagnostic_error(err.value,'test')
   assert diag['http_status']==status and diag['retry_at_utc']==until
   assert app.market_cache_status()['retry_at_utc']==until
 finally:app._MCP_PAUSES.clear()


def test_expired_binance_pause_allows_fresh_fetch():
 from datetime import datetime,timezone,timedelta
 from unittest.mock import AsyncMock
 app._MCP_PAUSES['BINANCE_MCP_URL']=(418,datetime.now(timezone.utc)-timedelta(seconds=1))
 try:
  with patch.object(app,'call_mcp',new=AsyncMock(return_value={'status':'OK'})) as net:
   assert app._call_mcp_with_retries('BINANCE_MCP_URL','get_kairos_spot_prices',{})['status']=='OK'
   assert net.call_count==1
 finally:app._MCP_PAUSES.clear()


def test_manual_spot_refresh_preserves_closed_history_cache():
 app._HIST_CACHE['test']={'status':'OK'}
 try:
  with app.app.test_request_context('/api/spot/refresh',method='POST'):
   with patch.object(app,'_portfolio_authorized',return_value=True),patch.object(app,'_same_origin',return_value=True),patch.object(app,'_csrf_ok',return_value=True),patch.object(app,'load_live_dashboard',return_value=('test',{})):
    response=app.spot_refresh()
    assert response.json['history']=='MANUAL_BUNDLED_SNAPSHOT'
    assert app._HIST_CACHE['test']=={'status':'OK'}
 finally:app._HIST_CACHE.pop('test',None)


def test_pause_ui_disables_then_expires_without_automatic_mcp_poll():
 import subprocess
 script=r"""
 const fs=require('fs'),vm=require('vm'),assert=require('assert');let timer,click,requests=[];
 const button={dataset:{csrf:'test'},addEventListener:(name,fn)=>click=fn},label={};
 const now=Date.now(),deadline=new Date(now+60000).toISOString();
 let clock=now;class TestDate extends Date{static now(){return clock;}}
 const context={Date:TestDate,Intl,console,setInterval:fn=>timer=fn,
 document:{getElementById:id=>id==='spot-refresh'?button:label,
 querySelectorAll:()=>[{getAttribute:()=>deadline}]},
 fetch:async(url)=>{requests.push(url);return {json:async()=>({retry_at_utc:deadline,http_status:418})}},window:{location:{reload:()=>assert.fail('No auto reload')}}};
 vm.runInNewContext(fs.readFileSync('static/spot_refresh.js','utf8'),context);
 (async()=>{await new Promise(resolve=>setImmediate(resolve));assert(button.disabled);
 await click();assert.deepStrictEqual(requests,['/api/market-status']);
 clock=now+61000;timer();assert(!button.disabled);
 assert.deepStrictEqual(requests,['/api/market-status']);})().catch(e=>{console.error(e);process.exitCode=1;});
 """
 subprocess.run(['node','-e',script],check=True)

# Manual Binance snapshot integration: all network edges are mocked.
def test_binance_navigation_never_calls_transport(tmp_path):
 from unittest.mock import patch
 with patch.object(app,'_BINANCE_SNAPSHOT',None),patch.object(app,'_BINANCE_SNAPSHOT_PATH',tmp_path/'snapshot.json'),patch.object(app,'call_mcp') as net:
  for tool,args in [('get_kairos_spot_prices',{}),('get_kairos_ohlcv',{'symbol':'BTCUSDT','interval':'1d','limit':210}),('get_kairos_indicators',{'symbol':'BTCUSDT','interval':'1h'})]:
   with pytest.raises(app.SpotRefreshRequired):app.call_mcp_resilient('BINANCE_MCP_URL',tool,args)
  net.assert_not_called()

def _manual_bundle():
 observed=app.datetime.now(app.timezone.utc).isoformat()
 spot={'status':'OK','as_observed_utc':observed,'records':[{'symbol':'BTCUSDT','price':'100'}]}
 return {'status':'OK','policy':'MANUAL_SNAPSHOT','as_observed_utc':observed,'spot':spot,
         'histories':{'BTCUSDT:1d':{'status':'OK','symbol':'BTCUSDT','interval':'1d','source':'Binance Spot','closed_only':True,'count':3,'records':[{'close':'1'},{'close':'2'},{'close':'3'}]}}}

def test_manual_refresh_is_one_tool_call_and_navigation_uses_local_bundle(tmp_path):
 from unittest.mock import AsyncMock,patch
 bundle=_manual_bundle()
 with patch.object(app,'_BINANCE_SNAPSHOT',None),patch.object(app,'_BINANCE_SNAPSHOT_PATH',tmp_path/'snapshot.json'),patch.object(app,'_active_mcp_pause',return_value=None),patch.object(app,'_validate_spot_payload',return_value=(bundle['as_observed_utc'],{'BTC':100})),patch.object(app,'call_mcp',new_callable=AsyncMock,return_value=bundle) as net:
  app._refresh_binance_snapshot()
  for _ in range(3):
   assert app.call_mcp_resilient('BINANCE_MCP_URL','get_kairos_spot_prices')['as_observed_utc']==bundle['as_observed_utc']
   result=app.call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',{'symbol':'BTCUSDT','interval':'1d','limit':2})
   assert result['records']==[{'close':'2'},{'close':'3'}]
  net.assert_awaited_once_with('BINANCE_MCP_URL','get_kairos_dashboard_snapshot',{})
  # A worker restart loads the saved observation, without opening MCP.
  app._BINANCE_SNAPSHOT=None
  assert app._snapshot_response('get_kairos_spot_prices')['as_observed_utc']==bundle['as_observed_utc']
  assert net.await_count==1

def test_expired_spot_does_not_automatically_refresh():
 from unittest.mock import patch
 data=_manual_bundle()['spot'];data['as_observed_utc']=(app.datetime.now(app.timezone.utc)-app.timedelta(seconds=181)).isoformat()
 with patch.object(app,'TOKENS',['BTC']),patch.object(app,'_snapshot_response',return_value=data),patch.object(app,'_refresh_binance_snapshot') as net:
  with pytest.raises(app.SpotRefreshRequired):app._load_live_dashboard_uncached()
  net.assert_not_called()

def test_failed_refresh_keeps_original_bundle_and_does_not_retry(tmp_path):
 from unittest.mock import AsyncMock,patch
 previous=_manual_bundle()
 with patch.object(app,'_BINANCE_SNAPSHOT',previous),patch.object(app,'_BINANCE_SNAPSHOT_PATH',tmp_path/'snapshot.json'),patch.object(app,'_active_mcp_pause',return_value=None),patch.object(app,'call_mcp',new_callable=AsyncMock,side_effect=TimeoutError) as net:
  with pytest.raises(TimeoutError):app._refresh_binance_snapshot()
  assert app._BINANCE_SNAPSHOT is previous
  assert net.await_count==1
