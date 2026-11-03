"""Explicit public Glassnode MCP fetch; only BTC STH and USDT/USD, no portfolio data."""
import asyncio
import json
import math
import os
import tempfile
import threading
from datetime import datetime,timezone,timedelta
from pathlib import Path
from btc_references import valid_metric

STH='/v1/metrics/market/price_realized_less_155_usd'
FX='/v1/metrics/market/price_usd_close'
_LOCK=threading.Lock()

def cache_path():return Path(os.getenv('KAIROS_GLASSNODE_CACHE_FILE','/tmp/kairos-glassnode-refs.json'))

def cached():
    try:
        value=json.loads(cache_path().read_text())
        return value if isinstance(value,dict) else {}
    except (ValueError,OSError):return {}

def latest_closed(payload,now=None):
    now=now or datetime.now(timezone.utc)
    if not isinstance(payload,dict):raise ValueError('Invalid metric envelope')
    data=payload.get('raw_data',payload.get('data'))
    if not isinstance(data,list) or len(data)>64:raise ValueError('Missing metric series')
    today=now.astimezone(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    seen=set();closed=[]
    for row in data:
        t=row.get('t',row.get('timestamp'));v=row.get('v',row.get('value'))
        if type(t) not in (int,float) or not math.isfinite(t) or t!=int(t) or t%86400 or t in seen:raise ValueError('Invalid/duplicate daily timestamp')
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:raise ValueError('Invalid metric value')
        seen.add(t);at=datetime.fromtimestamp(t,timezone.utc)
        if at<today-timedelta(days=7) or at>=today:continue
        closed.append((at,float(v)))
    if not closed:raise ValueError('No closed daily observation')
    at,value=max(closed)
    point=dict(status='OK',value=value,point_utc=at.isoformat(),source='Glassnode MCP',resolution='24h')
    if not valid_metric(point,now):raise ValueError('Metric stale')
    return point

async def fetch_references(now=None):
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport
    now=now or datetime.now(timezone.utc)
    end=now.replace(hour=0,minute=0,second=0,microsecond=0)
    headers={}
    # An API key is optional and must only be set deliberately by the operator.
    if os.getenv('GLASSNODE_API_KEY'):headers['X-Api-Key']=os.environ['GLASSNODE_API_KEY']
    transport=StreamableHttpTransport('https://mcp.glassnode.com',headers=headers or None)
    result={}
    async with Client(transport,timeout=25) as client:
        for key,endpoint,asset in [('sth',STH,'BTC'),('fx',FX,'USDT')]:
            try:
                raw=await client.call_tool('fetch_metric',{'endpoint':endpoint,'params':{'a':asset,'i':'24h','f':'json','s':str(int((end-timedelta(days=7)).timestamp())),'u':str(int(end.timestamp()))}})
                if raw.is_error:raise ValueError('Metric access failure')
                payload=raw.data if isinstance(raw.data,dict) else None
                if payload is None:
                    for block in raw.content:
                        if getattr(block,'type',None)=='text':
                            payload=json.loads(block.text);break
                result[key]=latest_closed(payload,now)
                result[key].update(asset=asset,metric=endpoint,currency='USD')
            except Exception:
                result[key]=dict(status='N/D',reason='Métrica no disponible, sin permiso o sin cierre reciente en Glassnode.')
    return result

def refresh(now=None,fetcher=None):
    now=now or datetime.now(timezone.utc)
    with _LOCK:
        previous=cached()
        stamp=previous.get('fetched_utc')
        if stamp:
            try:
                at=datetime.fromisoformat(stamp)
                age=(now-at).total_seconds()
                both=all(valid_metric(previous.get(key,{}),now) for key in ('sth','fx'))
                if 0<=age<60 or (both and at.date()==now.date()):return dict(previous,cached=True)
            except (ValueError,TypeError):pass
        result=asyncio.run((fetcher or fetch_references)(now))
        result.update(fetched_utc=now.isoformat(),status='OK' if result.get('sth',{}).get('status')=='OK' else 'PARTIAL',source='Glassnode MCP')
        path=cache_path();fd,name=tempfile.mkstemp(prefix='glassnode-',suffix='.json',dir=path.parent)
        try:
            with os.fdopen(fd,'w') as f:json.dump(result,f,allow_nan=False)
            os.replace(name,path)
        finally:
            if os.path.exists(name):os.unlink(name)
        return result
