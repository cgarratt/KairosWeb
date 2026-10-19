from datetime import date, timedelta
from buy_weekly_policy import confirmed_p1_buy_impulse
from wave_structure import full_utc_weeks


def market_weeks():
    first=date(2026,1,5);records=[]
    for i in range(20):
        lo=50 if i==3 else 80
        hi={5:120,10:160,15:140,18:180}.get(i,100)
        for j in range(7):
            d=first+timedelta(weeks=i,days=j)
            records.append({'open_utc':d.isoformat()+'T00:00:00+00:00',
                'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
                'high':hi,'low':lo,'close':90})
    return full_utc_weeks(records)


def test_propuesto_validado_confirmado_p1_allowed_for_simulation():
    weeks=market_weeks();low=weeks[3]
    for status in ('PROPUESTO','VALIDADO','CONFIRMADO'):
        result=confirmed_p1_buy_impulse(weeks,{'cycle_low':50,'cl_date':low['low_date'],'cl_status':status})
        assert result['eligible'] and result['simulation_only']
        assert result['anchors']['low']['status']==status
        assert result['anchors']['high']['price']==180
        assert result['status']==('PROPUESTO_SIMULACION' if status=='PROPUESTO' else 'PROPUESTO_SIMULACION')
        assert result['operational_blocked'] is True  # all stages are simulation-only


def test_p2_is_highest_later_closed_week_without_5r_bos():
    weeks=market_weeks();low=weeks[3]
    p={'cycle_low':50,'cl_date':low['low_date'],'cl_status':'CONFIRMADO','waves':{}}
    r=confirmed_p1_buy_impulse(weeks,p)
    assert r['eligible'] and r['simulation_only']
    assert r['anchors']['low']['price']==50
    assert r['anchors']['high']['price']==180
    assert r['anchors']['high']['status']=='PROPUESTO'
    assert r['levels']['c1']==115
    assert r['mode']=='RETROCESO_ALCISTA'


def test_latest_confirmed_low_selected_when_more_than_one():
    weeks=market_weeks(); low1=weeks[3];low2=weeks[12]
    p={'cycle_low':50,'cl_date':low1['low_date'],'cl_status':'CONFIRMADO',
       'waves':{'o2':{'price':80,'date':low2['low_date'],'status':'CONFIRMADO'}}}
    r=confirmed_p1_buy_impulse(weeks,p)
    assert r['eligible'] and r['anchors']['low']['pivot']=='O2'
    assert r['anchors']['high']['price']==180


def test_missing_p2_or_wrong_p1_low_fails():
    weeks=market_weeks()
    p={'cycle_low':49,'cl_date':weeks[3]['low_date'],'cl_status':'CONFIRMADO'}
    assert confirmed_p1_buy_impulse(weeks,p)['reason']=='P1_NO_COINCIDE_MINIMO_SEMANAL'
    p={'cycle_low':50,'cl_date':weeks[-1]['low_date'],'cl_status':'CONFIRMADO'}
    assert confirmed_p1_buy_impulse(weeks,p)['reason']=='P1_NO_COINCIDE_MINIMO_SEMANAL'


def test_p2_confirmed_never_modified_on_conflict():
    weeks=market_weeks()
    p={'cycle_low':50,'cl_date':weeks[3]['low_date'],'cl_status':'CONFIRMADO',
       'waves':{'o1':{'price':120,'date':weeks[18]['high_date'],'status':'CONFIRMADO'}}}
    result=confirmed_p1_buy_impulse(weeks,p)
    assert result['reason']=='P2_CONFLICTO_CON_CONFIRMADO'


def test_missing_p1_nd_blocks_and_archive_is_only_proposed():
    weeks=market_weeks(); low=weeks[3]
    assert confirmed_p1_buy_impulse(weeks,{})['reason']=='P1_ND'
    assert confirmed_p1_buy_impulse(weeks,{'cycle_low':50,'cl_status':'PROPUESTO'})['reason']=='P1_ND'
    archive={'cycle_low':50,'cl_date':low['low_date']}
    result=confirmed_p1_buy_impulse(weeks,{},archive)
    assert result['eligible'] and result['anchors']['low']['status']=='PROPUESTO'
    assert result['anchors']['low']['source']=='MCP_ARCHIVE_PROPUESTO'
    mismatch=confirmed_p1_buy_impulse(weeks,{'cycle_low':51,'cl_date':low['low_date'],'cl_status':'PROPUESTO'},archive)
    assert mismatch['reason']=='P1_NO_COINCIDE_MINIMO_SEMANAL'
