"""Kairos v2.0.40 shared, fail-closed cash envelopes (simulations only).

QF belongs to physical USDT exactly once. The Balancer allocation is derived
from the APPROVED percentage of TOTAL physical USDT (including QF once), but it
must fit within the non-QF balance. The remaining non-QF cash funds O2/O4 first.
Hypothetical SELL proceeds never increase real cash; they may be displayed only
in an explicitly conditional plan. No physical transfer is implied.
"""
from __future__ import annotations
import math

class LiquidityPolicyError(ValueError): pass


def liquidity_by_venue(venues, physical_total):
    """Venue view of the SAME physical cash; never add this to category totals."""
    if not isinstance(venues,dict):raise LiquidityPolicyError('Liquidez por venue no disponible')
    total=_amount(physical_total,'USDT físico')
    amounts={name:_amount(value,'USDT '+str(name)) for name,value in venues.items()}
    if not math.isclose(sum(amounts.values()),total,rel_tol=1e-10,abs_tol=1e-7):
        raise LiquidityPolicyError('Liquidez por venue no concilia con el total físico')
    colors={'Binance':'#7bbce8','KuCoin':'#16ab89','Hyperliquid':'#a58be6',
            'Quantfury':'#efa53f','MEXC':'#ec8493','Metamask':'#a7bd71','Phantom':'#7794bb'}
    fallback=('#7bbce8','#16ab89','#a58be6','#efa53f','#ec8493','#a7bd71','#7794bb')
    records=[];start=0.
    positive=sorted(((name,value) for name,value in amounts.items() if value>0),key=lambda x:(-x[1],x[0]))
    for i,(name,value) in enumerate(positive):
        pct=100*value/total
        end=100. if i==len(positive)-1 else start+pct
        records.append({'venue':name,'amount':value,'pct':pct,'start':start,'end':end,
                        'color':colors.get(name,fallback[i%len(fallback)])})
        start=end
    return {'total':total,'records':records}


def liquidity_allocation(physical_usdt, qf_usdt, balancer_assigned):
    """Three disjoint REAL cash envelopes; assignment is not extra liquidity."""
    total=_amount(physical_usdt,'USDT físico')
    trading=_amount(qf_usdt,'Trading real')
    balancer=_amount(balancer_assigned,'Balancer asignado')
    weekly=total-trading-balancer
    if weekly < -1e-8:
        raise LiquidityPolicyError('Reservas Trading + Balancer exceden la liquidez física')
    weekly=max(0.,weekly)
    result={'total':total,'weekly':weekly,'balancer':balancer,'trading':trading}
    if not math.isclose(sum(result[k] for k in ('weekly','balancer','trading')),total,abs_tol=1e-8):
        raise LiquidityPolicyError('Las tres categorías no concilian con liquidez total')
    for k in ('weekly','balancer','trading'):
        result[k+'_pct']=100*result[k]/total if total else 0.
    return result


def _amount(x, name):
    if type(x) not in (int,float) or not math.isfinite(x) or x < 0:
        raise LiquidityPolicyError(name+': valor negativo, no numérico o no finito')
    return float(x)


def calculate_budgets(physical_usdt, qf_usdt, *, balancer_allocated=None,
                      buy_commitments=0., balancer_commitments=0.,
                      conditional_sell_proceeds=0.):
    """No transfers, orders, or implied fills. All amounts in USDT."""
    physical=_amount(physical_usdt,'USDT físico')
    qf=_amount(qf_usdt,'Reserva QF')
    if qf>physical+1e-8:
        raise LiquidityPolicyError('QF supera el USDT físico')
    commitments=_amount(buy_commitments,'Compromisos BUY')
    bal_commit=_amount(balancer_commitments,'Compromisos Balancer')
    conditional=_amount(conditional_sell_proceeds,'Ventas hipotéticas')
    operating=max(0.,physical-qf)
    if commitments>operating+1e-8:
        raise LiquidityPolicyError('Compromisos BUY exceden USDT fuera de QF')
    free= max(0.,operating-commitments)
    if balancer_allocated is None:
        # There is no certified Balancer reserve in the public Master yet.
        bal=0.
        status='PENDIENTE_ASIGNACION'
    else:
        allocated=_amount(balancer_allocated,'Reserva Balancer asignada')
        if allocated>operating+1e-8:
            raise LiquidityPolicyError('Reserva Balancer asignada supera USDT no QF')
        if bal_commit>allocated+1e-8:
            raise LiquidityPolicyError('Compromisos Balancer exceden la reserva')
        # If an order was already included in total buy commitments, subtract
        # only once from global available funds.
        bal=min(max(0.,allocated-bal_commit),free)
        status='ASIGNACION_PUBLICADA'
    weekly=max(0.,free-bal)
    return {'status':status,'usdt_physical':physical,'qf_protected':qf,
            'usdt_non_qf':operating,'buy_commitments':commitments,
            'weekly_uncommitted':weekly,'balancer_uncommitted':bal,
            'compras_max':free,'balancer_max':bal,
            'balancer_with_sales_conditional':bal+conditional,
            'conditional_sell_proceeds':conditional,
            'balancer_allocated':balancer_allocated,
            'unallocated_cash':weekly if status=='PENDIENTE_ASIGNACION' else 0.}


def derive_balancer_allocation(physical_usdt, qf_usdt, fraction):
    """Actual USD allocation = fraction of ALL physical USDT, NOT of non-QF cash.

    Reject plans that would need to consume physical QF. The calculation is
    rounded to cents, never counted as new money, and recomputed on each read.
    """
    from decimal import Decimal, ROUND_HALF_UP
    physical=_amount(physical_usdt,'USDT físico')
    qf=_amount(qf_usdt,'Reserva QF')
    if qf>physical+1e-8:
        raise LiquidityPolicyError('QF supera el USDT físico')
    if type(fraction) not in (int,float) or not math.isfinite(fraction) or not 0<=fraction<=1:
        raise LiquidityPolicyError('Porcentaje Balancer inválido')
    value=float((Decimal(str(physical))*Decimal(str(fraction))).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
    if value>physical-qf+1e-8:
        raise LiquidityPolicyError('Reserva Balancer objetivo invade QF; revisar reparto publicado')
    return value


def allocation_from_master(parameters, physical_usdt=None, qf_usdt=None, *, portfolio_total=None):
    """Prefer the authoritative approved 70/20/10 percentage over legacy USD.

    If liquidity mix exists but is incomplete or not approved, fail closed.
    Legacy explicitly approved allocations remain compatible for older Sheets.
    """
    keys=('PORTFOLIO_LIQ_USDT_FRACTION','PORTFOLIO_LIQ_BALANCER_FRACTION','PORTFOLIO_LIQ_TRADING_FRACTION')
    records=[parameters.get(key) for key in keys]
    if any(r is not None for r in records):
        if any(not isinstance(r,dict) or r.get('status')!='APROBADO' for r in records):
            return None
        values=[]
        for key,r in zip(keys,records):
            v=r.get('value')
            if type(v) not in (int,float) or not math.isfinite(v) or v<0 or v>1:
                raise LiquidityPolicyError(key+': porcentaje inválido')
            values.append(v)
        if abs(sum(values)-1)>1e-8:
            raise LiquidityPolicyError('Reparto publicado de liquidez debe sumar 100%')
        if physical_usdt is None or qf_usdt is None:
            # Missing cash readings must never produce an operational allocation.
            return None
        caps=reserve_caps_from_master(parameters)
        if caps is not None:
            if portfolio_total is None:
                raise LiquidityPolicyError('Topes de reservas requieren valoración Spot vigente')
            p=_amount(portfolio_total,'Valor del portafolio Spot')
            if p < physical_usdt or p <= 0:
                raise LiquidityPolicyError('Valor del portafolio menor que liquidez física')
            # Round DOWN: cent rounding must never breach a hard maximum.
            from decimal import Decimal, ROUND_DOWN
            cap=Decimal(str(p))*Decimal(str(caps['balancer']))
            base=Decimal(str(physical_usdt))*Decimal(str(values[1]))
            available=Decimal(str(physical_usdt))-Decimal(str(qf_usdt))
            return float(min(base,cap,available).quantize(Decimal('0.01'),rounding=ROUND_DOWN))
        return derive_balancer_allocation(physical_usdt,qf_usdt,values[1])
    record=parameters.get('BALANCER_RESERVE_ASSIGNED_USDT')
    if not isinstance(record,dict) or record.get('status')!='APROBADO':
        return None
    return _amount(record.get('value'),'BALANCER_RESERVE_ASSIGNED_USDT')


def reserve_caps_from_master(parameters):
    """Caps are configuration, not physical transfers; require both approvals."""
    keys={'balancer':'BALANCER_MAX_PORTFOLIO_FRACTION',
          'trading':'TRADING_MAX_PORTFOLIO_FRACTION'}
    if not any(key in parameters for key in keys.values()):
        return None  # Compatibility with older published Masters.
    caps={}
    for name,key in keys.items():
        record=parameters.get(key)
        if not isinstance(record,dict) or record.get('status')!='APROBADO':
            raise LiquidityPolicyError(key+': tope incompleto o no aprobado')
        v=_amount(record.get('value'),key)
        if v>1:raise LiquidityPolicyError(key+': máximo 100%')
        caps[name]=v
    return caps


def budgets_from_master(parameters, physical_usdt, qf_usdt, portfolio_total, **kwargs):
    """Single runtime entry point: live Spot P, immutable actual QF, capped targets."""
    caps=reserve_caps_from_master(parameters)
    allocation=allocation_from_master(parameters,physical_usdt,qf_usdt,
                                      portfolio_total=portfolio_total)
    result=calculate_budgets(physical_usdt,qf_usdt,balancer_allocated=allocation,**kwargs)
    # Evaluate the NORMAL envelope, before releasing Balancer, so the rule
    # cannot oscillate on successive reads. Confirmed commitments stay deducted.
    threshold=balancer_purchase_threshold(parameters)
    p=_amount(portfolio_total,'Valor del portafolio Spot')
    if p<=0 or p<physical_usdt:raise LiquidityPolicyError('Portafolio Spot inválido')
    baseline=result['weekly_uncommitted']
    from decimal import Decimal
    disabled=Decimal(str(baseline)) < Decimal(str(p))*Decimal(str(threshold))
    result['balancer_liquidity_guard']={'threshold_fraction':threshold,
        'baseline_o2_o4_usdt':baseline,'baseline_o2_o4_fraction':baseline/p,
        'disabled':disabled,'reason':'O2_O4_BELOW_THRESHOLD' if disabled else 'THRESHOLD_MET'}
    if disabled:
        released=result['balancer_uncommitted']
        result.update(balancer_allocated=0.,balancer_uncommitted=0.,balancer_max=0.,
                      weekly_uncommitted=baseline+released,
                      balancer_with_sales_conditional=result['conditional_sell_proceeds'])
    if caps is None:
        result['reserve_caps']=None
        return result
    p=_amount(portfolio_total,'Valor del portafolio Spot')
    fraction=parameters.get('PORTFOLIO_LIQ_TRADING_FRACTION',{})
    if fraction.get('status')!='APROBADO':
        raise LiquidityPolicyError('Porcentaje Trading no aprobado')
    trading_fraction=_amount(fraction.get('value'),'Porcentaje Trading')
    if trading_fraction>1:raise LiquidityPolicyError('Porcentaje Trading inválido')
    from decimal import Decimal, ROUND_DOWN
    money=lambda x:float(Decimal(str(x)).quantize(Decimal('0.01'),rounding=ROUND_DOWN))
    bal_cap=money(Decimal(str(p))*Decimal(str(caps['balancer'])))
    trading_cap=money(Decimal(str(p))*Decimal(str(caps['trading'])))
    trading_base=money(Decimal(str(physical_usdt))*Decimal(str(trading_fraction)))
    target=min(trading_base,trading_cap)
    result['reserve_caps']={
        'portfolio_total':p,'balancer_fraction':caps['balancer'],
        'trading_fraction':caps['trading'],'balancer_cap_usdt':bal_cap,
        'trading_cap_usdt':trading_cap,'trading_base_usdt':trading_base,
        'trading_target_usdt':target,'trading_actual_usdt':qf_usdt,
        'trading_excess_over_cap':max(0.,qf_usdt-trading_cap),
        'trading_excess_over_target':max(0.,qf_usdt-target),
    }
    # Cap the initial reserve only. Recycling sale proceeds is conditional
    # and must not be erased by the reserve floor or counted as real cash.
    result['balancer_with_sales_conditional']=min(
        result['balancer_uncommitted'],
        max(0.,bal_cap-_amount(kwargs.get('balancer_commitments',0.),'Compromisos Balancer'))) + result['conditional_sell_proceeds']
    return result


BALANCER_O2_O4_MIN_KEY = 'BALANCER_MIN_O2_O4_PORTFOLIO_FRACTION'

def balancer_purchase_threshold(parameters):
    """Default explicitly approved by user; a present invalid row fails closed."""
    record=parameters.get(BALANCER_O2_O4_MIN_KEY)
    if record is None:return 0.10
    if not isinstance(record,dict) or record.get('status')!='APROBADO':
        raise LiquidityPolicyError('Umbral Balancer no aprobado')
    value=_amount(record.get('value'),'Umbral mínimo O2/O4')
    if value>1:raise LiquidityPolicyError('Umbral mínimo O2/O4: máximo 100%')
    return value
