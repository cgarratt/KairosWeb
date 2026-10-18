"""Kairos proposal inbox — price structure vs portfolio rebalance.

Phase 1 is read-only. Structural LIMIT objectives are derived solely from
weekly pivots/Fibonacci; balancing proposals may lack a LIMIT price.
Neither proposed BUY nor SELL are orders, committed funds or exchange fills.
Real activity remains exclusively in 05_ORDENES/06_FILLS after reconciliation.
"""
from math import isfinite
from wave_structure import SELL_RATIOS

VENUES = {
    'BTC':'Binance', 'ETH':'Binance', 'SOL':'Binance', 'LINK':'Binance',
    'HBAR':'Binance', 'ONDO':'Binance',
    'SUI':'KuCoin', 'PUMP':'KuCoin', 'PLUME':'KuCoin',
    'VIRTUAL':'KuCoin', 'PEPE':'KuCoin', 'HYPE':'Hyperliquid',
}
FIB_NAMES = ('38.2%', '50%', '61.8%', '78.6%')
LEVEL_FIELDS = ('ref382','c1','c2','ref786')


def _finite_pos(value):
    try:
        n=float(value)
        return n if isfinite(n) and n>0 else None
    except (TypeError, ValueError):
        return None


def _proximity(side, spot, target, threshold):
    """Distance to FUTURE objective relative to current Spot (not filled)."""
    if not spot or not target:
        return None, 'PRECIO_PENDIENTE'
    if side == 'BUY':
        distance=(spot/target-1)*100  # positive while buy price lies below spot
    else:
        distance=(target/spot-1)*100  # positive while sell price lies above spot
    if distance < -1e-9:
        return distance, 'NIVEL_SUPERADO'
    if distance <= threshold + 1e-9:
        return distance, 'CERCA'
    return distance, 'EN_ESPERA'


def _buy_allocation(items, budget, crypto):
    """Same two-stage balance + proportional surplus as purchase_plan.js."""
    t=[max(0.,float(x['target'])) for x in items]
    v=[max(0.,float(x['current_usdt'])) for x in items]
    total=sum(t)
    n=len(items)
    if total<=0 or budget<=0:return [0.]*n
    weights=[x/total for x in t]
    required=max([0.]+[v[i]/weights[i]-crypto for i in range(n) if weights[i]>0])
    first=min(budget,max(0.,required))
    if first<=1e-9: balance=[0.]*n
    elif budget>=required-1e-7:
        balance=[max(0.,weights[i]*(crypto+required)-v[i]) for i in range(n)]
    else:
        gaps=[max(0.,weights[i]*(crypto+first)-v[i]) for i in range(n)]
        denom=sum(gaps)
        balance=[first*x/denom for x in gaps] if denom>0 else [0.]*n
    extra=max(0.,budget-first)
    return [balance[i]+extra*weights[i] for i in range(n)]


def staged_buy_candidates(buy, budget, proximity_pct=1.0):
    """Hypothetical sequential fills only: four buy prices/weights per token.

    Never report these synthetic fills as submitted, committed or realized.
    """
    tokens=buy['tokens']
    levels=buy['o2_levels']
    eligible=buy['buy_eligibility']
    stage_weights=buy['buy_stage_weights']
    default=buy['forecast_o2_allocation']
    weights=[]; px_all=[]
    for t in tokens:
        token=t['token']
        v=stage_weights.get(token,default)
        if not isinstance(v,(list,tuple)) or len(v)!=4 or abs(sum(float(x) for x in v)-100)>1e-6:
            raise ValueError('Invalid published tranche weights')
        weights.append([float(x)/100 for x in v])
        ref=levels.get(token) or {}
        prices=[_finite_pos(ref.get(k)) for k in LEVEL_FIELDS]
        px_all.append(prices if eligible.get(token) is True else [None]*4)
    units=[max(0.,float(t.get('units') or 0)) for t in tokens]
    remaining=max(0.,float(budget));candidates=[]
    for j in range(4):
        sim_prices=[px_all[i][j] or float(t['price']) for i,t in enumerate(tokens)]
        values=[units[i]*sim_prices[i] for i in range(len(tokens))]
        crypto=sum(values)
        planned=min(remaining,budget*sum(max(0.,float(t['target']))*weights[i][j]
                       for i,t in enumerate(tokens) if px_all[i][j] is not None))
        items=[{'target':t['target'] if px_all[i][j] is not None else 0,
                'current_usdt':values[i]} for i,t in enumerate(tokens)]
        spends=_buy_allocation(items,planned,crypto)
        actually_spent=0.
        for i,t in enumerate(tokens):
            price=px_all[i][j];a=max(0.,spends[i]) if price else 0.
            if not price or a<.005:continue
            token=t['token'];spot=_finite_pos(t['price'])
            ctx=buy.get('weekly_context',{}).get(token,{})
            phase=ctx.get('mode') or 'RETROCESO_ALCISTA'
            stage=f"O4C{j+1}" if phase=='O4' else f"O2C{j+1}" if phase=='O2' else f"C{j+1}"
            delta,proximity=_proximity('BUY',spot,price,proximity_pct)
            if token=='HYPE':
                # Binance HYPE/USDT Spot and Hyperliquid HYPE/USDC macro must
                # not be treated as one homogeneous quote for proximity.
                delta,proximity=None,'COTIZACION_NO_HOMOLOGADA'
            candidates.append({
                'token':token,'venue':VENUES.get(token,'Sin asignar'),
                'category':'ESTRUCTURA','side':'BUY','mode':'Compras',
                'wave':phase,'stage':stage,'fib':FIB_NAMES[j],
                'spot':spot,'limit':price,'distance_pct':delta,'quote_currency':'USDC' if token=='HYPE' else 'USDT',
                'usdt':a,'quantity':a/price,'proximity':proximity,
                'pivot_status':'PROPUESTO / PROVISIONAL' if ctx.get('operational_blocked') or ctx.get('status')=='PROPUESTO_SIMULACION' else 'VALIDADO / REVISAR MASTER',
                'order_status':'PROPUESTA_NO_COLOCADA',
                'source':'Compras · retroceso semanal','note':'Compra secuencial simulada; toque de precio no acredita fill',
                'sizing_status':'SIMULADO',
            })
            units[i]+=a/price;actually_spent+=a
        remaining=max(0.,remaining-actually_spent)
    return candidates,remaining


def structural_sell_candidates(d, buy, wave_levels=None, proximity_pct=1.0):
    """Future-limit SELL objectives from VERIFIED SOURCE ANCHORS only.

    O3 and O5 use the published dated 3-point Fibonacci structure. A generic
    bullish weekly impulse MAY supply independent projections 1.618..4.618,
    explicitly *not* certified Elliott O3/O5. No executable SELL sizing is
    inferred from an unapproved staged liquidation plan.
    """
    wave_levels=wave_levels or {}
    candidates=[]
    contexts=buy.get('weekly_context') or {}
    for row in d['rows']:
        token=row['token']
        if token=='BTC':continue  # BTC NEVER SELL, including price structure
        spot=_finite_pos(row.get('price'))
        if spot is None:continue
        level_grids=[]
        published=(wave_levels.get(token) or {}).get('levels') or {}
        for wave in ('O3','O5'):
            levels=published.get(wave) or {}
            if levels:
                level_grids.append((wave,levels,'PUBLICADO_REFERENCIA_3_ANCLAS'))
        # Only if no published multi-anchor extension, offer a 2-pivot generic
        # weekly continuation reference. Never call it O3/O5.
        if not level_grids:
            ctx=contexts.get(token) or {}
            pair=ctx.get('anchors') or {}
            low=pair.get('low') or {};high=pair.get('high') or {}
            l=_finite_pos(low.get('price'));h=_finite_pos(high.get('price'))
            if (ctx.get('eligible') is True or buy.get('buy_eligibility',{}).get(token) is True) and l and h and h>l and low.get('date') and high.get('date') and low['date']<high['date']:
                levels={f'EXT1W{i}':l+e*(h-l) for i,e in enumerate(SELL_RATIOS,1)}
                level_grids.append(('EXTENSION_1W',levels,'PROPUESTO_IMPULSO_2_ANCLAS'))
        for wave,levels,origin in level_grids:
            for i,ratio in enumerate(SELL_RATIOS,1):
                stage=f'{wave}V{i}' if wave in ('O3','O5') else f'EXT1W{i}'
                px=_finite_pos(levels.get(stage))
                if not px:continue
                distance,proximity=_proximity('SELL',spot,px,proximity_pct)
                if token=='HYPE':
                    # HYPE weekly extensions quote USDC: preserve the technical
                    # level but do not compare to Binance HYPE/USDT Spot.
                    distance,proximity=None,'COTIZACION_NO_HOMOLOGADA'
                # Past upside levels are NOT upcoming sell-order suggestions.
                if token!='HYPE' and (distance is None or distance<0):continue
                candidates.append({
                    'token':token,'venue':VENUES.get(token,'Sin asignar'),
                    'category':'ESTRUCTURA','side':'SELL','mode':'Estructura 1W',
                    'wave':wave,'stage':stage,'fib':f'{ratio:.3f}',
                    'spot':spot,'limit':px,'distance_pct':distance,'quote_currency':'USDC' if token=='HYPE' else 'USDT',
                    'usdt':None,'quantity':None,'proximity':proximity,
                    'pivot_status':origin,'order_status':'REFERENCIA_NO_COLOCADA',
                    'source':'Fibonacci 1W · extensiones',
                    'note':'Precio objetivo semanal; tamaño SELL pendiente de política O3/O5 o revisión de Exchange',
                    'sizing_status':'SIN_TAMANO',
                })
    return candidates


def portfolio_candidates(d, bal):
    """Spot-valued rebalancing suggestions; never fabricate LIMIT levels."""
    by_token={r['token']:r for r in d['rows']};candidates=[]
    for side,items in (('BUY',bal.get('buys',[])),('SELL',bal.get('sells',[]))):
        for suggestion in items:
            token=suggestion['token']
            if token not in by_token or (side=='SELL' and token=='BTC'):continue
            row=by_token[token];spot=_finite_pos(row.get('price'))
            if not spot:continue
            amount=max(0.,float(suggestion.get('value') or 0))
            if side=='SELL':
                free=max(0.,float(row.get('exchange_units') or 0))
                units=min(max(0.,float(suggestion.get('units') or 0)),free)
                amount=min(amount,units*spot)
                if amount<.005:continue
            else:
                units=amount/spot if amount>0 else 0
            candidates.append({
                'token':token,'venue':VENUES.get(token,'Sin asignar'),
                'category':'BALANCE','side':side,'mode':'Balancer',
                'wave':'INFRA' if side=='BUY' else 'SOBRE',
                'stage':'REBALANCEO','fib':None,'spot':spot,'limit':None,
                'distance_pct':None,'usdt':amount,'quantity':units,'quote_currency':'USDT',
                'proximity':'PRECIO_PENDIENTE' if amount>0 else 'SIN_CAJA',
                'pivot_status':'SIN_FILTRO_SEMANAL',
                'order_status':'PROPUESTA_NO_COLOCADA',
                'source':'Balancer · desviación vs objetivo',
                'note':'Spot orientativo, sin nivel LIMIT ni libro de órdenes conciliado',
                'sizing_status':'SIMULADO' if amount>0 else 'SIN_CAJA',
            })
    return candidates


def build_order_inbox(d, buy_payload, balancer_payload, proximity_pct=1.0, wave_levels=None):
    """Unified read-only inbox, grouped into Balance and Structural sources."""
    threshold=float(proximity_pct)
    if not 0<threshold<=5:raise ValueError('Invalid proximity threshold')
    budget=min(float(d['usdt_operating']),max(0.,float(d['usdt_total'])-float(d['trading_reserve'])))
    buys,unassigned=staged_buy_candidates(buy_payload,budget,threshold)
    technical_sells=structural_sell_candidates(d,buy_payload,wave_levels,threshold)
    portfolio=portfolio_candidates(d,balancer_payload)
    combined=buys+technical_sells+portfolio
    for c in combined:
        c['near_reference']=(c['category']=='ESTRUCTURA' and c['proximity']=='CERCA')
        c['actionable_alert']=False  # fase 1 never executable, especially unsized SELL
        c['proposal_key']='|'.join((c['venue'],c['token'],c['category'],c['side'],c['mode'],c['stage'],
                                    f"{c['limit']:.12g}" if c['limit'] is not None else 'SIN_LIMIT'))
    combined.sort(key=lambda c:(0 if c['proximity']=='CERCA' else 1 if c['proximity']=='EN_ESPERA' else 2,
                                 c['venue'],c['token'],c['side'],c['stage']))
    coverage=[]
    for row in d['rows']:
        token=row['token'];spot=_finite_pos(row.get('price'))
        future=[x for x in combined if x['token']==token and x['category']=='ESTRUCTURA' and
                x['limit'] is not None and x['distance_pct'] is not None and x['distance_pct']>=0]
        nearest=min(future,key=lambda x:x['distance_pct'],default=None)
        balance_fallback=next((x for x in portfolio if x['token']==token and
                               x['usdt'] is not None and x['usdt']>.005),None)
        picked=nearest or balance_fallback
        coverage.append({'token':token,'venue':VENUES.get(token,'Sin asignar'),
                         'spot':spot,'side':picked['side'] if picked else None,
                         'limit':picked['limit'] if picked else None,
                         'distance_pct':picked['distance_pct'] if picked else None,
                         'stage':picked['stage'] if picked else None,
                         'origin':picked['category'] if picked else 'N/D',
                         'status':('CERCANO' if nearest['distance_pct']<=threshold+1e-9 else 'EN_ESPERA') if nearest
                                  else 'SIN_LIMIT' if balance_fallback else 'N/D',
                         'reason':None if nearest else 'BALANCE_SIN_LIMIT' if balance_fallback else 'SIN_OBJETIVO_VALIDO',
                         'no_fake_order':nearest is None})
    sales=[c for c in portfolio if c['side']=='SELL']
    balances_buys=[c for c in portfolio if c['side']=='BUY']
    venues={v:{'available_usdt':max(0.,float(d['liquidity_venues'].get(v,0))),
               'buys_proposed_usdt':sum(x['usdt'] or 0 for x in buys if x['venue']==v),
               'sells_proposed_usdt':sum(x['usdt'] or 0 for x in sales if x['venue']==v),
               'balance_buys_usdt':sum(x['usdt'] or 0 for x in balances_buys if x['venue']==v),
               'structural_sell_levels':sum(x['venue']==v for x in technical_sells)}
            for v in ('Binance','KuCoin','Hyperliquid')}
    return {'candidates':combined,'categories':{'ESTRUCTURA':buys+technical_sells,'BALANCE':portfolio},
            'coverage':coverage,'venues':venues,'buy_budget':budget,
            'buy_unassigned':unassigned,'buy_planned':sum(x['usdt'] or 0 for x in buys),
            'sell_planned':sum(x['usdt'] or 0 for x in sales),
            'near_count':sum(bool(x['near_reference']) for x in combined),
            'excluded_hype_count':sum(x['venue']=='Hyperliquid' for x in combined),
            'proximity_pct':threshold,
            'note':'Solo propuestas. Balance sin LIMIT técnico; extensiones SELL sin tamaño aprobado. No se envían órdenes ni se acreditan fills.'}
