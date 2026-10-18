"""Exploratory 12-token CH/CL/O1..O5 candidates. NEVER certified; never use for live orders.

Other 11 assets: Binance MCP H4 weekly 5L/5R plus weekly close BOS candidates.
HYPE: Hyperliquid HYPE/USDC closed 1D -> complete Mon-Sun UTC weeks, 5L/5R.
"""
from datetime import datetime
from hype_weekly import aggregate_weeks
from structural_outliers import virtual_flash_cl


def _val(p):
    try:return float(p['price']) if isinstance(p,dict) else None
    except (ValueError,TypeError,KeyError):return None

def _date(p):
    if not isinstance(p,dict):return None
    return str(p.get('date_utc',''))[:10] or None

def candidates_binance(token, data, *, selected_low=None):
    if data.get('status')!='OK' or data.get('scope')!='EXPLORATORY_ONLY':
        return {'token':token,'status':'DATA_ERROR','warning':'MCP no devolvió candidato exploratorio válido'}
    ch=data.get('cycle_high');cl=data.get('cycle_low');wp=data.get('wave_pivots') or {}
    raw=_val(cl);value=raw;warnings=[]
    if token=='SUI' and raw is not None and abs(raw-.5597)<.00001:
        value=float(selected_low) if selected_low is not None else None
        warnings.append('CL bruto 0.5597 es OUTLIER; usar exclusivamente SUI_CL_SELECTED aprobado del Master')
    if token=='PUMPFUN' and raw is not None and abs(raw-.000411)<.00000001:
        value=float(selected_low) if selected_low is not None else None
        warnings.append('CL bruto 0.000411 pertenece a semana excluida; usar únicamente PUMP_CL_CANDIDATE del Master, aún no certificado')
    virtual_excluded=(token=='VIRTUAL' and virtual_flash_cl(raw,_date(cl)))
    if virtual_excluded:
        value=None
        warnings.append('VIRTUAL: CL bruto del flash crash 06–12/10/2025 excluido; proponer nuevo CL desde 1W cerrado, no se certifica automáticamente')
    def wave(key):return _val(wp.get(key))
    selected_override=token in ('SUI','PUMPFUN') and raw is not None and value!=raw
    result={'token':token,'market':('PUMP' if token=='PUMPFUN' else token)+'/USDT',
            'source':'Binance Spot MCP H4','status':'CANDIDATO_NO_CERTIFICADO',
            'cycle_high':_val(ch),'ch_date':_date(ch),
            'cycle_low':value,'cl_date':None if selected_override or virtual_excluded else _date(cl),'raw_cycle_low':raw,
            'o1':wave('SH1'),'o1_date':_date(wp.get('SH1')),
            'o2':wave('SL1'),'o2_date':_date(wp.get('SL1')),
            'o3':wave('SH2'),'o3_date':_date(wp.get('SH2')),
            'o4':None,'o5':None,'phase_candidate':data.get('phase'),
            'warning':'; '.join(warnings or ['CL provisional; pivotes semanales candidatos sin certificación humana']),
            'method':'5L/5R + BOS semanal; NO_C1C2_CERTIFICADO'}
    return result


def candidates_hype(data, *, left=5, right=5):
    weeks=aggregate_weeks(data)['weeks']
    # Weekly 5L/5R strict extrema from complete UTC Mon-Sun weeks. BOS is not inferred.
    if type(left)!=int or type(right)!=int or not(3<=left<=12 and 3<=right<=12):
        raise ValueError('Radio de pivotes no aprobado')
    highs=[];lows=[]
    for i in range(left,len(weeks)-right):
        curr=weeks[i];window=weeks[i-left:i]+weeks[i+1:i+1+right]
        if all(curr['high']>w['high'] for w in window):highs.append(curr)
        if all(curr['low']<w['low'] for w in window):lows.append(curr)
    def dt(w):return w['week_open_utc'][:10]
    def first_or_none(xs):return xs[0] if xs else None
    # Structural anchors chosen from distinct chronological pivots, not arbitrary price levels.
    candidates=[w for w in highs if w['week_open_utc']>='2025-09-01']
    ch=first_or_none(candidates)
    cl=first_or_none([w for w in lows if ch and dt(w)>dt(ch)])
    o1=first_or_none([w for w in highs if cl and dt(w)>dt(cl)])
    o2=first_or_none([w for w in lows if o1 and dt(w)>dt(o1)])
    o3=first_or_none([w for w in highs if o2 and dt(w)>dt(o2)])
    # If 5R incomplete, record raw post-O2 high as candidate only; not an O3 pivot.
    remaining=[w for w in weeks if o2 and dt(w)>dt(o2)]
    raw_o3=max(remaining,key=lambda w:w['high']) if remaining else None
    return {'token':'HYPE','market':'HYPE/USDC','source':'Hyperliquid Spot MCP 1D -> semanas UTC',
            'status':'CANDIDATO_NO_CERTIFICADO',
            'cycle_high':ch['high'] if ch else None,'ch_date':dt(ch) if ch else None,
            'cycle_low':cl['low'] if cl else None,'cl_date':dt(cl) if cl else None,
            'o1':o1['high'] if o1 else None,'o1_date':dt(o1) if o1 else None,
            'o2':o2['low'] if o2 else None,'o2_date':dt(o2) if o2 else None,
            'o3':o3['high'] if o3 else None,'o3_date':dt(o3) if o3 else None,
            'o3_unconfirmed_high':raw_o3['high'] if raw_o3 else None,
            'o3_unconfirmed_date':dt(raw_o3) if raw_o3 else None,
            'o4':None,'o5':None, 'full_weeks':len(weeks),
            'method':'5L/5R, semanas UTC completas; BOS y Elliott pendientes',
            'warning':'Los extremos 5L/5R requieren BOS semanal y aprobación humana. O3 sin 5R = máximo observado, NO pivote O3.'}


def add_uncertified_daily_extrema(candidate, ohlcv):
    """Legacy UI function: ONLY fully closed weekly O1 observed after dated CL.

    No daily-extrema pivot detection and no 5L/5R/BOS auto-certification.
    """
    from wave_structure import full_utc_weeks, weekly_o1_candidate, WaveStructureError
    result=dict(candidate)
    if not isinstance(ohlcv,dict) or ohlcv.get('status')!='OK' or ohlcv.get('closed_only') is not True:
        return result
    if result.get('o1') is not None:return result
    if not(result.get('cl_date') and result.get('cycle_low')):
        result['warning']=(str(result.get('warning') or '')+'; CL sin fecha/precio semanal válido').strip('; ')
        return result
    try:
        weeks=full_utc_weeks(ohlcv.get('records') or [])
        picked=weekly_o1_candidate(weeks,result['cycle_low'],result['cl_date'])
        if picked.get('price') is None:return result
    except WaveStructureError:
        return result
    result.update(o1=picked['price'],o1_date=picked['date'],
                  o1_preliminary_week_utc=picked['week_start'],
                  o1_preliminary_method='CLOSED_UTC_WEEK_AFTER_CL',
                  o1_pivot_5l5r=picked['pivot_5l5r'],o1_certified=False)
    result['warning']=(str(result.get('warning') or '')+
        '; O1 candidato semanal, requiere 5L/5R, BOS y certificación humana; NO operativo').strip('; ')
    return result
