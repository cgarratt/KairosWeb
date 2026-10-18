"""Kairos LONG-TERM COMPRAS eligibility, shared with KairosGPT.

Only the two most recent, *published VALIDADO/CONFIRMADO* closed-week pivots may
supply an upward impulse.  No daily maxima, O2 legacy inverse Fibonacci or
unvalidated Elliott guesses.  Pure function: no MCP calls or Sheet writes.

This is deliberately NOT a restriction on ordinary VENTAS or on explicitly
hypothetical FORECAST scenarios.
"""
from __future__ import annotations
from datetime import date
from math import isclose
from wave_structure import BUY_RATIOS, iso_date, fib_grid, positive


class BuyEligibilityError(ValueError):
    pass


def _pivot_indices(weeks, direction, left=5, right=5):
    field='high' if direction=='high' else 'low'
    indices=[]
    for i in range(left, len(weeks)-right):
        value=float(weeks[i][field]); neighbors=weeks[i-left:i]+weeks[i+1:i+right+1]
        if all(value>float(w[field]) for w in neighbors) if direction=='high' else all(value<float(w[field]) for w in neighbors):
            indices.append(i)
    return indices


def _observed_bull_bos(weeks, low_idx, high_idx, highs, right=5):
    """A bullish weekly close must break the latest older protected high.

    The high and low pivots each require their own 5L/5R confirmation, and
    the BOS cannot be credited until 5R confirms the swing low.
    """
    previous=[j for j in highs if j+right < low_idx]
    if not previous:return None
    protected=weeks[previous[-1]]
    for w in weeks[low_idx+right+1:]:
        if float(w['close']) > float(protected['high']):
            return {'protected_high':float(protected['high']),
                    'protected_week':protected['week_start'],
                    'bos_week':w['week_start'],'bos_close':float(w['close'])}
    return None


def _anchor_match(published, low, high, *, tol=1e-5):
    """Identify O2/O4 only when BOTH published wave dates/prices coincide.

    A lone label must never invent an Elliott classification.
    """
    published=published or {}
    waves=published.get('waves') or {}
    names={'O2':(published.get('cycle_low'),published.get('cl_date'),waves.get('o1') or {}),
           'O4':((waves.get('o2') or {}).get('price'),(waves.get('o2') or {}).get('date'),waves.get('o3') or {})}
    for label,(lo,lo_date,hi) in names.items():
        try:
            if (str(lo_date)[:10]==low['date'] and str(hi.get('date'))[:10]==high['date']
                and isclose(float(lo),low['price'],rel_tol=tol)
                and isclose(float(hi.get('price')),high['price'],rel_tol=tol)):
                return label
        except (TypeError,ValueError):pass
    return 'RETROCESO_ALCISTA'



def _approved_extreme(published, kind, anchor, *, tolerance=1e-5):
    """Gate Compras on PUBLISHED 07_PIVOTES state, not fresh MCP proposals."""
    published=published or {}
    items=[]
    if kind=='LOW' and published.get('cycle_low') is not None:
        items.append(('CL',published.get('cycle_low'),published.get('cl_date'),published.get('cl_status','PROPUESTO')))
    for name,rec in (published.get('waves') or {}).items():
        if name.lower() not in (('o2','o4') if kind=='LOW' else ('o1','o3','o5')):continue
        items.append((name.upper(),rec.get('price'),rec.get('date'),rec.get('status','PROPUESTO')))
    matching=[]
    for name,price,when,status in items:
        if not when or price is None:continue
        try:
            if str(when)[:10]==anchor['date'] and isclose(float(price),float(anchor['price']),rel_tol=tolerance):
                matching.append({'pivot':name,'status':{'ESTIMADO':'PROPUESTO','CANDIDATO':'PROPUESTO','VALIDADO_TECNICAMENTE':'VALIDADO'}.get(str(status).upper(),str(status).upper())})
        except (TypeError,ValueError):continue
    approved=next((x for x in matching if x['status'] in ('VALIDADO','CONFIRMADO')),None)
    return approved,matching

def select_buy_impulse(weeks, published=None, *, left=5, right=5):
    """Return an eligible latest bullish impulse or a detailed blocked status.

    Source `weeks`: complete UTC Monday-to-Sunday *closed* Spot weeks from
    `full_utc_weeks` after venue verification. Confirmed published pivots are
    never overwritten: a conflicting newer structure blocks until reviewed.
    """
    def blocked(reason, **extra):
        result=dict(status='BLOQUEADO',eligible=False,reason=reason,mode=None,levels=None,anchors=None)
        result.update(extra)
        return result
    if not isinstance(weeks,list) or len(weeks)<2*(left+right)+2:
        return blocked('HISTORICO_SEMANAL_INSUFICIENTE')
    try:
        if any(iso_date(w['week_start'],'week')>=iso_date(w['week_end'],'week end') for w in weeks):
            return blocked('SEMANA_INVALIDA')
        if any(weeks[i]['week_start']>=weeks[i+1]['week_start'] for i in range(len(weeks)-1)):
            return blocked('SECUENCIA_SEMANAL_INVALIDA')
        lows=_pivot_indices(weeks,'low',left,right)
        highs=_pivot_indices(weeks,'high',left,right)
        swings=sorted([(i,'LOW') for i in lows]+[(i,'HIGH') for i in highs])
        if len(swings)<2:return blocked('DOS_PIVOTES_5L5R_AUSENTES')
        (li,lk),(hi,hk)=swings[-2:]
        if lk!='LOW' or hk!='HIGH' or li>=hi:return blocked('ULTIMOS_PIVOTES_NO_ALCISTAS',last_types=[lk,hk])
        low={'price':positive(weeks[li]['low'],'low'),'date':weeks[li]['low_date'],
             'week_start':weeks[li]['week_start']}
        high={'price':positive(weeks[hi]['high'],'high'),'date':weeks[hi]['high_date'],
              'week_start':weeks[hi]['week_start']}
        if high['price']<=low['price'] or iso_date(high['date'],'high')<=iso_date(low['date'],'low'):
            return blocked('IMPULSO_INVALIDO')
        bos=_observed_bull_bos(weeks,li,hi,highs,right)
        if not bos:return blocked('BOS_ALCISTA_SEMANAL_PENDIENTE',anchors={'low':low,'high':high})
        # A confirmed older pivot remains immutable, but may legitimately be
        # followed by a NEW weekly impulse. Never replace it; reject only a
        # same-date contradictory value, not every newer pivot.
        published=published or {};waves=published.get('waves') or {}
        locked=[]
        if str(published.get('cl_status')).upper()=='CONFIRMADO' and published.get('cycle_low'):
            locked.append(('CL',published.get('cycle_low'),published.get('cl_date')))
        for name in ('o1','o2','o3'):
            rec=waves.get(name) or {}
            if rec.get('status')=='CONFIRMADO' and rec.get('price') and rec.get('date'):
                locked.append((name.upper(),rec['price'],rec['date']))
        for name,price,dt in locked:
            matched=low if name in ('CL','O2') else high
            if str(dt)[:10]==matched['date'] and not isclose(float(price),matched['price'],rel_tol=1e-5):
                return blocked('ANCLA_CONFIRMADA_EN_CONFLICTO',confirmed=name,
                               anchors={'low':low,'high':high})
        low_ok,low_states=_approved_extreme(published,'LOW',low)
        high_ok,high_states=_approved_extreme(published,'HIGH',high)
        if not low_ok or not high_ok:
            return blocked('EXTREMOS_NO_VALIDADOS_EN_MASTER',
                           anchors={'low':low,'high':high},
                           low_state=low_ok or low_states or [{'status':'PROPUESTO'}],
                           high_state=high_ok or high_states or [{'status':'PROPUESTO'}])
        mode=_anchor_match(published,low,high)
        levels=fib_grid('O2',{'CL':low['price'],'O1':high['price']})
        return {'status':'VALIDADO_TECNICAMENTE_NO_OPERATIVO','eligible':True,
                'reason':'PAREJA_SEMANAL_ALCISTA_5L5R_BOS', 'mode':mode,
                'anchors':{'low':low,'high':high},'bos':bos,
                'levels':dict(zip(('ref382','c1','c2','ref786'),levels.values())),
                'pivot_authority':{'low':low_ok,'high':high_ok},
                'requires_explicit_user_trade_approval':True}
    except (ValueError,TypeError,KeyError) as exc:
        return blocked('ESTRUCTURA_INVALIDA',detail=str(exc)[:140])
