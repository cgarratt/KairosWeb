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


def allocation_from_master(parameters, physical_usdt=None, qf_usdt=None):
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
        return derive_balancer_allocation(physical_usdt,qf_usdt,values[1])
    record=parameters.get('BALANCER_RESERVE_ASSIGNED_USDT')
    if not isinstance(record,dict) or record.get('status')!='APROBADO':
        return None
    return _amount(record.get('value'),'BALANCER_RESERVE_ASSIGNED_USDT')
