"""Provisional post-O1 daily history. No pivot/fill certification."""
from datetime import datetime
import math

def estimate_post_o1(c1,c2,candles, tolerance=.025):
    try:
        c1,c2=float(c1),float(c2)
        if not (math.isfinite(c1) and math.isfinite(c2) and c1>c2>0):raise ValueError()
        o1=c1+.5*(c1-c2)/.118
    except (TypeError,ValueError,OverflowError):
        return {'status':'NO_REFERENCE','certified':False}
    series=[]
    for candle in candles or []:
        try:
            high=float(candle['high']);low=float(candle['low']);date=str(candle.get('open_utc',''))[:10]
            if not(high>0 and 0<low<=high and date):continue
            series.append((date,high,low))
        except (KeyError,TypeError,ValueError):continue
    series.sort(key=lambda t:t[0])
    # Only accept a dated daily candle with an observed high close to the
    # algebraically reconstructed O1. No suitable match -> no semaphore.
    candidates=[(abs(high/o1-1),-i,i) for i,(_,high,_) in enumerate(series[:-1]) if abs(high/o1-1)<=tolerance]
    if not candidates:return {'status':'UNVERIFIED_O1','estimated_o1':o1,'certified':False}
    _,_,index=min(candidates)
    remainder=series[index+1:]
    date,lowest=min(((date,low) for date,_,low in remainder),key=lambda x:x[1])
    return {'status':'PROVISIONAL','estimated_o1':o1,'estimated_o1_date':series[index][0],
            'post_o1_min':lowest,'post_o1_min_date':date,'certified':False,
            'source':'BINANCE_SPOT_1D_CLOSED','historical_scope':'post_O1_candidate_daily'}

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
