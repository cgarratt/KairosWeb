"""Kairos shared pure structural-wave/Fibonacci contract for Web and GPT.

NO I/O; never certifies Elliot pivots or places orders. Structural OHLC is
closed UTC Mon-Sun weeks. Daily OHLC can ONLY verify a retracement after a
previously selected weekly O1 date, not select/confirm structural pivots.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from math import isfinite

BUY_RATIOS=(.382,.5,.618,.786)
SELL_RATIOS=(1.618,2.618,3.618,4.618)
WAVE_REQUIREMENTS={"O2":("CL","O1"),"O3":("CL","O1","O2"),
                   "O4":("O2","O3"),"O5":("O2","O3","O4")}

class WaveStructureError(ValueError): pass

def positive(v, label):
    try: n=float(v)
    except (TypeError,ValueError) as exc:raise WaveStructureError(f"{label}: missing numeric anchor") from exc
    if not isfinite(n) or n<=0:raise WaveStructureError(f"{label}: invalid anchor")
    return n

def iso_date(value,label):
    try:return date.fromisoformat(str(value)[:10])
    except (ValueError,TypeError) as exc:raise WaveStructureError(f"{label}: YYYY-MM-DD UTC required") from exc

def fib_grid(wave, anchors):
    """Prices ONLY from forward chronological anchors, NEVER invert legacy C1/C2.

    For O2: O1-r*(O1-CL); O3: O2+r*(O1-CL);
    O4: O3-r*(O3-O2); O5: O4+r*(O3-O2).
    Anchors must originate upstream from weekly Spot structures and carry
    provenance in caller output; pure arithmetic cannot itself certify source.
    """
    wave=wave.upper()
    if wave not in WAVE_REQUIREMENTS:raise WaveStructureError("Unsupported wave")
    a={name:positive(anchors.get(name),name) for name in WAVE_REQUIREMENTS[wave]}
    if wave in ("O2","O3"):
        if a["O1"]<=a["CL"]:raise WaveStructureError("O1 must exceed CL")
        if wave=="O3" and not a["CL"]<a["O2"]<a["O1"]:
            raise WaveStructureError("O3 requires CL < O2 < O1")
        rise=a["O1"]-a["CL"]
        out=[a["O1"]-r*rise for r in BUY_RATIOS] if wave=="O2" else [a["O2"]+r*rise for r in SELL_RATIOS]
    else:
        if a["O3"]<=a["O2"]:raise WaveStructureError("O3 must exceed O2")
        if wave=="O5" and not a["O2"]<a["O4"]<a["O3"]:
            raise WaveStructureError("O5 requires O2 < O4 < O3")
        rise=a["O3"]-a["O2"]
        out=[a["O3"]-r*rise for r in BUY_RATIOS] if wave=="O4" else [a["O4"]+r*rise for r in SELL_RATIOS]
    if any(x<=0 for x in out):raise WaveStructureError(f"{wave}: nonpositive hypothetical level")
    return dict(zip((f"{wave}{'C' if wave in ('O2','O4') else 'V'}{i}" for i in range(1,5)),out))

def full_utc_weeks(daily_records):
    """Aggregate only all-seven-day, fully CLOSED UTC Mon-Sun weeks.

    HYPE records must be HYPE/USDC Hyperliquid Spot, Binance others Binance
    Spot; callers validate the source before passing records here.
    """
    groups={}
    for r in daily_records or []:
        try:
            day=iso_date(r['open_utc'],'daily open')
            if 'close_utc' not in r:continue
            ending=datetime.fromisoformat(str(r['close_utc']).replace('Z','+00:00'))
            starting=datetime.fromisoformat(str(r['open_utc']).replace('Z','+00:00'))
            if (ending-starting)!=timedelta(days=1) or starting.utcoffset()!=timedelta(0):continue
            if starting.hour or starting.minute or starting.second:continue
            h=positive(r['high'],'high');l=positive(r['low'],'low');c=positive(r['close'],'close')
            if not l<=c<=h:continue
            monday=day-timedelta(days=day.weekday())
            g=groups.setdefault(monday,{})
            if day in g:raise WaveStructureError('Duplicate UTC day')
            g[day]={'high':h,'low':l,'close':c}
        except WaveStructureError:
            raise
        except (KeyError,TypeError,ValueError):continue
    out=[]
    for monday,g in sorted(groups.items()):
        expected={monday+timedelta(days=i) for i in range(7)}
        if set(g)!=expected:continue
        vals=list(g.values()); high_day=max(g,key=lambda d:g[d]['high']);low_day=min(g,key=lambda d:g[d]['low'])
        out.append({'week_start':monday.isoformat(),'week_end':(monday+timedelta(days=6)).isoformat(),
                    'high':max(v['high'] for v in vals),'low':min(v['low'] for v in vals),
                    'close':g[monday+timedelta(days=6)]['close'],
                    'high_date':high_day.isoformat(),'low_date':low_day.isoformat()})
    return out

def weekly_o1_candidate(weeks, cl_price, cl_date, *, published_o1=None, left=5,right=5):
    """Never choose a daily similar-price high or an incomplete weekly candle.

    A candidate in recent full weeks can be PROVISIONAL_PENDING_5R_BOS;
    five-left/five-right local maxima still require weekly BOS + human approval.
    Published confirmed pivots remain immutable at caller policy level.
    """
    cl=positive(cl_price,'CL'); start=iso_date(cl_date,'CL date')
    if published_o1 and published_o1.get('status')=='CONFIRMADO':
        val=positive(published_o1.get('price'),'confirmed O1');dt=iso_date(published_o1.get('date'),'O1 date')
        if dt<=start or val<=cl:raise WaveStructureError('Confirmed O1 invalid relative to CL')
        return {'price':val,'date':dt.isoformat(),'status':'CONFIRMADO','source':'07_PIVOTES_PUBLICADO',
                'week_start':(dt-timedelta(days=dt.weekday())).isoformat(),'pivot_5l5r':False,
                'bos_certified_by_mcp':False}
    # A previously reviewed and dated estimated O1 is preferred to a new
    # automatic weekly candidate; never overwrite manually maintained anchors.
    if published_o1 and published_o1.get('price') and published_o1.get('date'):
        val=positive(published_o1['price'],'estimated O1');dt=iso_date(published_o1['date'],'O1 date')
        if dt<=start or val<=cl:raise WaveStructureError('Estimated O1 invalid relative to CL')
        return {'price':val,'date':dt.isoformat(),'status':('VALIDADO' if published_o1.get('status') in ('VALIDADO','VALIDADO_TECNICAMENTE') else 'PROPUESTO'),'source':'07_PIVOTES_PUBLICADO',
                'week_start':(dt-timedelta(days=dt.weekday())).isoformat(),'pivot_5l5r':False,
                'bos_certified_by_mcp':False}
    eligible=[(i,w) for i,w in enumerate(weeks) if iso_date(w['week_start'],'week')>start and w['high']>cl]
    if not eligible:return {'status':'NO_WEEKLY_O1','source':'CLOSED_UTC_WEEKS'}
    # A recently observed maximum, not a claim that the entire post-CL rally
    # has a 5L/5R verified Elliott O1. Include last 5 FULL weeks by policy.
    window=eligible[-max(left,1):]
    index,w=max(window,key=lambda v:(v[1]['high'],v[0]))
    pivot=(index>=left and index+right<len(weeks) and
           all(w['high']>x['high'] for x in weeks[index-left:index]+weeks[index+1:index+right+1]))
    return {'price':w['high'],'date':w['high_date'],'week_start':w['week_start'],
            'status':'PROPUESTO','source':'MCP_WEEKLY_CLOSED_CANDIDATE',
            'pivot_5l5r':pivot,'bos_certified_by_mcp':False,
            'review':'BOS and human certification required; never executable'}

def post_o1_daily_low(records, o1_date):
    """Observed low in CLOSED daily candles after the selected O1 high DATE."""
    dt=iso_date(o1_date,'O1 date')
    lows=[]
    for r in records or []:
        try:
            day=iso_date(r['open_utc'],'daily date')
            if day<=dt:continue
            low=positive(r['low'],'low');lows.append((day,low))
        except (KeyError,TypeError,ValueError):continue
    if not lows:return {'status':'NO_POST_O1_DAYS','low':None}
    day,low=min(lows,key=lambda x:x[1]);return {'status':'OBSERVED_POST_O1','low':low,'date':day.isoformat()}

def level_color(level, minimum):
    if level is None or minimum is None:return 'unknown'
    p=positive(level,'level');l=positive(minimum,'minimum')
    return 'hit' if l<=p else 'near' if l<=p*1.01 else 'pending'


def weekly_wave_candidates(weeks, cl_date, *, left=5, right=5):
    """Construct O1..O5 exploratory 1W pivots in chronological swing order.

    5L/5R strict highs/lows on FULL UTC weeks are necessary but NOT enough:
    weekly-close BOS and human Elliott approval are still required separately.
    Never fill an O2/O3/O4/O5 gap using Fibonacci prices or daily highs.
    """
    if not isinstance(left,int) or not isinstance(right,int) or left<1 or right<1:
        raise WaveStructureError('Invalid weekly pivot radius')
    start=iso_date(cl_date,'CL date')
    chosen={}
    last_idx=-1
    for wave,kind in [('O1','high'),('O2','low'),('O3','high'),('O4','low'),('O5','high')]:
        candidates=[]
        for i in range(max(left,last_idx+1),len(weeks)-right):
            curr=weeks[i]
            if iso_date(curr['week_start'],'week')<=start:continue
            r=weeks[i-left:i]+weeks[i+1:i+right+1]
            value=positive(curr[kind],wave)
            if (all(value>x[kind] for x in r) if kind=='high' else all(value<x[kind] for x in r)):
                candidates.append((i,curr))
        if not candidates:break
        i,curr=candidates[0]
        chosen[wave]={'price':curr[kind],'date':curr[f'{kind}_date'],
                      'week_start':curr['week_start'],'status':'PROPUESTO',
                      'pivot_5l5r':True,'bos_status':'PENDIENTE_VALIDACION',
                      'human_certification':False,'source':'MCP_WEEKLY_CLOSED'}
        last_idx=i
    return chosen
