"""Provisional post-O1 daily history. No pivot/fill certification."""
from datetime import datetime
import math

def estimate_post_o1(c1,c2,candles,tolerance=.025, *, fixed_o1_date=None,fixed_o1_price=None):
    """Legacy API fail-closed: old Fib C1/C2 MUST NOT choose an O1 candle.

    Callers must provide a weekly-selected O1 with date AND price. New
    integrations should use wave_structure.post_o1_daily_low instead.
    """
    if not fixed_o1_date or not fixed_o1_price:
        return {'status':'WEEKLY_O1_REQUIRED','certified':False}
    from wave_structure import post_o1_daily_low, WaveStructureError
    try:
        value=float(fixed_o1_price)
        if not math.isfinite(value) or value<=0:raise ValueError()
        history=post_o1_daily_low(candles,fixed_o1_date)
        if history['status']!='OBSERVED_POST_O1':return {'status':history['status'],'certified':False}
        return {'status':'PROVISIONAL','estimated_o1':value,
                'estimated_o1_date':str(fixed_o1_date)[:10],
                'post_o1_min':history['low'],'post_o1_min_date':history['date'],
                'certified':False,'source':'BINANCE_CLOSED_1D_POST_WEEKLY_O1'}
    except (ValueError,TypeError,WaveStructureError):
        return {'status':'INVALID_WEEKLY_O1','certified':False}

def color_state(reference,history):
    if history.get('status')!='PROVISIONAL':return 'unknown'
    low=history.get('post_o1_min')
    if reference is None or low is None:return 'unknown'
    try:
        r=float(reference);l=float(low)
        if r<=0 or l<=0:return 'unknown'
        if l<=r:return 'hit'
        if l<=r*1.01:return 'near'
        return 'pending'
    except (ValueError,TypeError):return 'unknown'
