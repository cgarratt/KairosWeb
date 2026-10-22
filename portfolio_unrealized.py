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


def current_capital_distribution(rows, physical_usdt, qf_real, *, portfolio_total=None):
    """Four disjoint, current Spot-valued capital segments.

    Inputs must come from the same validated PUBLICADO snapshot and Binance
    Spot observation as portfolio_allocation. QF is already part of physical
    USDT; never add it to that value again. Fail closed on missing/inconsistent
    custody instead of drawing a plausible but incorrect donut.
    """
    cash=_finite(physical_usdt)
    reserve=_finite(qf_real)
    if cash is None or reserve is None or reserve > cash:
        raise ValueError('Liquidez física/QF no conciliada')
    if len(rows)!=12:
        raise ValueError('Se requieren 12 tokens para distribución de capital')
    holdings_value=0.0
    exchange_value=0.0
    for row in rows:
        price=_finite(row.get('price'), positive=True)
        hodl=_finite(row.get('hodl_units'))
        core=_finite(row.get('core_units'))
        exchange=_finite(row.get('exchange_units'))
        reported=_finite(row.get('value'))
        total_units=_finite(row.get('units'))
        if any(v is None for v in (price,hodl,core,exchange,reported,total_units)):
            raise ValueError('Custodia o Spot de token incompleto')
        if not _math.isclose(hodl+core+exchange,total_units,rel_tol=1e-9,abs_tol=1e-7):
            raise ValueError('Custodia no concilia unidades de token')
        value=(hodl+core+exchange)*price
        if not _math.isclose(value,reported,rel_tol=1e-9,abs_tol=0.01):
            raise ValueError('Valor de token no concilia con Spot')
        holdings_value+=(hodl+core)*price
        exchange_value+=exchange*price
    values=(('hodl_core','HODL + Core',holdings_value),
            ('exchange','Exchange',exchange_value),
            ('liquidity','Liquidez operativa',cash-reserve),
            ('trading','ReservaTrading QF',reserve))
    total=sum(v for _,_,v in values)
    if not math.isfinite(total) or total <= 0:
        raise ValueError('Patrimonio actual inválido')
    if portfolio_total is not None:
        expected=_finite(portfolio_total)
        if expected is None or not _math.isclose(total,expected,rel_tol=1e-9,abs_tol=0.01):
            raise ValueError('Distribución por custodia no concilia con patrimonio')
    return {'total':total,
            'items':[{'key':k,'name':label,'value':v,'pct':v/total*100}
                     for k,label,v in values],
            'basis':'02_POSICIONES + 03_LIQUIDEZ + Binance Spot MCP',
            'qf_included_once':True}


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
"""Historical *fixed-basket* repricing with actual CLOSED Binance Spot 1D prices.

Does not claim historical units, realized returns, flows, or certified PRI data.
No writing to Google Sheets or to the order/fill book.
"""
from datetime import date, datetime, timedelta, timezone
from math import isfinite

EXPECTED = ('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO',
            'PUMP','PLUME','VIRTUAL','PEPE')

class RepricingError(ValueError):
    pass


def _positive(x, where, allow_zero=False):
    if isinstance(x, bool):
        raise RepricingError(f'{where}: valor no numérico')
    try:
        f=float(x)
    except (TypeError, ValueError) as exc:
        raise RepricingError(f'{where}: valor no numérico') from exc
    if not isfinite(f) or (f<0 if allow_zero else f<=0):
        raise RepricingError(f'{where}: valor inválido')
    return f


def build_fixed_basket_history(rows, physical_usdt, candle_data, *, max_days=100):
    """Closed 1D close aligned across every token, holdings held constant.

    candle_data: {token: Binance MCP get_kairos_ohlcv response}.  Never fill
    missing days or prices and never replace absent quotes with current spot.
    """
    cash=_positive(physical_usdt, 'USDT físico', allow_zero=True)
    if len(rows)!=12 or {r.get('token') for r in rows}!=set(EXPECTED):
        raise RepricingError('02_POSICIONES: falta inventario de 12 tokens')
    seen={}
    for row in rows:
        t=row['token']; units=_positive(row.get('units'),f'{t} unidades',allow_zero=True)
        raw=candle_data.get(t)
        if not isinstance(raw,dict) or raw.get('status')!='OK' or not raw.get('closed_only') or raw.get('interval')!='1d':
            raise RepricingError(f'{t}: MCP OHLCV 1D cerrado indisponible')
        if str(raw.get('symbol'))!=f'{t}USDT':
            raise RepricingError(f'{t}: par distinto a {t}USDT')
        rows1=raw.get('records') or []
        indexed={}
        for candle in rows1:
            try:
                close_dt=datetime.fromisoformat(str(candle['close_utc']).replace('Z','+00:00'))
                if close_dt.tzinfo is None or close_dt.astimezone(timezone.utc).hour!=0:
                    continue
                candle_day=(close_dt.astimezone(timezone.utc)-timedelta(days=1)).date().isoformat()
                price=_positive(candle.get('close'),f'{t} precio {candle_day}')
                if candle_day in indexed:
                    raise RepricingError(f'{t}: vela diaria duplicada')
                indexed[candle_day]=price
            except (KeyError,ValueError,TypeError) as exc:
                raise RepricingError(f'{t}: datos de vela diaria inválidos') from exc
        if len(indexed)<2:
            raise RepricingError(f'{t}: menos de dos cierres diarios verificables')
        seen[t]=(units,indexed)
    common=set.intersection(*(set(d) for _,d in seen.values()))
    dates=sorted(common)[-max_days:]
    if len(dates)<2:
        raise RepricingError('Las 12 series MCP no tienen dos cierres diarios en común')
    # No invisible gaps between daily candle observations.
    for a,b in zip(dates,dates[1:]):
        if (date.fromisoformat(b)-date.fromisoformat(a)).days!=1:
            raise RepricingError('Brecha en cierres diarios comunes; no se interpola')
    points=[]
    for day in dates:
        crypto=sum(q*series[day] for q,series in seen.values())
        total=crypto+cash
        if not (isfinite(total) and total>0):
            raise RepricingError('Valorización retrospectiva inválida')
        points.append({'day':day,'timestamp':day+'T23:59:59+00:00',
                       'total':round(total,2),'crypto':round(crypto,2),'cash':round(cash,2)})
    basis=points[0]['total']
    for p in points:
        p['change_pct']=round((p['total']/basis-1)*100,4)
    return {'status':'OK','mode':'SIMULACION_CARTERA_FIJA','points':points,
            'days':len(points), 'last_closed_day':points[-1]['day'],
            'source':'BINANCE_SPOT_MCP_1D_CERRADO',
            'disclaimer':'Unidades actuales y USDT físico actual congelados retrospectivamente. No es rentabilidad real histórica, no refleja fills/aportes/retiros ni modifica PRI.'}


def btc_equivalent(total_usdt, btc_spot_usdt):
    """Whole portfolio BTC denomination using the *same* observed Binance Spot quote.

    total_usdt must already contain crypto market value + physical USDT once
    (including the Quantfury trading reserve as a component of physical USDT).
    No conversion from historic pricing or a separately observed BTC price.
    """
    if (not isinstance(total_usdt,(int,float)) or isinstance(total_usdt,bool)
            or not _math.isfinite(total_usdt) or total_usdt<0):
        raise ValueError('Valor total USDT inválido para conversión BTC')
    if (not isinstance(btc_spot_usdt,(int,float)) or isinstance(btc_spot_usdt,bool)
            or not _math.isfinite(btc_spot_usdt) or btc_spot_usdt<=0):
        raise ValueError('BTCUSDT Spot no válido; no puede calcularse equivalencia BTC')
    return float(total_usdt)/float(btc_spot_usdt)
