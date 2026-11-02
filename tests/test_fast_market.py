import asyncio, copy, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as a
TOKENS=('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PLUME','PEPE','VIRTUAL')

def spot(source='Binance Spot',age=0):
 return dict(status='OK',source=source,provider='KUCOIN' if source=='KuCoin Spot' else 'BINANCE',as_observed_utc=(datetime.now(timezone.utc)-timedelta(seconds=age)).isoformat(),records=[dict(symbol=t+'USDT',price='10',source=source) for t in TOKENS])

def bundle():
 day=datetime.now(timezone.utc).date().isoformat()
 return dict(status='OK',policy='MANUAL_SNAPSHOT',source='Binance Spot',histories={t+'USDT:1d':dict(status='OK',source='Binance Spot',symbol=t+'USDT',interval='1d',closed_only=True,records=[dict(close_utc=day+'T00:00:00+00:00',close='10')]) for t in TOKENS},indicators={},cycles={})

@pytest.fixture(autouse=True)
def setup(tmp_path,monkeypatch):
 monkeypatch.setattr(a,'_BINANCE_SNAPSHOT',None)
 monkeypatch.setattr(a,'_BINANCE_SNAPSHOT_PATH',tmp_path/'market.json')
 monkeypatch.setattr(a,'_active_mcp_pause',lambda env:None)
 monkeypatch.setattr(a,'_accept_mcp_response',lambda env,data:data)
 monkeypatch.setenv('KUCOIN_MCP_URL','https://backup.example/mcp')
 monkeypatch.setattr(a,'TOKENS',TOKENS)
 a._HIST_CACHE.clear()


def test_fast_spot_fetches_no_history(monkeypatch):
 remote=AsyncMock(return_value=spot());monkeypatch.setattr(a,'call_mcp',remote)
 a._refresh_binance_snapshot()
 assert remote.call_args.args[1]=='get_kairos_spot_prices'
 assert 'histories' not in a._BINANCE_SNAPSHOT


def test_cached_spot_no_request_preserves_time(monkeypatch):
 remote=AsyncMock(return_value=spot());monkeypatch.setattr(a,'call_mcp',remote)
 first=a._refresh_binance_snapshot();second=a._refresh_binance_snapshot()
 assert remote.call_count==1 and first==second


def test_timeout_falls_back_and_retains_history(monkeypatch):
 h=bundle();h.update(spot=spot(age=100),as_observed_utc='old',history_day_utc=datetime.now(timezone.utc).date().isoformat())
 a._BINANCE_SNAPSHOT=copy.deepcopy(h)
 remote=AsyncMock(side_effect=[TimeoutError(),spot('KuCoin Spot')]);monkeypatch.setattr(a,'call_mcp',remote)
 a._refresh_binance_snapshot()
 assert remote.call_count==2
 assert a._BINANCE_SNAPSHOT['fallback']['active']
 assert a._BINANCE_SNAPSHOT['histories']==h['histories']


def test_known_pause_skips_primary(monkeypatch):
 pause=a.PrimaryUnavailable(418)
 monkeypatch.setattr(a,'_active_mcp_pause',lambda env:pause if env=='BINANCE_MCP_URL' else None)
 remote=AsyncMock(return_value=spot('KuCoin Spot'));monkeypatch.setattr(a,'call_mcp',remote)
 a._refresh_binance_snapshot()
 assert remote.call_count==1 and remote.call_args.args[0]=='KUCOIN_MCP_URL'

@pytest.mark.parametrize('bad',['missing','duplicate','mixed','stale'])
def test_invalid_primary_does_not_use_backup(monkeypatch,bad):
 raw=spot()
 if bad=='missing':raw['records'].pop()
 if bad=='duplicate':raw['records'][1]=raw['records'][0]
 if bad=='mixed':raw['records'][0]['source']='KuCoin Spot'
 if bad=='stale':raw=spot(age=181)
 remote=AsyncMock(return_value=raw);monkeypatch.setattr(a,'call_mcp',remote)
 with pytest.raises((ValueError,RuntimeError)):a._refresh_binance_snapshot()
 assert remote.call_count==1 and a._BINANCE_SNAPSHOT is None


def test_both_fail_keep_previous_observation(monkeypatch):
 old=dict(status='OK',policy='MANUAL_SNAPSHOT',spot=spot(age=100))
 a._BINANCE_SNAPSHOT=copy.deepcopy(old)
 monkeypatch.setattr(a,'call_mcp',AsyncMock(side_effect=[TimeoutError(),TimeoutError()]))
 with pytest.raises(a.BackupUnavailable):a._refresh_binance_snapshot()
 assert a._BINANCE_SNAPSHOT==old


def test_history_does_not_change_spot_or_refetch_same_day(monkeypatch):
 a._BINANCE_SNAPSHOT=dict(status='OK',policy='MANUAL_SNAPSHOT',spot=spot('KuCoin Spot'),source='KuCoin Spot')
 before=copy.deepcopy(a._BINANCE_SNAPSHOT['spot'])
 remote=AsyncMock(return_value=bundle());monkeypatch.setattr(a,'call_mcp',remote)
 a._refresh_history_snapshot();a._refresh_history_snapshot()
 assert remote.call_count==1 and a._BINANCE_SNAPSHOT['spot']==before
 assert a._snapshot_response('get_kairos_ohlcv',dict(symbol='BTCUSDT',interval='1d',limit=1))['source']=='Binance Spot'


def test_history_missing_or_wrong_day_fails_closed(monkeypatch):
 for mode in ('incomplete','old_day'):
  raw=bundle()
  if mode=='incomplete':raw['histories'].pop('BTCUSDT:1d')
  else:raw['histories']['BTCUSDT:1d']['records'][0]['close_utc']='2020-01-01T00:00:00+00:00'
  monkeypatch.setattr(a,'call_mcp',AsyncMock(return_value=raw))
  with pytest.raises((RuntimeError,ValueError)):a._refresh_history_snapshot()
  assert a._BINANCE_SNAPSHOT is None


def test_disk_restart_restores_separate_data(monkeypatch):
 monkeypatch.setattr(a,'call_mcp',AsyncMock(return_value=spot()))
 a._refresh_binance_snapshot();before=copy.deepcopy(a._BINANCE_SNAPSHOT)
 a._BINANCE_SNAPSHOT=None
 assert a._read_binance_snapshot()==before


def test_history_only_then_spot_succeeds(monkeypatch):
 remote=AsyncMock(side_effect=[bundle(),spot()]);monkeypatch.setattr(a,'call_mcp',remote)
 a._refresh_history_snapshot();a._refresh_binance_snapshot()
 assert len(a._BINANCE_SNAPSHOT['histories'])==12 and len(a._BINANCE_SNAPSHOT['spot']['records'])==12


def test_previous_day_history_not_consumed():
 a._BINANCE_SNAPSHOT=dict(status='OK',policy='MANUAL_SNAPSHOT',history_day_utc='2020-01-01',**{'histories':bundle()['histories']})
 with pytest.raises(a.SpotRefreshRequired):a._snapshot_response('get_kairos_ohlcv',{'interval':'1d','limit':1})


def test_http_history_auth_and_csrf(monkeypatch):
 client=a.app.test_client()
 assert client.post('/api/history/refresh').status_code==401
 monkeypatch.setattr(a,'_portfolio_authorized',lambda:True)
 assert client.post('/api/history/refresh').status_code==403
 monkeypatch.setattr(a,'_same_origin',lambda:True);monkeypatch.setattr(a,'_csrf_ok',lambda:True)
 remote=Mock(return_value={'status':'OK'});monkeypatch.setattr(a,'_refresh_history_snapshot',remote)
 assert client.post('/api/history/refresh').status_code==200 and remote.call_count==1


def test_navigation_uses_sheets_cache_writes_force(monkeypatch):
 state=Mock(return_value={});monkeypatch.setattr(a,'get_state',state)
 for method in ('GET','POST'):
  with a.app.test_request_context('/mode/portafolio',method=method):
   a.bind_published_sheet()
   assert state.call_args.kwargs['force']==(method=='POST')


def test_concurrent_clicks_coalesce(monkeypatch):
 remote=AsyncMock(return_value=spot());monkeypatch.setattr(a,'call_mcp',remote)
 monkeypatch.setattr(a,'core_dashboard',lambda prices:{'prices':prices})
 with ThreadPoolExecutor(max_workers=4) as pool:values=list(pool.map(lambda _:a.load_live_dashboard(force=True),range(4)))
 assert remote.call_count==1 and len(values)==4


def test_history_and_spot_concurrent_updates_do_not_overwrite(monkeypatch):
 started=threading.Event();release=threading.Event()
 async def remote(env,tool,args):
  if tool=='get_kairos_dashboard_snapshot':
   started.set();assert release.wait(3);return bundle()
  return spot('KuCoin Spot')
 # History waits upstream while Spot can finish independently.
 monkeypatch.setattr(a,'call_mcp',remote)
 with ThreadPoolExecutor(max_workers=2) as pool:
  history=pool.submit(a._refresh_history_snapshot);assert started.wait(3)
  monkeypatch.setattr(a,'_active_mcp_pause',lambda env:a.PrimaryUnavailable(418) if env=='BINANCE_MCP_URL' else None)
  a._refresh_binance_snapshot();release.set();history.result()
 assert a._BINANCE_SNAPSHOT['spot']['source']=='KuCoin Spot'
 assert len(a._BINANCE_SNAPSHOT['histories'])==12

@pytest.mark.parametrize('field,value',[('as_observed_utc','2026-11-02T12:00:00'),('boolean',True)])
def test_naive_timestamp_and_boolean_price_rejected(field,value):
 raw=spot()
 if field=='boolean':raw['records'][0]['price']=value
 else:raw[field]=value
 with pytest.raises(ValueError):a._validate_spot_payload(raw)


def test_spot_timeout_config_and_history_budget(monkeypatch):
 assert a._mcp_timeout('BINANCE_MCP_URL','get_kairos_spot_prices')==10
 assert a._mcp_timeout('KUCOIN_MCP_URL','get_kairos_kucoin_spot_prices')==45
 assert a._mcp_timeout('BINANCE_MCP_URL','get_kairos_dashboard_snapshot')==150
 monkeypatch.setenv('KAIROS_PRIMARY_SPOT_TIMEOUT_SECONDS','8')
 assert a._mcp_timeout('BINANCE_MCP_URL','get_kairos_spot_prices')==8


def test_history_failure_keeps_valid_spot(monkeypatch):
 a._BINANCE_SNAPSHOT={'status':'OK','policy':'MANUAL_SNAPSHOT','spot':spot('KuCoin Spot')}
 before=copy.deepcopy(a._BINANCE_SNAPSHOT)
 monkeypatch.setattr(a,'call_mcp',AsyncMock(side_effect=TimeoutError()))
 with pytest.raises(TimeoutError):a._refresh_history_snapshot()
 assert a._BINANCE_SNAPSHOT==before


def test_history_button_uses_explicit_request_only():
 import subprocess
 script=r'''
 const vm=require('vm'),fs=require('fs'),assert=require('assert');
 let requests=[],timers=[],reloads=0;
 const button=()=>({dataset:{csrf:'secret'},addEventListener(event,fn){this.click=fn;}});
 const spot=button(),history=button(),label={},historyLabel={};
 const elements={'spot-refresh':spot,'history-refresh':history,'spot-observed':label,'history-observed':historyLabel};
 const context={Date,Intl,console,setInterval:fn=>timers.push(fn),
 document:{getElementById:id=>elements[id]||null},
 fetch:async(url,opts)=>{requests.push({url,opts});return {ok:true,json:async()=>url==='/api/market-status'?{backup_configured:true}:{status:'OK'}}},
 window:{location:{reload:()=>reloads++}}};
 vm.runInNewContext(fs.readFileSync('static/spot_refresh.js','utf8'),context);
 (async()=>{
 await new Promise(setImmediate);
 assert.deepEqual(requests.map(r=>r.url),['/api/market-status','/api/market-status']);
 timers.forEach(fn=>fn());assert.equal(requests.length,2);
 await history.click();assert.equal(requests[2].url,'/api/history/refresh');
 assert.equal(requests[2].opts.headers['X-Kairos-Csrf'],'secret');
 assert.equal(requests[2].opts.method,'POST');assert.equal(reloads,0);
 assert(!history.disabled);
 })().catch(e=>{console.error(e);process.exitCode=1;});
 '''
 subprocess.run(['node','-e',script],check=True)


def test_primary_deadline_covers_connection_and_invocation(monkeypatch):
 async def slow(*args):
  await asyncio.sleep(.1)
 monkeypatch.setattr(a,'call_mcp',slow)
 monkeypatch.setattr(a,'_mcp_timeout',lambda env,tool:.001)
 with pytest.raises(TimeoutError):asyncio.run(a._spot_call('BINANCE_MCP_URL','get_kairos_spot_prices'))


@pytest.mark.parametrize('provider,source,tool',[('binance','Binance Spot','get_kairos_spot_prices'),('kucoin','KuCoin Spot','get_kairos_kucoin_spot_prices')])
def test_diagnostics_queries_own_provider_without_valuation(monkeypatch,provider,source,tool):
 monkeypatch.setenv('BINANCE_MCP_URL','https://primary.example/mcp')
 remote=AsyncMock(return_value=spot(source));monkeypatch.setattr(a,'call_mcp',remote)
 fallback=Mock(side_effect=AssertionError('No valuation fallback in diagnostics'))
 monkeypatch.setattr(a,'call_mcp_resilient',fallback)
 before=copy.deepcopy(a._BINANCE_SNAPSHOT)
 result=a._check_provider(provider)
 assert result['status']=='OK' and result['source']==source and result['records']==12
 assert remote.call_args.args[1]==tool and remote.call_count==1
 assert a._BINANCE_SNAPSHOT==before

@pytest.mark.parametrize('provider,source',[('binance','KuCoin Spot'),('kucoin','Binance Spot')])
def test_diagnostics_rejects_other_provider(monkeypatch,provider,source):
 monkeypatch.setenv('BINANCE_MCP_URL','https://primary.example/mcp')
 monkeypatch.setattr(a,'call_mcp',AsyncMock(return_value=spot(source)))
 assert a._check_provider(provider)['status']=='DATA_ERROR'

@pytest.mark.parametrize('bad',['missing','duplicate','stale'])
def test_kucoin_diagnostics_validates_coverage_and_age(monkeypatch,bad):
 raw=spot('KuCoin Spot',age=181 if bad=='stale' else 0)
 if bad=='missing':raw['records'].pop()
 if bad=='duplicate':raw['records'][1]=raw['records'][0]
 monkeypatch.setattr(a,'call_mcp',AsyncMock(return_value=raw))
 assert a._check_provider('kucoin')['status']=='DATA_ERROR'


def test_diagnostic_honors_primary_pause_while_backup_works(monkeypatch):
 monkeypatch.setenv('BINANCE_MCP_URL','https://primary.example/mcp')
 pause=a.MCPRateLimitError(418,datetime.now(timezone.utc)+timedelta(minutes=5))
 monkeypatch.setattr(a,'_active_mcp_pause',lambda env:pause if env=='BINANCE_MCP_URL' else None)
 remote=AsyncMock(return_value=spot('KuCoin Spot'));monkeypatch.setattr(a,'call_mcp',remote)
 assert a._check_provider('binance')['status']=='DATA_ERROR'
 assert remote.call_count==0
 assert a._check_provider('kucoin')['status']=='OK'
 assert remote.call_count==1


def test_kucoin_not_configured_no_remote_call(monkeypatch):
 monkeypatch.delenv('KUCOIN_MCP_URL')
 remote=AsyncMock();monkeypatch.setattr(a,'call_mcp',remote)
 assert a._check_provider('kucoin')['status']=='NOT_CONFIGURED'
 assert remote.call_count==0


def test_diagnostic_modules_allow_spot_backup_only():
 providers={name:{'status':'OK'} for name in ('sheets','kucoin','hyperliquid')}
 providers['binance']={'status':'DATA_ERROR'}
 states=a._module_dependency_states(providers)
 for name in ('portafolio','balancer','ventas'):assert states[name]['status']=='DEPENDENCIES_OK'
 assert states['tradingbot']['status']=='BLOCKED_OR_PARTIAL'
 assert states['compras']['status']=='BLOCKED_OR_PARTIAL'


def test_kucoin_diagnostic_routes_and_refresh(monkeypatch):
 monkeypatch.setattr(a,'_portfolio_authorized',lambda:True)
 monkeypatch.setattr(a,'_admin_authorized',lambda:True)
 monkeypatch.setattr(a,'_same_origin',lambda:True)
 monkeypatch.setattr(a,'_csrf_ok',lambda:True)
 remote=AsyncMock(return_value=spot('KuCoin Spot'));monkeypatch.setattr(a,'call_mcp',remote)
 with a.app.test_client() as c:
  check=c.get('/api/mcp-diagnostics?provider=kucoin').get_json()['providers']['kucoin']
  assert check['status']=='OK' and check['source']=='KuCoin Spot'
  result=c.post('/api/mcp-refresh',json={'provider':'kucoin'}).get_json()
  assert result['result']['status']=='OK' and result['provider']=='kucoin'
  assert c.get('/api/mcp-config-check').get_json()['checks']['kucoin']['configured']


def test_history_control_only_in_settings():
 from flask import render_template
 with a.app.test_request_context('/settings'):
  html=render_template('settings.html',master=a.APP_VERSION,portfolio_authenticated=True)
  assert html.count('id="history-refresh"')==1 and 'data-provider="kucoin"' in html
  assert html.index('id="settings-mcp-panel"')<html.index('id="history-refresh"')
 with a.app.test_request_context('/'):
  html=render_template('base.html',master=a.APP_VERSION,portfolio_authenticated=True)
  assert 'id="history-refresh"' not in html and 'id="spot-refresh"' in html


def test_integral_health_includes_kucoin(monkeypatch):
 monkeypatch.setattr(a,'_portfolio_authorized',lambda:True)
 probe=Mock(return_value={'status':'OK'});monkeypatch.setattr(a,'_live_provider_probe',probe)
 monkeypatch.setattr(a,'_deployed_asset_status',lambda:{'consistent':True})
 with a.app.test_client() as c:
  r=c.get('/api/health/diagnostics')
  assert r.status_code==200
  assert set(r.get_json()['operational_providers'])=={'sheets','binance','kucoin','hyperliquid'}
 assert probe.call_count==4


def test_binance_refresh_cannot_mask_outage_with_backup(monkeypatch):
 monkeypatch.setattr(a,'_portfolio_authorized',lambda:True)
 monkeypatch.setattr(a,'_admin_authorized',lambda:True)
 monkeypatch.setattr(a,'_same_origin',lambda:True)
 monkeypatch.setattr(a,'_csrf_ok',lambda:True)
 check=Mock(return_value={'status':'DATA_ERROR','diagnostic':{'code':'RATE_LIMIT'}})
 monkeypatch.setattr(a,'_check_provider',check)
 valuation=Mock(side_effect=AssertionError('Do not refresh valuation in provider diagnostics'))
 monkeypatch.setattr(a,'load_live_dashboard',valuation)
 with a.app.test_client() as c:
  r=c.post('/api/mcp-refresh',json={'provider':'binance'})
  assert r.status_code==503 and r.get_json()['result']['status']=='DATA_ERROR'
 check.assert_called_once_with('binance');valuation.assert_not_called()
