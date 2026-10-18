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


def test_proposed_pair_can_simulate_without_weekly_bos():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    low=next(w for w in weeks if w['low']==50)
    high=next(w for w in weeks if w['high']==200)
    pub={'cycle_low':low['low'],'cl_date':low['low_date'],'cl_status':'PROPUESTO',
         'waves':{'o1':{'price':high['high'],'date':high['high_date'],'status':'PROPUESTO'}}}
    result=proposed_simulation_impulse(weeks,pub)
    assert result['eligible'] is True
    assert result['status']=='PROPUESTO_SIMULACION'
    assert result['operational_blocked'] is True
    assert result['mode']=='O2'
    assert result['levels']['c1']==125


def test_no_extreme_nd_blocks_simulation():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    assert not proposed_simulation_impulse(weeks,{})['eligible']
    assert proposed_simulation_impulse(weeks,{})['reason']=='EXTREMO_LOW_ND'


def test_archive_proposals_allow_simulated_levels_when_master_nd():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    lo=next(w for w in weeks if w['low']==50)
    hi=next(w for w in weeks if w['high']==200)
    draft=proposed_simulation_impulse(weeks,{},{'cycle_low':lo['low'], 'cl_date':lo['low_date'],
        'o1':hi['high'], 'o1_date':hi['high_date']})
    assert draft['eligible'] and draft['simulation_only'] and draft['operational_blocked']
    assert draft['pivot_authority']['high']['status']=='PROPUESTO'


def test_archived_invalid_or_open_week_cannot_grant_simulation():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    lo=next(w for w in weeks if w['low']==50)
    hi=next(w for w in weeks if w['high']==200)
    bogus=proposed_simulation_impulse(weeks,{},{'cycle_low':lo['low'], 'cl_date':lo['low_date'],
        'o1':hi['high']+1, 'o1_date':hi['high_date']})
    assert not bogus['eligible']
    assert bogus['reason']=='EXTREMO_NO_COINCIDE_CON_1W_CERRADA'


def test_confirmed_mismatch_not_downgraded_to_proposal():
    from buy_weekly_policy import select_buy_impulse, proposed_simulation_impulse
    weeks=make_weeks(); base=select_buy_impulse(weeks)
    hi=base['anchors']['high']; lo=base['anchors']['low']
    published={'cycle_low':lo['price'],'cl_date':lo['date'],'cl_status':'CONFIRMADO',
       'waves':{'o1':{'price':hi['price']+1,'date':hi['date'],'status':'CONFIRMADO'}}}
    assert not proposed_simulation_impulse(weeks,published)['eligible']


def test_existing_cl_uses_latest_closed_week_for_proposed_o1():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    low=next(w for w in weeks if w['low']==50)
    p={'cycle_low':low['low'],'cl_date':low['low_date'],'cl_status':'PROPUESTO'}
    result=proposed_simulation_impulse(weeks,p)
    assert result['eligible'] and result['simulation_only'] and result['operational_blocked']
    assert result['pivot_authority']['high']['status']=='PROPUESTO'
    assert result['anchors']['high']['date'] > result['anchors']['low']['date']


def test_nd_and_unverified_cl_remain_blocked():
    from buy_weekly_policy import proposed_simulation_impulse
    weeks=make_weeks(bos=False)
    assert proposed_simulation_impulse(weeks,{'cycle_low':50})['reason']=='EXTREMO_LOW_ND'
    # A nominal CL outside the covered weekly range cannot be treated as O1 source.
    assert not proposed_simulation_impulse(weeks,{}, {'cycle_low':51,'cl_date':'2023-02-01'})['eligible']
