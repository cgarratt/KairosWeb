"""Select sufficient closed-daily history to validate a CL's 1W 5L/5R + BOS.

Read only; no Sheets mutation and no fallback to a different market source.
"""
from datetime import datetime, timezone, date
import re


def required_daily_candles(cl_date, *, now=None, lookback_weeks=30):
    current = now or datetime.now(timezone.utc).date()
    if isinstance(current,datetime):current=current.date()
    anchor=date.fromisoformat(str(cl_date))
    age=(current-anchor).days
    count=max(365,age+7*lookback_weeks)
    if count>999:
        raise ValueError('CL exceeds bounded MCP history; paginate explicitly')
    return count


def fetch_closed_binance_history(fetch, market, cl_date, *, now=None):
    """Retry once with the actual available candle count if MCP reports fewer.

    The following structural review must still fail closed when 5L/5R or BOS
    is unobservable. Fetching fewer candles never implies certification.
    """
    requested=required_daily_candles(cl_date,now=now)
    def read(n):
        return fetch('BINANCE_MCP_URL','get_kairos_ohlcv',
                     {'symbol':market+'USDT','interval':'1d','limit':n})
    result=read(requested)
    if result.get('status')=='DATA_ERROR':
        reason=str(result.get('reason') or result.get('message') or '')
        match=re.search(r'Insufficient closed candles:\s*(\d+)\s*/\s*(\d+)',reason,re.I)
        if match:
            available=int(match.group(1))
            if 120<=available<requested:
                result=read(available)
    return result
