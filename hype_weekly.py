"""Resample Hyperliquid HYPE/USDC 1D closed spot into full UTC Mon-Sun weeks.
A partial or gap week is discarded, never filled from Binance or futures.
"""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import math

class HypeHistoryError(ValueError):pass

def aggregate_weeks(data):
    if data.get('status')!='OK' or data.get('source')!='Hyperliquid Spot' or data.get('pair')!='HYPE/USDC' or data.get('interval')!='1d' or data.get('closed_only') is not True:
        raise HypeHistoryError('Source must be closed HYPE/USDC 1d Spot data')
    records=data.get('records')
    if not isinstance(records,list) or not records:raise HypeHistoryError('No closed days')
    groups=defaultdict(dict)
    for row in records:
        try:
            t=datetime.fromisoformat(row['open_utc'].replace('Z','+00:00'))
            end=datetime.fromisoformat(row['close_utc'].replace('Z','+00:00'))
            if t.utcoffset()!=timedelta(0) or end-t!=timedelta(days=1) or t.hour or t.minute or t.second:raise ValueError('bad day')
            week=(t-timedelta(days=t.weekday())).date()
            vals={k:float(row[k]) for k in ('open','high','low','close','volume_base')}
            if not all(math.isfinite(x) and x>=0 for x in vals.values()):raise ValueError('invalid values')
            if not (vals['high']>=max(vals['open'],vals['close'],vals['low']) and vals['low']<=min(vals['open'],vals['close'])):raise ValueError('OHLC error')
            if t.date() in groups[week]:raise ValueError('duplicate day')
            groups[week][t.date()]=vals
        except (KeyError,ValueError,TypeError) as exc:
            raise HypeHistoryError('Invalid HYPE Spot day in MCP response') from exc
    result=[]; skipped=0
    for week,dates in sorted(groups.items()):
        expected=[week+timedelta(days=i) for i in range(7)]
        if set(dates)!=set(expected):skipped+=1;continue
        candles=[dates[d] for d in expected]
        result.append({'week_open_utc':week.isoformat()+'T00:00:00Z',
                       'week_close_utc':(week+timedelta(days=7)).isoformat()+'T00:00:00Z',
                       'open':candles[0]['open'],'high':max(x['high'] for x in candles),
                       'low':min(x['low'] for x in candles),'close':candles[-1]['close'],
                       'volume_base':sum(x['volume_base'] for x in candles),
                       'closed_days':7})
    if not result:raise HypeHistoryError('No complete closed UTC Mon-Sun weeks')
    return {'status':'OK','source':'Hyperliquid Spot HYPE/USDC',
            'method':'CLOSED_1D_TO_FULL_UTC_MONDAY_SUNDAY',
            'scope':'EXPLORATORY_ONLY','weeks':result,'full_weeks':len(result),
            'discarded_incomplete_weeks':skipped, 'approved_elliott_pivots':False}
