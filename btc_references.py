"""BTC price references with separate provenance, units and observation times."""
import math
from datetime import datetime, timezone
from balancer_daily import analyze, weekly_series

def positive(value):
    try:
        return not isinstance(value,bool) and math.isfinite(float(value)) and float(value)>0
    except (ValueError,TypeError,OverflowError):return False

def ema(closes,period):
    if len(closes)<period or not all(positive(v) for v in closes):return None
    values=list(map(float,closes));value=sum(values[:period])/period
    alpha=2/(period+1)
    for price in values[period:]:value+=alpha*(price-value)
    return value

def reference_context(snapshot=None,interval='1d',spot=None,spot_utc=None,onchain=None,now=None):
    now=now or datetime.now(timezone.utc)
    result=dict(interval=interval,spot=None,spot_utc=spot_utc,spot_source=None,rows=[],
                fx=None,fx_cut_utc=None,sth_cut_utc=None,ema_cut_utc=None,ema_source=None)
    snapshot=snapshot or {};onchain=onchain or {}
    try:
        at=datetime.fromisoformat(spot_utc.replace('Z','+00:00'))
        if at.tzinfo and -30<=(now-at).total_seconds()<=180 and positive(spot):
            result['spot']=float(spot)
            result['spot_source']=(snapshot.get('spot') or {}).get('source')
    except (TypeError,ValueError,AttributeError):pass
    series=(snapshot.get('histories') or {}).get('BTCUSDT:1d')
    if interval=='1w':series=weekly_series(series,now) if series else None
    valid=bool(series) and analyze(series,'BTCUSDT',now,interval,validate_only=True)['status']=='OK'
    if valid:
        result.update(ema_cut_utc=series['records'][-1]['close_utc'],ema_source=series['source'])
    fx=(onchain.get('fx') or {})
    if valid_metric(fx,now):result.update(fx=float(fx['value']),fx_cut_utc=fx['point_utc'])
    sth=(onchain.get('sth') or {});sth_ok=valid_metric(sth,now)
    if sth.get('point_utc'):result['sth_cut_utc']=sth['point_utc']
    def add(label,value,currency,color,cut=None,reason='',comparable=True):
        delta=None
        if positive(value) and result['spot'] is not None and comparable:
            comparable_spot=result['spot']*(result['fx'] if currency=='USD' and result['fx'] else 1.)
            delta=100*(comparable_spot-float(value))/float(value)
        width=min(50.,abs(delta)*8) if delta is not None else 0.
        result['rows'].append(dict(label=label,value=float(value) if positive(value) else None,currency=currency,
                                  delta=delta,color=color,cut_utc=cut,reason=reason,
                                  left=50-width if delta is not None and delta<0 else 50.,width=width,
                                  overflow=delta is not None and abs(delta)>6.25))
    add('STH',sth.get('value') if sth_ok else None,'USD','sth',sth.get('point_utc'),
        reason=('Conversión USDT/USD pendiente: distancia N/D.' if sth_ok and not result['fx'] else sth.get('reason','Actualizar STH desde Glassnode.') if not sth_ok else ''),
        comparable=sth_ok and result['fx'] is not None)
    for period in (20,50):
        value=ema([r['close'] for r in series['records']],period) if valid else None
        add('EMA'+str(period),value,'USDT','ema'+str(period),result['ema_cut_utc'],
            reason='' if value is not None else 'Históricos cerrados insuficientes o no vigentes.')
    return result

def valid_metric(point,now):
    try:
        at=datetime.fromisoformat(point['point_utc'].replace('Z','+00:00'))
        age=(now-at).total_seconds()
        return point.get('status')=='OK' and at.tzinfo is not None and 86400<=age<=3*86400 and positive(point['value'])
    except (ValueError,KeyError,TypeError,AttributeError):return False
