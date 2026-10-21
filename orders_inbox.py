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


# A single read-only portfolio capacity policy for Balancer and Orders.
# The browser's Sales Optimizer keeps a JS parity implementation verified by tests.
TIER_SELL_FRACTIONS={'T1':.30,'T2':.70,'T3':1.0}
_EPS=1e-8


def drift_tone(drift_pp, band_pp):
    """One drift classification for all report colors, including edge values."""
    import math
    band=float(band_pp); d=float(drift_pp)
    if not math.isfinite(band) or band<0 or not math.isfinite(d):
        raise ValueError('DATA ERROR: invalid drift/band')
    return 'danger' if d>band else 'warn' if d< -band else 'ok'


def tradingbot_tokens(value,tiers):
    """Pure validation of approved TradingBot universe; cannot admit Tier 2."""
    if not isinstance(value,str) or not value.startswith('T1_ONLY:'):
        raise ValueError('DATA ERROR: invalid TradingBot universe')
    result=tuple(x.strip().upper() for x in value.split(':',1)[1].split(','))
    if (len(result)!=5 or len(set(result))!=5 or
        set(result)!={'BTC','ETH','SOL','LINK','HYPE'} or
        any(tiers.get(token)!='T1' for token in result)):
        raise ValueError('DATA ERROR: unapproved TradingBot tokens')
    return result


def _checked(value, label):
    try:
        number=float(value)
    except (TypeError,ValueError) as exc:
        raise ValueError(f'DATA ERROR: {label} is not numeric') from exc
    if not isfinite(number) or number < 0:
        raise ValueError(f'DATA ERROR: {label} is negative/non-finite')
    return number


def sell_capacity_usdt(row):
    """Maximum incremental SELL based on snapshot + SELL reservations.

    Reserved SELL quantities must come from reconciled ledger data. A proposal
    or an unconfirmed LIMIT never creates a reservation or a fill. The Sheets
    reader fails closed for OPEN orders; an omitted reservation defaults to 0
    only while the validated published state declares no active orders.
    """
    token=str(row['token']).upper()
    tier=row.get('tier')
    if tier not in TIER_SELL_FRACTIONS:
        raise ValueError('DATA ERROR: unapproved Tier')
    total=_checked(row['units'],f'{token} total units')
    exchange=_checked(row['exchange_units'],f'{token} Exchange')
    reserved=_checked(row.get('reserved_sell_units',0),f'{token} SELL reserved')
    price=_checked(row['price'],f'{token} Spot price')
    if price <= 0 or exchange > total+_EPS or reserved > exchange+_EPS:
        raise ValueError(f'DATA ERROR: {token} custodias/Spot inconsistentes')
    return (0. if token=='BTC' else
            price*max(0.,min(exchange-reserved,total*TIER_SELL_FRACTIONS[tier]-reserved)))


def overweight_sell_plan(rows, band_pp):
    """Stage-1 proportional target convergence; most OVER first, reevaluate.

    Completely independent of Fibonacci and of a target USDT percentage.
    The output is a *simulation*, NEVER an executable order.
    """
    band=_checked(band_pp,'banda de desviación')
    values=[_checked(r['value'],f"{r['token']} valuation") for r in rows]
    targets=[_checked(r['target'],f"{r['token']} target") for r in rows]
    if abs(sum(targets)-1)>1e-7:
        raise ValueError('DATA ERROR: targets cripto != 100%')
    limits=[sell_capacity_usdt(r) for r in rows]
    used=[0.]*len(rows)
    for _ in range(max(12, len(rows)*8)):
        crypto=sum(values)
        if crypto<=_EPS:break
        candidates=[(100*(values[i]/crypto-targets[i]),i)
                    for i,r in enumerate(rows) if r['token']!='BTC'
                    and targets[i] < 1 and limits[i]-used[i]>_EPS]
        candidates.sort(key=lambda x:(-x[0],x[1]))
        if not candidates or candidates[0][0]<=band+1e-8:break
        _,i=candidates[0]
        amount=min(limits[i]-used[i],
                   max(0.,(values[i]-targets[i]*crypto)/(1-targets[i])))
        if amount<=_EPS:break
        used[i]+=amount
        values[i]-=amount
    return [{'token':r['token'], 'value':used[i],
             'units':used[i]/float(r['price']) if used[i] else 0.,
             'cap_usdt':limits[i], 'weight':r['weight'],
             'target':r['target'],'drift':r['drift_pp']}
            for i,r in enumerate(rows) if r['token']!='BTC'
            and r['drift_pp']>band]


def allocate_infra_buys(rows, budget, band_pp):
    """Balance BUY-only, capped by final token target after *all* simulated BUYs.

    Total allowable B solves B <= sum_i(gap_i + target_i * B), where i
    ranges only over initial INFRA tokens. Unspent budget stays as USDT.
    No prices/pivots are inferred, no orders/fills recorded.
    """
    budget=_checked(budget,'Balancer buy budget')
    band=_checked(band_pp,'banda de desviación')
    crypto=sum(_checked(r['value'],f"{r['token']} valuation") for r in rows)
    if abs(sum(_checked(r['target'],f"{r['token']} target") for r in rows)-1)>1e-7:
        raise ValueError('DATA ERROR: targets cripto != 100%')
    if crypto<=_EPS or budget<=_EPS:return []
    candidates=[]
    for row in rows:
        value=_checked(row['value'],f"{row['token']} valuation")
        target=_checked(row['target'],f"{row['token']} target")
        if target>1 or target<=0:continue
        if 100*(value/crypto-target)<-band-1e-8:
            gap=max(0.,target*crypto-value)
            candidates.append((row,gap,target))
    if not candidates:return []
    total_gap=sum(g for _,g,_ in candidates)
    target_share=sum(t for _,_,t in candidates)
    if total_gap<=_EPS:return []
    maximum=(total_gap/(1-target_share)) if target_share<1-1e-10 else budget
    spend=min(budget,max(0.,maximum))
    # Waterfill while preserving relative initial deficits, cap every asset at
    # its final target calculated on crypto + spend (not the old crypto value).
    allocation=[0.]*len(candidates)
    capacities=[gap+target*spend for _,gap,target in candidates]
    left=spend
    active=list(range(len(candidates)))
    for _ in range(len(candidates)+2):
        if left<=_EPS or not active:break
        weights=sum(candidates[i][1] for i in active)
        if weights<=_EPS:break
        increments={i:left*candidates[i][1]/weights for i in active}
        saturated=[i for i in active if increments[i]>=capacities[i]-allocation[i]-1e-10]
        if not saturated:
            for i in active:allocation[i]+=increments[i]
            left=0.;break
        for i in saturated:
            move=max(0.,capacities[i]-allocation[i])
            allocation[i]+=move;left-=move
        active=[i for i in active if i not in saturated]
    if left>1e-5:
        raise ValueError('DATA ERROR: buy capacity could not be allocated')
    if any(x>capacities[i]+1e-6 for i,x in enumerate(allocation)):
        raise ValueError('DATA ERROR: BUY exceeds target deficit')
    return [{'token':r['token'],'value':allocation[i],
             'reference':0.,'weight':r['weight'],
             'target':r['target'],'drift':r['drift_pp'],
             'final_cap_usdt':capacities[i]}
            for i,(r,_,_) in enumerate(candidates)]


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


def _buy_allocation(items, budget, crypto, drift_band_pp=1.0):
    """Balancer parity: buy INFRA only, never overshoot per-token targets.

    One stage at a time, with the portfolio already marked to the simulated
    stage prices. Unused stage capital remains in USDT, never forced across
    over/neutral assets or structurally blocked tokens.
    """
    n=len(items)
    values=[max(0.,float(x['current_usdt'])) for x in items]
    targets=[max(0.,float(x['target'])) for x in items]
    if crypto<=0 or budget<=0:return [0.]*n
    permitted=[i for i in range(n) if
               targets[i]>0 and (values[i]/crypto-targets[i])*100 < -float(drift_band_pp)-1e-9]
    if not permitted:return [0.]*n
    gaps=[max(0.,targets[i]*crypto-values[i]) if i in permitted else 0. for i in range(n)]
    target_share=sum(targets[i] for i in permitted)
    gap_total=sum(gaps)
    cap=budget if target_share>=1-1e-10 else gap_total/max(1e-12,1-target_share)
    total=min(budget,max(0.,cap))
    rooms=[(gaps[i]+targets[i]*total) if i in permitted else 0. for i in range(n)]
    divisor=sum(rooms)
    return [min(rooms[i],total*rooms[i]/divisor) if divisor>1e-10 else 0. for i in range(n)]


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
        # Parity with o2_sequential.js: an incomplete P1/P2 grid is N/D
        # for all stages, not a partially executable simulated schedule.
        px_all.append(prices if eligible.get(token) is True and all(prices) else [None]*4)
    units=[]; targets=[]
    for t in tokens:
        spot=_finite_pos(t.get('price'))
        current=max(0.,float(t.get('current_usdt') or 0))
        units.append(current/spot if spot else max(0.,float(t.get('units') or 0)))
        targets.append(max(0.,float(t['target'])))

    # All four theoretical budgets total 100% of the slider maximum.
    # This plan does NOT change when a token is blocked or over target.
    budget=max(0.,float(budget))
    target_sum=sum(targets)
    if target_sum<=0:
        return [],budget
    stage_mix=[sum((targets[i]/target_sum)*weights[i][j]
                   for i in range(len(tokens))) for j in range(4)]
    mix_total=sum(stage_mix)
    if abs(mix_total-1)>1e-8:
        raise ValueError('Published tranche weights do not sum to 100%')
    stage_budgets=[budget*stage_mix[j] for j in range(4)]
    stage_budgets[3]=max(0.,budget-sum(stage_budgets[:3]))

    remaining=budget;candidates=[]
    for j in range(4):
        sim_prices=[px_all[i][j] or _finite_pos(t.get('price')) or 0.
                    for i,t in enumerate(tokens)]
        values=[units[i]*sim_prices[i] for i in range(len(tokens))]
        crypto=sum(values)
        planned=min(remaining,stage_budgets[j])
        items=[{'target':targets[i] if px_all[i][j] is not None else 0.,
                'current_usdt':values[i]} for i in range(len(tokens))]
        spends=_buy_allocation(items,planned,crypto,buy.get('drift_band_pp',1.0))
        actually_spent=0.
        for i,t in enumerate(tokens):
            price=px_all[i][j];a=max(0.,spends[i]) if price else 0.
            if not price or a<.005:continue
            token=t['token'];spot=_finite_pos(t.get('price'))
            ctx=buy.get('weekly_context',{}).get(token,{})
            phase=ctx.get('mode') or 'RETROCESO_ALCISTA'
            stage=f"O4C{j+1}" if phase=='O4' else f"O2C{j+1}" if phase=='O2' else f"C{j+1}"
            delta,proximity=_proximity('BUY',spot,price,proximity_pct)
            if token=='HYPE':
                # Never compare Binance HYPE/USDT and Hyperliquid HYPE/USDC.
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


def portfolio_candidates(d, bal, drift_band_pp=1.0):
    """Spot-valued rebalancing suggestions; never fabricate LIMIT levels."""
    by_token={r['token']:r for r in d['rows']};candidates=[]
    # Portfolio Balance is an independent scenario from staged Fibonacci BUYs.
    # Sizing must nevertheless honor each approved target and INFRA band.
    holdings={token:max(0.,float(row.get('value') or 0)) for token,row in by_token.items()}
    crypto=sum(holdings.values())
    for side,items in (('BUY',bal.get('buys',[])),('SELL',bal.get('sells',[]))):
        for suggestion in items:
            token=suggestion['token']
            if token not in by_token or (side=='SELL' and token=='BTC'):continue
            row=by_token[token];spot=_finite_pos(row.get('price'))
            if not spot:continue
            amount=max(0.,float(suggestion.get('value') or 0))
            if side=='SELL':
                cap_usdt=sell_capacity_usdt(row)
                amount=min(amount,cap_usdt)
                units=amount/spot
                if amount<.005:continue
            else:
                # Fail closed on missing numeric inventory/targets. Balancer
                # previews are not permission to spend past a token's target.
                target=_finite_pos(row.get('target'))
                value=holdings[token]
                if target is None or target>=1 or crypto<=0:
                    continue
                if (value/crypto-target)*100 >= -float(drift_band_pp)-1e-9:
                    continue  # Only INFRA at THIS step may receive BUY.
                headroom=max(0.,(target*crypto-value)/(1-target))
                amount=min(amount,headroom)
                if amount<.005:continue
                units=amount/spot
                holdings[token]+=amount
                crypto+=amount
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
    portfolio=portfolio_candidates(d,balancer_payload,buy_payload.get('drift_band_pp',1.0))
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
                         # The amount/units MUST come from the same proposal as
                         # the selected level. Never attach Balancer SELL units
                         # to an independently sized Fibonacci extension.
                         'buy_usdt':(picked['usdt'] if picked and picked['side']=='BUY' and
                                     picked['usdt'] is not None and picked['usdt']>.005 else None),
                         'sell_units':(picked['quantity'] if picked and picked['side']=='SELL' and
                                        picked['quantity'] is not None and picked['quantity']>0 else None),
                         'sizing_status':picked['sizing_status'] if picked else 'N/D',
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
