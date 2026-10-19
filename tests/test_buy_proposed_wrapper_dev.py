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


def test_web_accepts_proposed_p1_and_proposed_p2_as_simulation():
    data=daily_payload();w=full_utc_weeks(data['records'])
    lo=next(x for x in w if x['low']==50)
    hi=next(x for x in w if x['high']==200)
    proposed={'cycle_low':lo['low'],'cl_date':lo['low_date'],'cl_status':'PROPUESTO',
       'waves':{'o1':{'price':hi['high'],'date':hi['high_date'],'status':'PROPUESTO'}}}
    blocked=resolve_long_term_buy('BTC',proposed,data)
    assert blocked['eligible'] is True and blocked['status']=='PROPUESTO_SIMULACION'
    assert blocked['anchors']['low']['status']=='PROPUESTO'
    proposed['cl_status']='VALIDADO'
    assert resolve_long_term_buy('BTC',proposed,data)['eligible'] is True
    proposed['cl_status']='CONFIRMADO'
    yes=resolve_long_term_buy('BTC',proposed,data)
    assert yes['eligible'] and yes['simulation_only']
    assert yes['anchors']['low']['price']==50
    assert yes['anchors']['high']['price']==200
    assert yes['levels']['c1']==125
    no_low=resolve_long_term_buy('BTC',{},data)
    assert not no_low['eligible'] and no_low['levels'] is None


def test_archive_proposes_p1_without_certifying():
    data=daily_payload();w=full_utc_weeks(data['records'])
    lo=next(x for x in w if x['low']==50);hi=next(x for x in w if x['high']==200)
    archive={'cycle_low':lo['low'],'cl_date':lo['low_date'],
             'o1':hi['high'],'o1_date':hi['high_date']}
    result=resolve_long_term_buy('BTC',{},data,archive)
    assert result['eligible'] and result['anchors']['low']['status']=='PROPUESTO'
    assert result['operational_blocked']
