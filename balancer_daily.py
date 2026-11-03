"""Read-only daily context. Never changes allocations, orders or the MASTER."""
import math
from datetime import datetime, timezone, timedelta


def recommendation(rsi, ma, k, d):
    values = (rsi, ma, k, d)
    if not all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 100 for x in values):
        return 'N/D'
    if rsi < 30 and rsi > ma and k > d:
        return 'COMPRAR'
    if rsi > 70 and rsi < ma and k < d:
        return 'VENDER'
    return 'ESPERAR'


def analyze(series, symbol, now=None, interval="1d", validate_only=False):
    now = now or datetime.now(timezone.utc)
    duration = timedelta(days=1 if interval == '1d' else 7)
    minimum = 250 if interval == '1d' else 80
    result = dict(symbol=symbol, interval=interval, status='N/D', signal='N/D', rsi=None, ma=None,
                  k=None, d=None, source=None, close_utc=None, close_lima=None,
                  reason='Históricos diarios pendientes. Pulsa Actualizar históricos.' if symbol == 'BTCUSDT'
                  else 'Históricos pendientes.')
    if not series:
        return result
    try:
        if series.get('status') != 'OK' or series.get('symbol') != symbol or series.get('interval') != interval or series.get('closed_only') is not True:
            raise ValueError('Identidad o temporalidad de la serie inválida.')
        source = series.get('source')
        allowed = ('KuCoin Spot', 'Binance Spot')
        if source not in allowed:
            raise ValueError('Fuente no autorizada para este indicador.')
        bars = series['records']
        if not minimum <= len(bars) <= 999:
            raise ValueError('Se requieren 250–999 cierres diarios consecutivos.')
        closes, previous = [], None
        for bar in bars:
            opening = datetime.fromisoformat(bar['open_utc'].replace('Z', '+00:00'))
            closing = datetime.fromisoformat(bar['close_utc'].replace('Z', '+00:00'))
            if opening.utcoffset() != timedelta(0) or closing.utcoffset() != timedelta(0) or opening.time() != datetime.min.time() or closing-opening != duration or (previous and opening != previous):
                raise ValueError('Velas fuera de UTC, discontinuas o duplicadas.')
            if closing > now or bar.get('source', source) != source:
                raise ValueError('Vela abierta o mezcla de proveedores.')
            price = bar['close']
            if isinstance(price, bool) or not math.isfinite(float(price)) or float(price) <= 0:
                raise ValueError('Cierre inválido.')
            closes.append(float(price))
            previous = closing
        expected = expected_close(interval, now)
        if interval == '1w' and any(datetime.fromisoformat(b['open_utc'].replace('Z','+00:00')).weekday() != 0 for b in bars):
            raise ValueError('Weekly candle must open Monday UTC')
        if previous != expected:
            raise ValueError('Serie desactualizada: falta el último cierre diario UTC.')
        if validate_only:
            return {'status':'OK'}
        gains = [max(0., b-a) for a, b in zip(closes, closes[1:])]
        losses = [max(0., a-b) for a, b in zip(closes, closes[1:])]
        gain, loss = sum(gains[:14])/14, sum(losses[:14])/14
        def rsi_value():
            return 50. if gain == loss == 0 else 100. if loss == 0 else 100.-100./(1.+gain/loss)
        rsis = [rsi_value()]
        for up, down in zip(gains[14:], losses[14:]):
            gain, loss = (gain*13+up)/14, (loss*13+down)/14
            rsis.append(rsi_value())
        stochastic = []
        for i in range(13, len(rsis)):
            window = rsis[i-13:i+1]
            lo, hi = min(window), max(window)
            stochastic.append(None if hi == lo else 100*(rsis[i]-lo)/(hi-lo))
        def sma(values, n):
            return [None if any(x is None for x in values[i-n+1:i+1]) else sum(values[i-n+1:i+1])/n for i in range(n-1, len(values))]
        ks = sma(stochastic, 3)
        ds = sma(ks, 3)
        if ks[-1] is None or ds[-1] is None:
            raise ValueError('Stoch RSI indefinido: ventana de RSI sin rango.')
        rsi, ma, k, d = rsis[-1], sum(rsis[-14:])/14, ks[-1], ds[-1]
        result.update(status='OK', signal=recommendation(rsi, ma, k, d), rsi=rsi, ma=ma, k=k, d=d,
                      source=source, close_utc=previous.isoformat(),
                      close_lima=previous.astimezone(timezone(timedelta(hours=-5))).strftime('%d/%m/%Y %H:%M Lima'), reason='')
    except (ValueError, TypeError, KeyError, OverflowError, AttributeError, IndexError):
        # Return a safe cause without disclosing file paths, credentials or raw data.
        result['reason'] = 'Serie inválida, incompleta, desactualizada o Stoch RSI sin rango. Revisar fuente y cierres.'
    return result


def weekly_series(series, now=None):
    """Aggregate only validated consecutive daily data into complete UTC weeks."""
    # Daily validation also checks freshness, source, continuity and coverage.
    checked = analyze(series, 'BTCUSDT', now, validate_only=True)
    if checked['status'] != 'OK':
        return None
    records = series['records']
    weeks = []
    for index, bar in enumerate(records):
        opening = datetime.fromisoformat(bar['open_utc'].replace('Z','+00:00'))
        group = records[index:index+7]
        if opening.weekday() == 0 and len(group) == 7:
            week=dict(open_utc=bar['open_utc'],close_utc=group[-1]['close_utc'],
                      close=group[-1]['close'],source=series['source'])
            try:
                # Preserve real weekly extrema, never use weekly close as high/low.
                for daily in group:
                    h,l,c=(float(daily[k]) for k in ('high','low','close'))
                    if any(isinstance(daily[k],bool) for k in ('high','low','close')) or not all(math.isfinite(v) and v>0 for v in (h,l,c)) or not l<=c<=h:
                        raise ValueError('OHLC inválido')
                week.update(high=max(float(d['high']) for d in group),low=min(float(d['low']) for d in group))
            except (KeyError,ValueError,TypeError,OverflowError):pass
            weeks.append(week)
    return dict(status='OK',symbol='BTCUSDT',interval='1w',closed_only=True,
                source=series['source'],records=weeks)


def technical_context(snapshot=None, interval='1d', now=None):
    snapshot = snapshot or {}
    series = snapshot.get('histories',{}).get('BTCUSDT:1d')
    if interval == '1w':
        series = weekly_series(series, now) if series else None
    btc = analyze(series,'BTCUSDT',now,interval)
    if interval == '1w' and btc['status'] != 'OK':
        btc['reason'] = 'Se requieren al menos 80 semanas UTC completas de BTC. Actualizar históricos (mínimo 566 días para cubrir semanas parciales).'
    from adx_context import enrich_context
    valid = bool(series) and analyze(series,'BTCUSDT',now,interval,validate_only=True)['status']=='OK'
    return [enrich_context(btc,series,valid)]


def daily_context(snapshot=None, now=None):
    return technical_context(snapshot, '1d', now)


def expected_close(interval, now=None):
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return day if interval == '1d' else day-timedelta(days=day.weekday())
