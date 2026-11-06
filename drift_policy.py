"""Relative composition tolerance; 10% approved for this release by user.
Legacy DRIFT_BAND_PP is never interpreted as a relative percentage.
No writes occur on reads. Save Configuration to persist the new key.
"""
from math import isfinite
KEY='DRIFT_BAND_RELATIVE_PCT'
DEFAULT=10.0

def relative_band(parameters):
    row=parameters.get(KEY)
    if row is None:return DEFAULT
    if row.get('status') not in ('APROBADO','APROBADO_CONDICIONAL'):
        raise ValueError(KEY+': no aprobado')
    value=float(row['value'])
    if not isfinite(value) or not 0<=value<=100:raise ValueError(KEY+': fuera de rango')
    return value

def relative_drift(weight,target):
    if target<=0:return None
    return 100*(weight-target)/target

def classify(weight,target,band=DEFAULT):
    if target==0:return 'SOBRE' if weight>0 else 'NEUTRAL'
    d=relative_drift(weight,target)
    return 'SOBRE' if d>band+1e-9 else 'INFRA' if d < -band-1e-9 else 'NEUTRAL'
