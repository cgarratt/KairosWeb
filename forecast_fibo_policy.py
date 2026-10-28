"""Fibonacci Forecast stage budgets, four individual percentage cells per wave.

The 16 numeric keys override any obsolete serialized 4-item string; legacy
strings remain read-only compatibility references, never a second budget.
No simulation result constitutes an executable order.
"""
from math import isfinite

LEVELS_BUY=(.382,.5,.618,.786)
LEVELS_SELL=(1.618,2.618,3.618,4.618)
STAGE_KEYS={
    'o2':'FORECAST_O2_FIB_ALLOCATION',
    'o3':'FORECAST_O3_FIB_ALLOCATION',
    'o4':'FORECAST_O4_FIB_ALLOCATION',
    'o5':'FORECAST_O5_FIB_ALLOCATION',
}
TRANCHES={
  'o2':(('382','38.2%'),('500','50%'),('618','61.8%'),('786','78.6%')),
  'o3':(('1618','1.618'),('2618','2.618'),('3618','3.618'),('4618','4.618')),
  'o4':(('382','38.2%'),('500','50%'),('618','61.8%'),('786','78.6%')),
  'o5':(('1618','1.618'),('2618','2.618'),('3618','3.618'),('4618','4.618')),
}
TRANCHE_KEYS={s:tuple(f'FORECAST_{s.upper()}_FIB_{suffix}_PCT' for suffix,_ in v) for s,v in TRANCHES.items()}
ALL_TRANCHE_KEYS=frozenset(k for group in TRANCHE_KEYS.values() for k in group)
STAGE_FOR_KEY={k:stage for stage,keys in TRANCHE_KEYS.items() for k in keys}
DEFAULTS={'o2':(0,60,40,0),'o3':(20,20,30,30),'o4':(0,60,40,0),'o5':(20,20,30,30)}

class ForecastAllocationError(ValueError):pass

def validate_weights(values):
    if not isinstance(values,(list,tuple)) or len(values)!=4:
        raise ForecastAllocationError('Cuatro asignaciones Fibonacci obligatorias')
    if any(type(v) not in (int,float) or not isfinite(v) or v<0 or v>100 for v in values):
        raise ForecastAllocationError('Cada tramo debe estar entre 0% y 100%')
    if abs(sum(values)-100)>1e-7:
        raise ForecastAllocationError('Los cuatro tramos deben sumar exactamente 100%')
    return tuple(float(v) for v in values)

def parse_weights(value):
    if not isinstance(value,str):raise ForecastAllocationError('Los tramos deben ser porcentajes separados por comas')
    try:parts=tuple(float(s.strip()) for s in value.split(','))
    except ValueError as e:raise ForecastAllocationError('Porcentaje incorrecto') from e
    return validate_weights(parts)

def stringify_weights(weights):
    parts=parse_weights(weights) if isinstance(weights,str) else validate_weights(weights)
    return ','.join(f'{v:g}' for v in parts)

def defaults_from_master(parameters):
    result={}
    for stage,key in STAGE_KEYS.items():
        numeric=TRANCHE_KEYS[stage]
        found=[k in parameters for k in numeric]
        if any(found):
            if not all(found):
                raise ForecastAllocationError(stage.upper()+': hay tramos individuales incompletos en Google Sheets; faltan '+', '.join(k for k in numeric if k not in parameters))
            items=[parameters[k] for k in numeric]
            if any(r.get('status') not in ('APROBADO_SIMULACION','APROBADO') for r in items):
                raise ForecastAllocationError(stage.upper()+': existe un tramo no aprobado: '+', '.join(k+'='+str(r.get('status')) for k,r in zip(numeric,items) if r.get('status') not in ('APROBADO_SIMULACION','APROBADO')))
            try:result[stage]=list(validate_weights([r['value'] for r in items]))
            except (KeyError,TypeError) as e:raise ForecastAllocationError(stage.upper()+': porcentaje inválido') from e
        elif (entry:=parameters.get(key)) and entry.get('status') in ('APROBADO_SIMULACION','APROBADO'):
            result[stage]=list(parse_weights(str(entry.get('value'))))
        elif stage=='o5' and parameters.get('O5_STAGED_TRANCHES',{}).get('status')=='APROBADO':
            result[stage]=list(parse_weights(str(parameters['O5_STAGED_TRANCHES']['value'])))
        else:result[stage]=list(DEFAULTS[stage])
    return result
