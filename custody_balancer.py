"""Kairos Balancer custody comparison (read-only, no custody movements).

Input MUST be the already validated, PUBLICADO Google Sheets positions and 04_CUSTODIA
policy. No price, screenshots, stored ZIP data, fills or custody updates are inferred.
Only proposed Exchange -> HODL / Exchange -> Core transfers are permitted; custody
already protected in HODL/Core never flows back to Exchange or between protected pools.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, InvalidOperation
from typing import Mapping, Any

LABELS = ("hodl", "core", "exchange")
DUST = Decimal("0.00000001")


class CustodyError(ValueError):
    """No certified custody calculation is available."""


def _decimal(v: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CustodyError(f"{name}: dato no numérico") from exc
    if not result.is_finite() or result < 0:
        raise CustodyError(f"{name}: dato negativo/no finito")
    return result


def _fmt(value: Decimal) -> str:
    return format(value.normalize(), "f") if value else "0"


def _qty(value: Decimal) -> Decimal:
    """Never propose more Exchange units than physically held; floor 8 decimals."""
    return value.quantize(DUST, rounding=ROUND_DOWN)


def compare_custody(positions: Mapping[str, Mapping[str, Any]],
                    custody_policy: Mapping[str, Mapping[str, Any]],
                    *, reserved_exchange: Mapping[str, Any] | None = None) -> dict:
    """Compute nominal targets, feasible post-transfer holdings and exact transfer units.

    Current holdings remain intact. The feasible result is monotone: only *unreserved*
    Exchange units exceeding the tier's nominal Exchange target may be transferred.
    When full nominal allocation is impossible without withdrawing protected funds,
    the gap is displayed rather than fabricating a reverse Ledger transfer.
    ``reserved_exchange`` is reserved SELL quantity by token, from reconciled orders.
    """
    if not positions or not custody_policy:
        raise CustodyError("02_POSICIONES / 04_CUSTODIA no disponibles")
    reservations = reserved_exchange or {}
    rows=[]
    motions=[]
    for token, row in positions.items():
        tier = str(row.get('tier',''))
        if tier not in custody_policy:
            raise CustodyError(f'{token}: Tier sin configuración publicada')
        policy = custody_policy[tier]
        # The PUBLICADO Master adapter (google_sheets_master.parse_master) returns
        # custody ratios as a three-element [HODL, Core, Exchange] list. Earlier
        # standalone tests supplied a dict, which hid a production MODE_RENDER.
        # Accept both published list shape and named mapping; reject everything else.
        if isinstance(policy, (list, tuple)):
            if len(policy) != len(LABELS):
                raise CustodyError(f'{tier}: se requieren HODL/Core/Exchange')
            policy = dict(zip(LABELS, policy))
        elif not isinstance(policy, Mapping):
            raise CustodyError(f'{tier}: distribución no reconocida')
        ratios={key:_decimal(policy.get(key),f'{tier}.{key}') for key in LABELS}
        if sum(ratios.values()) != 1:
            raise CustodyError(f'{tier}: distribución publicada debe sumar 100%')
        actual={key:_decimal(row.get(key),f'{token}.{key}') for key in LABELS}
        total=sum(actual.values())
        if 'units' in row and abs(total-_decimal(row['units'],f'{token}.units'))>DUST:
            raise CustodyError(f'{token}: descalce inventario HODL+Core+Exchange')
        reserved=_decimal(reservations.get(token,0),f'{token}.reserved_sell')
        if reserved>actual['exchange']:
            raise CustodyError(f'{token}: SELL reservado excede unidades Exchange')
        nominal={key:total*ratios[key] for key in LABELS}
        # Structural Exchange surplus must be the source of any proposal.
        excess=max(Decimal(0),actual['exchange']-nominal['exchange'])
        excess=min(excess,actual['exchange']-reserved)
        excess=_qty(excess)
        suggested=dict(actual)
        token_moves=[]
        # Stable deterministic order: fill permanent HODL first, then strategic Core;
        # no intermediate movements between protected categories.
        for target in ('hodl','core'):
            deficit=max(Decimal(0),nominal[target]-suggested[target])
            move=_qty(min(deficit,excess))
            if move>0:
                suggested['exchange']-=move
                suggested[target]+=move
                excess-=move
                token_moves.append({'token':token,'tier':tier,'source':'Exchange',
                    'destination':'HODL' if target=='hodl' else 'Core',
                    'units':_fmt(move), 'status':'PROPUESTA_SIN_TRANSFERENCIA'})
        if sum(suggested.values())!=total:
            raise CustodyError(f'{token}: se perdió conservación de unidades')
        if suggested['exchange'] < reserved:
            raise CustodyError(f'{token}: propuesta consume unidades reservadas SELL')
        diff_nominal={key:nominal[key]-suggested[key] for key in LABELS}
        reachable=all(abs(nominal[k]-suggested[k])<=DUST for k in LABELS)
        rows.append({
            'token':token,'tier':tier,'total_units':_fmt(total),
            'current':{k:_fmt(actual[k]) for k in LABELS},
            'ideal_nominal':{k:_fmt(nominal[k]) for k in LABELS},
            'ideal_feasible':{k:_fmt(suggested[k]) for k in LABELS},
            'policy_pct':{k:float(ratios[k]*100) for k in LABELS},
            'current_pct':{k:float(actual[k]/total*100) if total else 0 for k in LABELS},
            'feasible_pct':{k:float(suggested[k]/total*100) if total else 0 for k in LABELS},
            'gap_units_to_nominal':{k:_fmt(diff_nominal[k]) for k in LABELS},
            'nominal_reachable':reachable,
            'reserved_sell_exchange':_fmt(reserved),
            'transfer_count':len(token_moves),
            'status':('OBJETIVO_ALCANZABLE' if reachable else
                      'PARCIAL_SIN_RETIRAR_PROTEGIDAS' if token_moves else 'SIN_TRANSFERENCIA_SEGURA'),
        })
        motions.extend(token_moves)
    if set(reservations) - set(positions):
        raise CustodyError('Reserva SELL refiere a token inexistente')
    return {'status':'SIMULACION_NO_EJECUTADA','basis':'UNIDADES_PUBLICADAS',
            'rows':rows,'transfers':motions,'transfer_count':len(motions),
            'tokens_with_moves':sum(bool(r['transfer_count']) for r in rows),
            'nominal_unreachable':sum(not r['nominal_reachable'] for r in rows),
            'notes':('No transferencias automáticas. HODL/Core nunca salen de custodia protegida.',
                     'Ideal nominal por Tier y resultado alcanzable sin transferencias inversas se muestran por separado.',
                     'Transferir requiere confirmación real del usuario y nuevo snapshot publicado.')}


def compare_master_custody(master: Mapping[str, Any], *, reserved_exchange=None) -> dict:
    """KairosGPT adapter: only validated master payload, no stale fallback."""
    if master.get('status','').startswith('PASS_SNAPSHOT') is False:
        raise CustodyError('MASTER no validado/publicado')
    result=compare_custody(master['positions'],master['custody_policy'],reserved_exchange=reserved_exchange)
    result['snapshot_id']=master['snapshot_id']
    result['snapshot_cutoff']=master['snapshot_cutoff']
    return result
