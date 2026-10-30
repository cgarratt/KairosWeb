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
