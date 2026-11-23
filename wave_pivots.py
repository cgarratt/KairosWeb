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
PIVOT_STATES = ('PROPUESTO','VALIDADO','CONFIRMADO')
CL_STATES = PIVOT_STATES
LEGACY_STATES = {'CANDIDATO':'PROPUESTO','VALIDADO_TECNICAMENTE':'VALIDADO','ESTIMADO':'PROPUESTO'}

def normalized_status(value):
    status=str(value or 'PROPUESTO').strip().upper()
    return LEGACY_STATES.get(status,status)

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
    output={'cycle_low':cell(row,1),'cl_date':date_iso(cell(row,2)),'waves':{}}
    cl_status=normalized_status(cell(row,CL_STATUS_COL))
    if cl_status not in CL_STATES:raise WavePivotError(f'{row[0]} CL: estado no permitido')
    if cl_status!='PROPUESTO' and (cell(row,1) is None or date_iso(cell(row,2)) is None):
        raise WavePivotError(f'{row[0]} CL: validación requiere precio y fecha')
    output['cl_status']=cl_status
    for wave in WAVES:
        status=normalized_status(cell(row,STATE_COLS[wave]))
        if status not in PIVOT_STATES:
            raise WavePivotError(f'{row[0]} {wave.upper()}: estado no permitido')
        price=cell(row,PRICE_COLS[wave]); when=date_iso(cell(row,DATE_COLS[wave]))
        if price is not None:
            if isinstance(price,bool) or not isinstance(price,(float,int)) or not math.isfinite(float(price)) or price<=0:
                raise WavePivotError(f'{row[0]} {wave.upper()}: precio positivo obligatorio')
        if status in ('VALIDADO','CONFIRMADO') and (price is None or not when):
            raise WavePivotError(f'{row[0]} {wave.upper()}: confirmado sin precio y fecha')
        output['waves'][wave]={'price':price,'date':when,'status':status}
    from pivot_timeline import timeline_issues
    output['timeline_issues']=timeline_issues(output)
    output['timeline_valid']=not output['timeline_issues']
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


def _observed_utc(value):
    from datetime import datetime, timezone

    instant = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if instant.tzinfo is None:
        raise ValueError('Fecha sin zona horaria')
    return instant.astimezone(timezone.utc)


def _valid_price(price):
    return type(price) in (int, float) and math.isfinite(price) and price > 0


def weekly_reference_points(record, archived):
    """Select dated MASTER references. The former O1 can precede the new cycle."""
    if not record:
        return []
    if not record['timeline_valid']:
        raise WavePivotError('Cronología semanal inválida en el MASTER.')
    cycle_low = {'price': record['cycle_low'], 'date': record['cl_date'], 'status': record['cl_status']}
    points = [dict(pivot, name=name.upper(), source='07_PIVOTES')
              for name, pivot in (('cl', cycle_low), *record['waves'].items())
              if pivot['status'] in PIVOT_STATES and pivot['date'] and _valid_price(pivot['price'])]
    points = sorted(points, key=lambda pivot: pivot['date'])[-2:]
    if len(points) == 1 and points[0]['name'] == 'CL' and archived:
        old_price = archived.get('o1')
        try:
            old_date = date_iso(archived.get('o1_date'))
        except WavePivotError:
            old_date = None
        if (old_date and old_date < points[0]['date'] and _valid_price(old_price)
                and old_price > points[0]['price']):
            points.insert(0, {'name': 'O1 anterior', 'price': old_price, 'date': old_date,
                              'status': 'PROPUESTO · ARCHIVADO',
                              'source': '07_PIVOTES · Archivo · ' + archived['market']})
    return points


def closed_days_after(history, anchor_day, today, source, token):
    """Validate exact UTC coverage from the day after the last dated pivot."""
    from datetime import time, timedelta

    first = date.fromisoformat(anchor_day) + timedelta(days=1)
    if first >= today:
        return []
    if (history.get('status') != 'OK' or history.get('source') != source
            or history.get('interval') != '1d' or history.get('closed_only') is not True):
        raise ValueError('Serie diaria incompatible')
    if token == 'HYPE':
        if history.get('pair') != 'HYPE/USDC':
            raise ValueError('Par histórico incompatible')
    elif history.get('symbol') != token + 'USDT':
        raise ValueError('Par histórico incompatible')

    days = []
    expected = first
    for bar in history['records']:
        opening = _observed_utc(bar['open_utc'])
        if opening.date() < first:
            continue
        closing = _observed_utc(bar['close_utc'])
        if (opening.date() != expected or opening.time() != time.min
                or closing != opening + timedelta(days=1) or closing.date() > today
                or bar.get('source', source) != source):
            raise ValueError('Serie diaria incompleta o discontinua')
        values = [bar[key] for key in ('open', 'high', 'low', 'close')]
        if any(isinstance(value, bool) for value in values):
            raise ValueError('Extremos diarios inválidos')
        open_price, high, low, close_price = map(float, values)
        if (not all(_valid_price(value) for value in (open_price, high, low, close_price))
                or not low <= min(open_price, close_price) <= max(open_price, close_price) <= high):
            raise ValueError('Extremos diarios inválidos')
        days.append({'date': expected.isoformat(), 'low': low, 'high': high})
        expected += timedelta(days=1)
    if expected != today:
        raise ValueError('Faltan cierres diarios desde el pivote')
    return days


def weekly_retracement(points, days, spot, observed, token, source):
    """Build read-only two-point retracements and directional extensions."""
    from wave_structure import BUY_RATIOS, SELL_RATIOS

    result = {'pivots': points, 'levels': [], 'extensions': [], 'breakout': None,
              'currency': 'USDC' if token == 'HYPE' else 'USDT'}
    if len(points) < 2:
        result['issue'] = 'Se requieren dos referencias semanales con precio y fecha UTC.'
        return result
    start, end = points
    low, high = sorted((start, end), key=lambda pivot: pivot['price'])
    if low['price'] == high['price']:
        result['issue'] = 'Las dos referencias tienen el mismo precio.'
        return result

    peaks = {}
    last_side = None
    for day in days or []:
        below = day['low'] < low['price']
        above = day['high'] > high['price']
        if below and ('low' not in peaks or day['low'] < peaks['low']['price']):
            peaks['low'] = {'price': day['low'], 'date': day['date']}
        if above and ('high' not in peaks or day['high'] > peaks['high']['price']):
            peaks['high'] = {'price': day['high'], 'date': day['date']}
        if below or above:
            last_side = 'both' if below and above else 'low' if below else 'high'
    if _valid_price(spot) and observed:
        spot_day = _observed_utc(observed).date().isoformat()
        if spot_day > end['date'] and (not days or spot_day > days[-1]['date']):
            side = 'low' if spot < low['price'] else 'high' if spot > high['price'] else None
            if side:
                last_side = side
                if side not in peaks or (spot < peaks[side]['price'] if side == 'low' else spot > peaks[side]['price']):
                    peaks[side] = {'price': spot, 'date': observed, 'from_spot': True}
    if last_side == 'both':
        result['issue'] = 'Una misma vela diaria rompió ambos extremos. El orden de la ruptura es indeterminado.'
        return result
    if last_side:
        start = low if last_side == 'high' else high
        extreme = peaks[last_side]
        end = dict(extreme, name='Máximo observado' if last_side == 'high' else 'Mínimo observado',
                   source=source, status='PROVISIONAL')
        result['breakout'] = end

    def levels(ratios, origin, displacement):
        output = []
        for ratio in ratios:
            value = origin + ratio * displacement
            output.append({'percent': ratio * 100, 'price': value if _valid_price(value) else None})
        return output

    distance = end['price'] - start['price']
    result.update(start=start, end=end, levels=levels(BUY_RATIOS, end['price'], -distance),
                  extensions=levels(SELL_RATIOS, start['price'], distance))
    return result
