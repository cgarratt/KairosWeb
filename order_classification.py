"""Shared Kairos BUY classification. Pure, no balances/orders/Sheet mutation."""
from math import isfinite

def _positive(value):
    if isinstance(value,bool):return None
    try:value=float(value)
    except (TypeError,ValueError):return None
    return value if isfinite(value) and value>0 else None

def classify_buy_order(*, spot=None, target=None, stage_pct=None, state='PROPUESTA'):
    raw=str(state or 'PROPUESTA').strip().upper()
    raw={'FILLED':'EJECUTADA','COMPLETED':'EJECUTADA','OPEN':'CONFIRMADA','NEW':'CONFIRMADA',
         'PENDIENTE':'CONFIRMADA','PENDIENT':'CONFIRMADA','PARTIALLY_FILLED':'PARCIAL',
         'CANCELLED':'CANCELADA','CANCELED':'CANCELADA'}.get(raw,raw)
    spot=_positive(spot);target=_positive(target)
    deviation=100*(spot/target-1) if spot and target else None
    result={'raw_state':raw,'effective_status':raw,'deviation_pct':deviation,
            'indicator':'—','may_allocate':False,'reason':None}
    if raw in ('CONFIRMADA','EJECUTADA','PARCIAL'):
        return dict(result,indicator='🔵',reason='COMPROMISO_O_EJECUCION_REGISTRADA')
    if raw in ('NO_APLICA','CANCELADA'):
        return dict(result,indicator='⚪',reason=raw)
    if raw!='PROPUESTA':return dict(result,effective_status='PENDIENTE_DATOS',reason='ESTADO_DESCONOCIDO')
    if stage_pct is not None:
        if isinstance(stage_pct,bool):return dict(result,effective_status='PENDIENTE_DATOS',reason='ASIGNACION_INVALIDA')
        try:pct=float(stage_pct)
        except (ValueError,TypeError):pct=float('nan')
        if not isfinite(pct) or not 0<=pct<=100:return dict(result,effective_status='PENDIENTE_DATOS',reason='ASIGNACION_INVALIDA')
        if pct==0:return dict(result,effective_status='NO_APLICA',indicator='⚪',reason='ASIGNACION_FIBO_0')
    else:return dict(result,effective_status='PENDIENTE_DATOS',reason='ASIGNACION_NO_VERIFICADA')
    if deviation is None:return dict(result,effective_status='PENDIENTE_DATOS',reason='SPOT_OBJETIVO_NO_VERIFICADO')
    if spot<target:return dict(result,effective_status='NO_APLICA',indicator='⚪',reason='SPOT_MENOR_OBJETIVO')
    return dict(result,indicator='🟢' if deviation>5+1e-10 else '🟡',may_allocate=spot>target,
                reason='OBJETIVO_IGUAL_SPOT' if spot==target else 'PROPUESTA_ELEGIBLE_POR_PRECIO')
