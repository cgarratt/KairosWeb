from datetime import date,timedelta
from buy_weekly_policy import select_buy_impulse
from wave_structure import full_utc_weeks

def make_weeks(*, final_low=False, bos=True):
    first=date(2025,1,6);records=[]
    for i in range(45):
        h={6:150,29:170,32:200}.get(i,110)
        l={20:50,39:40}.get(i,90) if final_low else {20:50}.get(i,90)
        close=160 if i==29 and bos else (105 if i==29 else 100)
        close=min(h,max(l,close))
        for j in range(7):
            d=first+timedelta(weeks=i,days=j)
            records.append({'open_utc':d.isoformat()+'T00:00:00+00:00',
                'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
                'high':h if j==0 else max(105,close),
                'low':l if j==2 else 95,
                'close':close if j==6 else 100})
    return full_utc_weeks(records)

def test_latest_upward_two_pivots_and_o2_default():
    weeks=make_weeks();demo=select_buy_impulse(weeks)
    assert demo['eligible'] is False  # no published VALIDADO/CONFIRMADO pivots
    low,high=demo['anchors']['low'],demo['anchors']['high']
    ctx=select_buy_impulse(weeks,{'cycle_low':low['price'],'cl_date':low['date'],'cl_status':'VALIDADO',
        'waves':{'o1':{'price':high['price'],'date':high['date'],'status':'CONFIRMADO'}}})
    assert ctx['eligible'] is True
    assert ctx['mode']=='O2'
    assert ctx['anchors']['low']['price']==50
    assert ctx['anchors']['high']['price']==200
    assert ctx['levels']['c1']==125
    assert ctx['bos']['bos_week']==weeks[29]['week_start']

def test_o2_o4_named_only_when_both_anchors_match():
    draft=select_buy_impulse(make_weeks())
    pair=draft['anchors'];low=pair['low'];high=pair['high']
    o2=select_buy_impulse(make_weeks(),{'cycle_low':50,'cl_date':low['date'],'cl_status':'VALIDADO',
        'waves':{'o1':{'price':200,'date':high['date'],'status':'CONFIRMADO'}}})
    assert o2['mode']=='O2'
    o4=select_buy_impulse(make_weeks(),{'waves':{'o2':{'price':50,'date':low['date'],'status':'VALIDADO'},
        'o3':{'price':200,'date':high['date'],'status':'VALIDADO'}}})
    assert o4['mode']=='O4'

def test_blocks_without_bos_or_upward_last_two():
    assert select_buy_impulse(make_weeks(bos=False))['eligible'] is False
    assert select_buy_impulse(make_weeks(final_low=True))['reason']=='ULTIMOS_PIVOTES_NO_ALCISTAS'
    assert select_buy_impulse(make_weeks()[:10])['eligible'] is False

def test_confirmed_pivot_never_overwritten():
    ctx=select_buy_impulse(make_weeks());high=ctx['anchors']['high'];
    tampered={'waves':{'o1':{'status':'CONFIRMADO','date':high['date'],'price':199}}}
    assert select_buy_impulse(make_weeks(),tampered)['reason']=='ANCLA_CONFIRMADA_EN_CONFLICTO'
