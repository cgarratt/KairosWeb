"""Cross-Kairos weekly-only structure + forward Fibonacci parity."""
from datetime import date,timedelta
import importlib.util
from pathlib import Path
from wave_structure import (full_utc_weeks, weekly_o1_candidate, fib_grid,
                            post_o1_daily_low,level_color,WaveStructureError)
from wave_macro_context import resolve
import pytest

def days(start, weekly_highs, *, partial=0):
    first=date.fromisoformat(start);res=[]
    for idx,hi in enumerate(weekly_highs):
        for i in range(7 if idx<len(weekly_highs)-1 else (partial or 7)):
            d=first+timedelta(days=idx*7+i)
            res.append({'open_utc':d.isoformat()+'T00:00:00+00:00','close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
                        'high':str(hi if i==0 else hi*.9),'low':str(hi*.7),'close':str(hi*.8)})
    return res

def test_structural_excludes_open_week_and_legacy_reverse():
    d=days('2026-09-07',[.012,.014,.018,.02138,.02308,.02419],partial=6)
    weeks=full_utc_weeks(d)
    assert len(weeks)==5
    assert all(w['high']!=.02419 for w in weeks)
    o1=weekly_o1_candidate(weeks,.00836,'2025-10-10')
    assert o1['status']=='PROPUESTO'
    assert o1['price']==.02308
    assert o1['week_start']=='2026-10-05'
    assert o1['pivot_5l5r'] is False
    levels=fib_grid('O2',{'CL':.00836,'O1':o1['price']})
    assert levels['O2C1']==pytest.approx(.01745696)
    assert levels['O2C2']==pytest.approx(.01572)

def test_published_confirmed_o1_locked_and_forward_expansion():
    candidate=weekly_o1_candidate([], .00836,'2025-10-10',published_o1={'status':'CONFIRMADO','price':.02419,'date':'2026-10-12'})
    assert candidate['source']=='07_PIVOTES_PUBLICADO'
    assert candidate['price']==.02419
    o2=fib_grid('O2',{'CL':.00836,'O1':.02419})
    assert o2['O2C1']==pytest.approx(.01814294)
    assert o2['O2C2']==pytest.approx(.016275)
    assert o2['O2C3']==pytest.approx(.01440706)
    assert o2['O2C4']==pytest.approx(.01174762)
    a={'CL':.00836,'O1':.02419,'O2':.016275,'O3':.060,'O4':.04}
    assert fib_grid('O3',a)['O3V1']==pytest.approx(.016275+1.618*(.02419-.00836))
    assert fib_grid('O4',a)['O4C2']==pytest.approx(.060-.5*(.060-.016275))
    assert fib_grid('O5',a)['O5V1']==pytest.approx(.04+1.618*(.060-.016275))

def test_wrong_venue_and_incomplete_are_fail_closed():
    d=days('2026-09-07',[.012,.014,.018,.02138,.02308,.02419],partial=6)
    valid={'status':'OK','source':'Binance Spot','interval':'1d','closed_only':True,'records':d}
    archived={'cycle_low':.00836,'cl_date':'2025-10-10'}
    correct=resolve('PLUME',{},archived,valid)
    assert correct['status']=='ESTIMATED_WEEKLY_CANDIDATE'
    assert correct['anchors']['O1']==.02308
    assert correct['levels']['c1']==pytest.approx(.01572)
    assert resolve('HYPE',{},archived,valid)['status']=='WRONG_HYPE_SOURCE'
    assert resolve('PLUME',{},archived,{**valid,'closed_only':False})['status']=='MCP_DATA_ERROR'
    assert resolve('PLUME',{}, {'cycle_low':.00836},{**valid})['status']=='MISSING_DATED_CL'
    assert post_o1_daily_low(d,'2026-10-05')['status']=='OBSERVED_POST_O1'
    assert level_color(.018,.0181)=='near'

def test_shared_gpt_web_byte_parity():
    web=Path(__file__).resolve().parents[1]/'wave_structure.py'
    gpt=Path('/mnt/data/kairos_unified_gpt_dev/KairosGPT_v1.3.0/kairos_gpt/wave_structure.py')
    if gpt.exists():assert web.read_bytes()==gpt.read_bytes()

def test_all_five_weekly_pivots_require_five_l_and_five_r():
    from wave_structure import weekly_wave_candidates
    start=date(2026,1,5)
    weeks=[]
    for i in range(37):
        mon=start+timedelta(days=7*i)
        high={6:10,18:20,30:30}.get(i,5)
        low={12:1,24:2}.get(i,4)
        weeks.append({'week_start':mon.isoformat(),'high':high,'low':low,
                      'high_date':mon.isoformat(),'low_date':mon.isoformat()})
    result=weekly_wave_candidates(weeks,'2025-12-01')
    assert list(result)==['O1','O2','O3','O4','O5']
    assert [v['price'] for v in result.values()]==[10,1,20,2,30]
    assert all(v['status']=='PROPUESTO' and v['bos_status']=='PENDIENTE_VALIDACION'
               and v['pivot_5l5r'] for v in result.values())
