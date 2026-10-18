from datetime import date, timedelta
from wave_structure import full_utc_weeks
from wave_macro_context import resolve_long_term_buy
from buy_weekly_policy import proposed_simulation_impulse


def daily_payload():
    records=[];first=date(2025,1,6)
    for i in range(45):
        hi={6:150,29:170,32:200}.get(i,110)
        lo={20:50}.get(i,90)
        close=(160 if i==29 else 100)
        for day in range(7):
            d=first+timedelta(weeks=i,days=day)
            records.append({'open_utc':d.isoformat()+'T00:00:00+00:00',
                            'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
                            'high':hi if day==0 else max(105,close),
                            'low':lo if day==2 else 95,
                            'close':close if day==6 else 100})
    return {'status':'OK','source':'Binance Spot','interval':'1d',
            'closed_only':True,'records':records}


def test_web_allows_proposed_for_simulation_and_blocks_nd():
    data=daily_payload();w=full_utc_weeks(data['records'])
    lo=next(x for x in w if x['low']==50)
    hi=next(x for x in w if x['high']==200)
    proposal={'cycle_low':lo['low'],'cl_date':lo['low_date'],'cl_status':'PROPUESTO',
       'waves':{'o1':{'price':hi['high'],'date':hi['high_date'],'status':'PROPUESTO'}}}
    result=resolve_long_term_buy('BTC',proposal,data)
    assert result['eligible'] and result['simulation_only']
    assert result['operational_blocked'] and result['levels']['c1']==125
    assert result['mode']=='O2'
    no_high=resolve_long_term_buy('BTC',{'cycle_low':lo['low'],
                            'cl_date':lo['low_date'],'cl_status':'PROPUESTO'},data)
    assert not no_high['eligible']
    assert no_high['levels'] is None


def test_web_accepts_historical_mcp_proposal_as_provisional_only():
    data=daily_payload();w=full_utc_weeks(data['records'])
    lo=next(x for x in w if x['low']==50);hi=next(x for x in w if x['high']==200)
    archive={'cycle_low':lo['low'],'cl_date':lo['low_date'],
             'o1':hi['high'],'o1_date':hi['high_date']}
    result=resolve_long_term_buy('BTC',{},data,archive)
    assert result['eligible'] and result['status']=='PROPUESTO_SIMULACION'
    assert result['operational_blocked'] and result['simulation_only']
