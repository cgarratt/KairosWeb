"""Regression: sufficient historical coverage for 1W CL validation, no publication."""
from datetime import date, timedelta
from cl_review_history import required_daily_candles, fetch_closed_binance_history
from cl_validation import review_cl


def test_prior_protected_high_is_not_excluded_by_too_short_a_query():
    assert required_daily_candles('2026-07-01',now=date(2026,10,18))>=365
    assert required_daily_candles('2025-10-10',now=date(2026,10,18))>500


def test_retry_actual_history_without_claiming_automatic_confirmation():
    calls=[]
    def fetch(env,tool,args):
        calls.append(args['limit'])
        if len(calls)==1:
            return {'status':'DATA_ERROR','reason':'Insufficient closed candles: 425/583'}
        return {'status':'OK','closed_only':True,'symbol':'PLUMEUSDT','records':[]}
    result=fetch_closed_binance_history(fetch,'PLUME','2025-10-10',now=date(2026,10,18))
    assert calls==[583,425]
    assert result['status']=='OK'


def test_cl_weekly_review_requires_bos_even_with_pivot():
    monday=date(2026,1,5)
    weekly=[]
    for i in range(23):
        weekly.append({'week_start':(monday+timedelta(weeks=i)).isoformat(),
                       'week_end':(monday+timedelta(weeks=i,days=6)).isoformat(),
                       'low_date':(monday+timedelta(weeks=i,days=2)).isoformat(),
                       'high':30 if i==6 else 10,
                       'low':1 if i==12 else 5,
                       'close':8})
    dt=weekly[12]['low_date']
    assert not review_cl(weekly,1,dt)['validated']
    weekly[18]['high']=35
    weekly[18]['close']=31
    assert review_cl(weekly,1,dt)['validated']
