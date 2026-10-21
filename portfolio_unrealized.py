"""Read-only unrealized P&L for the published Kairos portfolio.

Market price and units must come from the already validated live dashboard;
never from a screenshot, local snapshots, LIMIT proposals or fills inferred by touch.
"""
import math


def _finite(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        return None
    return value


def summarize_unrealized(rows):
    """Build a 12-token diverging chart and total without inventing missing costs."""
    items = []
    raw_total = 0.0
    raw_cost = 0.0
    missing = []
    for row in rows:
        token = row['token']
        units = _finite(row.get('units'))
        spot = _finite(row.get('price'), positive=True)
        cost = _finite(row.get('avg_cost'), positive=True)
        if units is None or spot is None or (units > 0 and cost is None):
            missing.append(token)
            items.append({'token': token, 'status': 'N/D', 'pnl_usdt': None,
                          'pnl_pct': None, 'bar_pct': 0})
            continue
        # A genuinely empty position has zero unrealized P&L, not an invented cost.
        open_cost = units * cost if units > 0 else 0.0
        pnl = units * spot - open_cost
        raw_total += pnl
        raw_cost += open_cost
        items.append({'token': token, 'status': 'ZERO' if units == 0 else 'OK',
                      'pnl_usdt': round(pnl, 2), 'pnl_pct': (round(pnl / open_cost * 100, 2)
                          if open_cost > 0 else None), 'bar_pct': 0})
    scale = max((abs(x['pnl_usdt']) for x in items if x['pnl_usdt'] is not None), default=0.0)
    for x in items:
        if scale and x['pnl_usdt'] is not None:
            x['bar_pct'] = round(abs(x['pnl_usdt']) / scale * 100, 3)
    return {
        'status': 'OK' if not missing else 'PARCIAL',
        'items': items,
        'total_usdt': round(raw_total, 2) if not missing else None,
        'total_pct': round(raw_total / raw_cost * 100, 2) if raw_cost and not missing else None,
        'cost_open_usdt': round(raw_cost, 2) if not missing else None,
        'missing_tokens': missing,
        'count': len(items),
        'basis': 'Unidades de 02_POSICIONES × (Spot Binance MCP − costo promedio 02_POSICIONES)',
    }


# Portfolio layout v2.0.22: deliberately separates a verified current valuation from
# a certified, flow-adjusted return history (not yet available in Master 5.0.0).
import math as _math
from datetime import datetime as _datetime, timezone as _timezone

ALLOCATION_COLORS = {'USDT':'#2080ed','BTC':'#ed9e34','ETH':'#7551d9',
                     'SOL':'#14ae85','LINK':'#ed5374','HYPE':'#3b8fb1',
                     'HBAR':'#83b940','SUI':'#627fe3','ONDO':'#945bdb',
                     'PUMP':'#e98b7d','PLUME':'#29b7bb','VIRTUAL':'#ae65e9','PEPE':'#bfa752'}


def portfolio_allocation(rows, physical_usdt):
    """13 mutually-exclusive current amounts, including *physical* USDT once.

    All quantities/prices must originate from a validated published snapshot and MCP.
    Reject incomplete series instead of charting a misleading 0.
    """
    if isinstance(physical_usdt, bool) or not isinstance(physical_usdt,(int,float)) or not _math.isfinite(physical_usdt) or physical_usdt<0:
        raise ValueError('USDT físico inválido')
    if len(rows)!=12:
        raise ValueError('Se requieren los 12 tokens')
    values=[]
    for row in rows:
        value=row.get('value')
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not _math.isfinite(value) or value<0:
            raise ValueError('Valor Spot de token inválido')
        values.append({'token':str(row['token']).replace('PUMPFUN','PUMP'),'value':float(value)})
    total=physical_usdt+sum(x['value'] for x in values)
    if total<=0:raise ValueError('Patrimonio sin valoración positiva')
    items=[{'token':'USDT','value':float(physical_usdt)}]+values
    items.sort(key=lambda x:(-x['value'],x['token']))
    for i,x in enumerate(items):
        x['pct']=x['value']/total*100
        x['color']=ALLOCATION_COLORS[x['token']]
    return {'items':items,'total':total,'crypto':total-physical_usdt,'physical_cash':physical_usdt}


def category_allocation(rows):
    """Crypto-only allocation vs published tier targets, without USDT."""
    if len(rows)!=12:raise ValueError('Se requieren 12 activos para distribución por Tier')
    total=sum(float(r['value']) for r in rows)
    if total<=0:raise ValueError('Manga cripto sin valoración')
    output=[]
    for tier in ('T1','T2','T3'):
        subset=[r for r in rows if r['tier']==tier]
        output.append({'tier':tier,'actual':sum(float(r['value']) for r in subset)/total*100,
                       'target':sum(float(r['target']) for r in subset)*100,
                       'tokens':', '.join(str(r['token']) for r in subset)})
    return output


def pri_valuation_history(table):
    """Only certified complete PRI valuation rows; never synthetic backfills.

    PRI rows with DATA_ERROR/PARCIAL may still contain amounts but are not
    certified complete valuations: they must not become return-chart points.
    No cashflow-adjusted return is inferred from changing equity levels.
    """
    if not table or not isinstance(table,list):return []
    header=[str(x).strip().lower() for x in table[0]]
    required=('spot utc','estado','patrimonio usd','usdt físico','valor cripto usd')
    if not all(key in header for key in required):return []
    indexes={key:header.index(key) for key in required}
    result={}
    for row in table[1:]:
        try:
            status=str(row[indexes['estado']]).strip().upper()
            if status not in ('OK','VALIDADO','CERTIFICADO','COMPLETE','COMPLETO'):continue
            date=_datetime.fromisoformat(str(row[indexes['spot utc']]).replace('Z','+00:00'))
            if date.tzinfo is None:continue
            date=date.astimezone(_timezone.utc)
            total=float(row[indexes['patrimonio usd']]); cash=float(row[indexes['usdt físico']]); crypto=float(row[indexes['valor cripto usd']])
            if not all(_math.isfinite(v) and v>=0 for v in (total,cash,crypto)):continue
            if abs(total-cash-crypto)>max(.02,total*1e-6):continue
            day=date.strftime('%Y-%m-%d')
            if day not in result or date>result[day][0]:
                result[day]=(date,{'day':day,'timestamp':date.isoformat(),'total':round(total,2),
                                   'cash':round(cash,2),'crypto':round(crypto,2)})
        except (IndexError,TypeError,ValueError,OverflowError):
            continue
    return [result[day][1] for day in sorted(result)]
