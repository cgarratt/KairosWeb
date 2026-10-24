"""Kairos v2.0.40 shared, fail-closed cash envelopes (simulations only).

QF belongs to physical USDT exactly once. The management percentages in
12_PARAMETROS_KAIROS are *targets*, not evidence of assigned cash. Therefore a
Balancer BUY envelope exists only when an approved explicit amount is published.
A pending/unknown allocation blocks Balancer cash-funded purchases while O2/O4
may still use all uncommitted non-QF cash. Hypothetical SELL proceeds never
increase real cash; they may be displayed only in an explicitly conditional plan.
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


def allocation_from_master(parameters):
    """Return confirmed Balancer reserve only; never infer it from target %."""
    record=parameters.get('BALANCER_RESERVE_ASSIGNED_USDT')
    if not isinstance(record,dict) or record.get('status')!='APROBADO':
        return None
    return _amount(record.get('value'),'BALANCER_RESERVE_ASSIGNED_USDT')
