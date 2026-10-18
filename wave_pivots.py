"""Per-wave candidate/confirmed state for 07_PIVOTES; no automatic certification.

07_PIVOTES has its 12 live rows in A4:Z16. Wave prices remain in
D/F/H/I/J; O1/O2 dates in E/G. New S:W are five per-wave statuses,
X:Z hold O3/O4/O5 dates. Existing historic archive rows 19+ are untouched. AA stores the independent CL review status.
"""
from __future__ import annotations
from datetime import date
import math

WAVES = ('o1','o2','o3','o4','o5')
PRICE_COLS = {'o1':3,'o2':5,'o3':7,'o4':8,'o5':9}
DATE_COLS = {'o1':4,'o2':6,'o3':23,'o4':24,'o5':25}
STATE_COLS = {wave:18+i for i,wave in enumerate(WAVES)}
HEADERS = {18:'O1 estado',19:'O2 estado',20:'O3 estado',21:'O4 estado',22:'O5 estado',
           23:'O3 fecha UTC',24:'O4 fecha UTC',25:'O5 fecha UTC',26:'CL estado validación 1W'}
CL_STATUS_COL = 26
CL_STATES = ('CANDIDATO','VALIDADO_TECNICAMENTE','CONFIRMADO')

class WavePivotError(ValueError):
    pass


def cell(row,col):
    return row[col] if len(row)>col and row[col] not in ('',None) else None


def date_iso(value):
    if value is None or str(value).strip()=='':return None
    text=str(value).strip()
    try:
        if date.fromisoformat(text).isoformat()!=text:raise ValueError()
    except (ValueError,TypeError) as exc:
        raise WavePivotError('Fecha del pivote debe ser YYYY-MM-DD (UTC)') from exc
    return text


def wave_row(row):
    output={'cycle_low':cell(row,1),'cl_date':cell(row,2),'waves':{}}
    cl_status=str(cell(row,CL_STATUS_COL) or 'CANDIDATO').strip().upper()
    if cl_status not in CL_STATES:raise WavePivotError(f'{row[0]} CL: estado no permitido')
    if cl_status!='CANDIDATO' and (cell(row,1) is None or date_iso(cell(row,2)) is None):
        raise WavePivotError(f'{row[0]} CL: validación requiere precio y fecha')
    output['cl_status']=cl_status
    for wave in WAVES:
        status=str(cell(row,STATE_COLS[wave]) or 'ESTIMADO').strip().upper()
        if status not in ('ESTIMADO','CONFIRMADO'):
            raise WavePivotError(f'{row[0]} {wave.upper()}: estado no permitido')
        price=cell(row,PRICE_COLS[wave]); when=date_iso(cell(row,DATE_COLS[wave]))
        if price is not None:
            if isinstance(price,bool) or not isinstance(price,(float,int)) or not math.isfinite(float(price)) or price<=0:
                raise WavePivotError(f'{row[0]} {wave.upper()}: precio positivo obligatorio')
        if status=='CONFIRMADO' and (price is None or not when):
            raise WavePivotError(f'{row[0]} {wave.upper()}: confirmado sin precio y fecha')
        output['waves'][wave]={'price':price,'date':when,'status':status}
    return output


def fib_from_anchors(low,high):
    """Derived ONLY in direction CL->O1. No inverse Fibonacci reconstruction."""
    from wave_structure import fib_grid, WaveStructureError
    try:
        prices=fib_grid('O2',{'CL':low,'O1':high})
    except WaveStructureError:
        return None
    return {'ref382':prices['O2C1'],'c1':prices['O2C2'],
            'c2':prices['O2C3'],'ref786':prices['O2C4']}

def locked_values(pivots):
    return {w:details['price'] for w,details in pivots['waves'].items() if details['status']=='CONFIRMADO'}
