from datetime import date,timedelta
import ast, math, types, unittest
from datetime import datetime,timezone
from pathlib import Path
# Execute the production chart function in isolation; no Flask/network dependency.
source=Path(__file__).resolve().parents[1]/'app.py'
tree=ast.parse(source.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_btc_weekly_chart')
namespace={'datetime':datetime,'timezone':timezone,'math':math}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace)
app=types.SimpleNamespace(_btc_weekly_chart=namespace['_btc_weekly_chart'],datetime=datetime,timezone=timezone)

def series(n=30):
 first=date(2025,1,6);weeks=[];daily=[]
 for i in range(n):
  day=first+timedelta(weeks=i)
  weeks.append(dict(week_start=day.isoformat(),week_end=(day+timedelta(days=6)).isoformat(),high=110,low=90,close=100,high_date=day.isoformat(),low_date=day.isoformat()))
  daily.append(dict(open_utc=day.isoformat()+'T00:00:00Z',open=100))
 return weeks,daily

def chart(w,d,cl=None):return app._btc_weekly_chart(w,d,cl or w[0]['week_start'])

def test_two_right_weeks_are_not_confirmation():
 w,d=series(13);w[10]['high']=150
 assert chart(w,d)['pivots']==[]

def test_five_right_weeks_and_confirmation_date():
 w,d=series(16);w[10]['high']=150
 c=chart(w,d);assert len(c['pivots'])==1
 assert c['pivots'][0]['price']==150
 assert c['pivots'][0]['confirmed_at_utc']=='2025-04-28T00:00:00Z'
 assert c['pivot_rule'].startswith('5L/5R')

def test_fifth_left_and_right_extrema_reject_pivot():
 for j in (5,15):
  w,d=series(21);w[10]['high']=150;w[j]['high']=160
  assert not any(p['date']==w[10]['high_date'] and p['kind']=='H' for p in chart(w,d)['pivots'])

def test_equal_high_is_not_strict_pivot():
 w,d=series(16);w[10]['high']=150;w[5]['high']=150
 assert not any(p['date']==w[10]['high_date'] for p in chart(w,d)['pivots'])

def test_latest_three_confirmed_preserve_chronology():
 w,d=series(40)
 for i in (5,15,25):w[i]['high']=150+i
 w[35]['high']=200 # only four weeks to its right: excluded
 c=chart(w,d);assert [p['price'] for p in c['pivots']]==[155,165,175]

def test_pre_cl_weeks_count_on_left_without_showing_old_pivots():
 w,d=series(20);w[8]['low']=60
 c=chart(w,d,w[7]['week_start']);assert c['pivots'][0]['index']==1

def test_gap_does_not_substitute_an_extra_week():
 w,d=series(16);w[10]['high']=150;w.pop(8)
 assert chart(w,d)['pivots']==[]

def test_current_week_cannot_be_fifth_right_confirmation():
 today=app.datetime.now(app.timezone.utc).date();monday=today-timedelta(days=today.weekday())
 w,d=series(16)
 for i in range(16):
  day=monday-timedelta(weeks=15-i)
  w[i].update(week_start=day.isoformat(),week_end=(day+timedelta(days=6)).isoformat(),high_date=day.isoformat(),low_date=day.isoformat())
  d[i]['open_utc']=day.isoformat()+'T00:00:00Z'
 w[10]['high']=150
 assert chart(w,d)['pivots']==[]

if __name__=='__main__':
 suite=unittest.TestSuite(unittest.FunctionTestCase(fn) for name,fn in list(globals().items()) if name.startswith('test_') and callable(fn))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise SystemExit(1)

# Integration with the explicit historical snapshot (not the retired prefetch cache).
import sys,copy,json,subprocess,pytest
sys.path.insert(0,str(source.parent))
import app as web
from unittest.mock import Mock

@pytest.fixture
def historical_snapshot(monkeypatch,tmp_path):
 today=datetime.now(timezone.utc).date()
 records=[]
 for i in range(450):
  day=today-timedelta(days=450-i);price=100+i
  records.append({'open_utc':day.isoformat()+'T00:00:00Z',
    'close_utc':(day+timedelta(days=1)).isoformat()+'T00:00:00Z',
    'open':str(price),'high':str(price+3),'low':str(price-3),'close':str(price+1)})
 data={'status':'OK','source':'Binance Spot','symbol':'BTCUSDT','interval':'1d','closed_only':True,'records':records}
 snapshot={'status':'OK','policy':'MANUAL_SNAPSHOT','history_day_utc':today.isoformat(),'histories':{'BTCUSDT:1d':data}}
 monkeypatch.setattr(web,'_BINANCE_SNAPSHOT',snapshot)
 monkeypatch.setattr(web,'_BINANCE_SNAPSHOT_PATH',tmp_path/'absent.json')
 monkeypatch.setattr(web,'call_mcp',Mock(side_effect=AssertionError('Trend must not fetch market data')))
 monkeypatch.setattr(web,'call_mcp_resilient',Mock(side_effect=AssertionError('Trend must not fetch market data')))
 return snapshot


def test_chart_uses_full_loaded_history_from_cl(historical_snapshot):
 from wave_structure import full_utc_weeks
 data=historical_snapshot['histories']['BTCUSDT:1d'];weeks=full_utc_weeks(data['records'])
 cl=weeks[3]['week_start']
 result=web.cached_btc_weekly_regime(cl)
 assert result['status']=='OK' and result['source']=='Binance Spot'
 assert result['candles'][0]['week_start']==cl
 assert len(result['candles'])>30 # the old210-day window could not cover thisCL
 assert result['week']==weeks[-1]['week_end']
 assert result['pivot_rule'].startswith('5L/5R')


@pytest.mark.parametrize('bad',['stale','missing','wrong_source','gap','incomplete_week'])
def test_trend_explains_unavailable_history(historical_snapshot,bad):
 snapshot=historical_snapshot;data=snapshot['histories']['BTCUSDT:1d']
 if bad=='stale':snapshot['history_day_utc']='2020-01-01'
 if bad=='missing':snapshot['histories']={}
 if bad=='wrong_source':data['source']='Wrong Spot'
 if bad=='gap':data['records'].pop(-50)
 if bad=='incomplete_week':
  today=datetime.now(timezone.utc).date();day=today-timedelta(days=today.weekday()+4)
  data['records'][:]=[r for r in data['records'] if not r['open_utc'].startswith(day.isoformat())]
 result=web.cached_btc_weekly_regime('2025-01-06')
 assert result['regime']=='N/D' and result['reason'] and not result['candles']


def test_no_history_is_terminal_not_loading(historical_snapshot,monkeypatch):
 monkeypatch.setattr(web,'_BINANCE_SNAPSHOT',None)
 result=web.cached_btc_weekly_regime('2025-01-06')
 assert result['status']=='HISTORY_REQUIRED' and 'Configuración' in result['reason']


def test_missing_cl_keeps_regime_but_explains_chart(historical_snapshot):
 result=web.cached_btc_weekly_regime()
 assert result['status']=='OK' and not result['candles']
 assert result['reason']=='BTC CL publicado no disponible'


def test_frontend_reports_missing_history_and_http_errors():
 html=(source.parent/'templates/portfolio_integral.html').read_text()
 pos=html.index("const panel=document.getElementById('btc-trend-display');")
 script=html[html.rfind('<script>',0,pos)+len('<script>'):html.index('</script>',pos)]
 script=script.replace('{{ url_for("portfolio_btc_trend_status") }}','/api/portfolio/btc-trend')
 driver=r'''
 const vm=require('vm'),assert=require('assert');
 const script=SCRIPT;
 (async()=>{
 for(const mode of ['missing','http','network']){
 const panel={dataset:{regime:'N/D'}},empty={},week={},label={},icon={};let requests=0;
 const chart={querySelector:()=>empty};
 const nodes={'btc-trend-display':panel,'btc-weekly-pivot-chart':chart,'btc-trend-week':week,'btc-trend-label':label,'btc-trend-icon':icon};
 const ctx={AbortController,setTimeout:()=>1,clearTimeout:()=>{},
  document:{getElementById:id=>nodes[id]},
  fetch:async()=>{requests++;if(mode==='network')throw Error('network');return {ok:mode!=='http',json:async()=>({regime:'N/D',reason:'Actualizar históricos en Configuración'})};}};
 vm.runInNewContext(script,ctx);await new Promise(setImmediate);
 assert.equal(requests,1);assert.equal(label.textContent,'N/D');
 assert(week.textContent.includes('Configuración'));assert.equal(empty.textContent,week.textContent);
 }
 })().catch(e=>{console.error(e);process.exitCode=1;});
 '''.replace('SCRIPT',json.dumps(script))
 subprocess.run(['node','-e',driver],check=True)


def test_trend_reads_primary_kucoin_history(historical_snapshot):
 data=historical_snapshot['histories']['BTCUSDT:1d'];data['source']='KuCoin Spot'
 from wave_structure import full_utc_weeks
 weeks=full_utc_weeks(data['records'])
 result=web.cached_btc_weekly_regime(weeks[2]['week_start'])
 assert result['status']=='OK' and result['source']=='KuCoin Spot' and result['candles']
