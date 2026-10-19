"""Kairos LONG-TERM COMPRAS eligibility, shared with KairosGPT.

The two latest weekly anchors, including published or MCP PROPUESTO candidates,
may supply a SIMULATION. Only independently approved pivots enable operations.  No daily maxima, O2 legacy inverse Fibonacci or
unvalidated Elliott guesses.  Pure function: no MCP calls or Sheet writes.

This is deliberately NOT a restriction on ordinary VENTAS or on explicitly
hypothetical FORECAST scenarios.
"""
from __future__ import annotations
from datetime import date
from math import isclose
from wave_structure import BUY_RATIOS, iso_date, fib_grid, positive, weekly_o1_candidate


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
    approved=next((x for x in matching if x['status'] in ('VALIDADO','CONFIRMADO')),None) or next((x for x in matching if x['status']=='PROPUESTO'),None)
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
            return blocked('EXTREMOS_ND_EN_MASTER',
                           anchors={'low':low,'high':high},
                           low_state=low_ok or low_states or [{'status':'PROPUESTO'}],
                           high_state=high_ok or high_states or [{'status':'PROPUESTO'}])
        mode=_anchor_match(published,low,high)
        levels=fib_grid('O2',{'CL':low['price'],'O1':high['price']})
        provisional=any(p['status']=='PROPUESTO' for p in (low_ok,high_ok))
        return {'status':'PROPUESTO_SIMULACION' if provisional else 'VALIDADO_TECNICAMENTE_NO_OPERATIVO',
                'eligible':True,'simulation_only':True,'operational_blocked':provisional,
                'reason':'PAREJA_SEMANAL_ALCISTA_5L5R_BOS', 'mode':mode,
                'anchors':{'low':low,'high':high},'bos':bos,
                'levels':dict(zip(('ref382','c1','c2','ref786'),levels.values())),
                'pivot_authority':{'low':low_ok,'high':high_ok},
                'requires_explicit_user_trade_approval':True}
    except (ValueError,TypeError,KeyError) as exc:
        return blocked('ESTRUCTURA_INVALIDA',detail=str(exc)[:140])



def select_p1_p2_buy_impulse(weeks, published=None, archived=None):
    """Simulación: último P1 semanal documentado, incluso PROPUESTO;
    P2 es el mayor HIGH de semanas UTC completas posteriores a P1.

    Nunca inferir un P1 a partir de precios Fibo ni de Spot. Un CL/MIN
    archivado solo es PROPUESTO, sin certificación implícita. No escribe Master
    ni hace operativa una compra. Los pivotes CONFIRMADO son inmutables.
    """
    def deny(reason, **details):
        return {'eligible':False,'status':'BLOQUEADO','reason':reason,
                'anchors':None,'levels':None,'mode':None,**details}
    published=published or {};archived=archived or {}
    if not weeks:return deny('HISTORICO_SEMANAL_INSUFICIENTE')
    try:
        if any(iso_date(w['week_start'],'week')>=iso_date(w['week_end'],'end') for w in weeks):
            return deny('SEMANA_INVALIDA')
        if any(weeks[i]['week_start']>=weeks[i+1]['week_start'] for i in range(len(weeks)-1)):
            return deny('SECUENCIA_SEMANAL_INVALIDA')
        possible=[]
        states={'ESTIMADO':'PROPUESTO','CANDIDATO':'PROPUESTO',
                'VALIDADO_TECNICAMENTE':'VALIDADO'}
        def add_p1(name, price, day, status, source):
            if price is None or not day:return
            try:
                st=states.get(str(status or 'PROPUESTO').upper(),str(status or 'PROPUESTO').upper())
                if st not in ('PROPUESTO','VALIDADO','CONFIRMADO'):return
                possible.append({'pivot':name,'price':positive(price,name),
                    'date':iso_date(day,name).isoformat(),'status':st,'source':source})
            except (ValueError,TypeError):pass
        # The published CL takes priority; a dated MCP archive CL is proposed
        # only if the published record does not already contain that CL.
        if published.get('cycle_low') is not None or published.get('cl_date'):
            add_p1('CL',published.get('cycle_low'),published.get('cl_date'),
                   published.get('cl_status','PROPUESTO'),'07_PIVOTES_PUBLICADO')
        else:
            add_p1('CL',archived.get('cycle_low'),archived.get('cl_date'),
                   'PROPUESTO','MCP_ARCHIVE_PROPUESTO')
        for key in ('o2','o4'):
            rec=(published.get('waves') or {}).get(key) or {}
            add_p1(key.upper(),rec.get('price'),rec.get('date'),rec.get('status'),
                   '07_PIVOTES_PUBLICADO')
        if not possible:return deny('P1_ND')
        p1=max(possible,key=lambda x:x['date'])
        located=next((i for i,w in enumerate(weeks)
            if w['week_start']<=p1['date']<=w['week_end']),None)
        if located is None:return deny('P1_FUERA_DE_HISTORICO_1W',p1=p1)
        w1=weeks[located]
        if not isclose(float(w1['low']),p1['price'],rel_tol=1e-5,abs_tol=1e-12):
            return deny('P1_NO_COINCIDE_MINIMO_SEMANAL',p1=p1,observed_weekly_low=w1['low'])
        later=[w for w in weeks[located+1:] if float(w['high'])>p1['price']]
        if not later:return deny('P2_MAXIMO_POSTERIOR_ND',p1=p1)
        best=max(later,key=lambda w:(float(w['high']),w['week_start']))
        p2={'pivot':'P2','price':positive(best['high'],'P2'),
            'date':iso_date(best['high_date'],'P2').isoformat(),
            'week_start':best['week_start'],'status':'PROPUESTO',
            'source':'MCP_SEMANAL_CERRADO'}
        if p2['date']<=p1['date']:return deny('P2_NO_POSTERIOR_A_P1')
        for key in ('o1','o3','o5'):
            rec=(published.get('waves') or {}).get(key) or {}
            if not rec.get('date') or rec.get('price') is None:continue
            if str(rec['date'])[:10]!=p2['date']:continue
            if str(rec.get('status')).upper()=='CONFIRMADO' and not isclose(float(rec['price']),p2['price'],rel_tol=1e-5):
                return deny('P2_CONFLICTO_CON_CONFIRMADO',p1=p1,p2=p2)
            if isclose(float(rec['price']),p2['price'],rel_tol=1e-5):
                st=str(rec.get('status') or 'PROPUESTO').upper()
                p2.update({'pivot':key.upper(), 'status':states.get(st,st),
                           'source':'07_PIVOTES_PUBLICADO'})
                break
        low={'price':p1['price'],'date':p1['date'],
             'week_start':w1['week_start'],'status':p1['status'],
             'pivot':p1['pivot'],'source':p1['source']}
        high=p2
        mode=_anchor_match(published,low,high)
        grid=fib_grid('O2',{'CL':low['price'],'O1':high['price']})
        provisional=any(x['status']=='PROPUESTO' for x in (low,high))
        return {'eligible':True,
                'status':'PROPUESTO_SIMULACION' if provisional else 'SIMULACION_ESTRUCTURA_PUBLICADA',
                'simulation_only':True,'operational_blocked':True,
                'reason':'P1_ADMITIDO_P2_MAXIMO_SEMANAL_POSTERIOR','mode':mode,
                'anchors':{'low':low,'high':high},
                'pivot_authority':{'low':{'pivot':p1['pivot'],'status':p1['status']},
                                   'high':{'pivot':p2['pivot'],'status':p2['status']}},
                'levels':dict(zip(('ref382','c1','c2','ref786'),grid.values())),
                'requires_explicit_user_trade_approval':True}
    except (KeyError,ValueError,TypeError,OverflowError) as exc:
        return deny('ESTRUCTURA_INVALIDA',detail=str(exc)[:160])


def confirmed_p1_buy_impulse(weeks, published=None, archived=None):
    """Backward-compatible name; P1 accepts PROPUESTO for SIMULATION only."""
    return select_p1_p2_buy_impulse(weeks,published,archived)


def proposed_simulation_impulse(weeks, published=None, archived=None):
    """Non-actionable Compras preview when the most recent anchor is PROPUESTO.

    Use an explicitly dated 1W LOW/HIGH from the Master or its MCP candidate
    archive, or a freshly observed HIGH in a *closed* UTC week following a
    dated CL candidate. Missing price/date (N/D), weekly mismatch and bearish
    order fail closed. Never infer anchors by inverting legacy Fibonacci.
    """
    def deny(reason):
        return {'eligible':False,'status':'BLOQUEADO','reason':reason,
                'levels':None,'anchors':None,'mode':None}
    published=published or {}; archived=archived or {}
    waves=published.get('waves') or {}
    anchors=[]
    def add(label,kind,price,when,status,source):
        if price is None or not when:return
        try:
            p=positive(price,label);d=iso_date(when,label).isoformat()
            state={'ESTIMADO':'PROPUESTO','CANDIDATO':'PROPUESTO',
                   'VALIDADO_TECNICAMENTE':'VALIDADO'}.get(str(status or 'PROPUESTO').upper(),str(status or 'PROPUESTO').upper())
            if state not in ('PROPUESTO','VALIDADO','CONFIRMADO'):return
            anchors.append({'pivot':label,'kind':kind,'price':p,'date':d,'status':state,'source':source})
        except (ValueError,TypeError):pass
    add('CL','LOW',published.get('cycle_low') or archived.get('cycle_low'),
        published.get('cl_date') or archived.get('cl_date'),
        published.get('cl_status','PROPUESTO'),'MASTER' if published.get('cycle_low') else 'MCP_ARCHIVE')
    for name,kind in [('o1','HIGH'),('o2','LOW'),('o3','HIGH'),('o4','LOW'),('o5','HIGH')]:
        rec=waves.get(name) or {}
        add(name.upper(),kind,rec.get('price'),rec.get('date'),rec.get('status'), 'MASTER')
    if not any(x['pivot']=='O1' for x in anchors):
        add('O1','HIGH',archived.get('o1'),archived.get('o1_date'),'PROPUESTO','MCP_ARCHIVE')
    lows=[x for x in anchors if x['kind']=='LOW']
    if not lows:return deny('EXTREMO_LOW_ND')
    # Settings can show an O1 from MCP that is not yet published. Reconstruct
    # the same PROPOSED candidate from complete weekly bars for simulation.
    # Never infer a weekly extremum from the current spot or a legacy Fibo.
    if not any(x['kind']=='HIGH' for x in anchors):
        last_low=max(lows,key=lambda x:x['date'])
        cl_in_week=any(w['week_start']<=last_low['date']<=w['week_end']
            and isclose(float(w['low']),last_low['price'],rel_tol=1e-4,abs_tol=1e-12)
            for w in weeks)
        if cl_in_week:
            try:
                found=weekly_o1_candidate(weeks,last_low['price'],last_low['date'])
                if found.get('price') and found.get('date'):
                    add('O1','HIGH',found['price'],found['date'],'PROPUESTO','MCP_CLOSED_WEEK_ESTIMATED')
            except (ValueError,TypeError):pass
    if len(anchors)<2:return deny('EXTREMO_HIGH_ND')
    anchors.sort(key=lambda x:(x['date'],{'CL':0,'O1':1,'O2':2,'O3':3,'O4':4,'O5':5}.get(x['pivot'],9)))
    low,high=anchors[-2:]
    if low['kind']!='LOW' or high['kind']!='HIGH':return deny('ULTIMOS_PIVOTES_NO_ALCISTAS')
    if high['price']<=low['price'] or high['date']<=low['date']:return deny('IMPULSO_INVALIDO')
    def in_closed_week(item,field):
        # Both anchors must be actual highs/lows observed in full UTC weeks.
        for week in weeks:
            if week['week_start']<=item['date']<=week['week_end']:
                return isclose(float(week[field]),item['price'],rel_tol=1e-4,abs_tol=1e-12)
        return False
    if not in_closed_week(low,'low') or not in_closed_week(high,'high'):
        return deny('EXTREMO_NO_COINCIDE_CON_1W_CERRADA')
    mode='O2' if (low['pivot'],high['pivot'])==('CL','O1') else ('O4' if (low['pivot'],high['pivot'])==('O2','O3') else 'RETROCESO_ALCISTA')
    grid=fib_grid('O2',{'CL':low['price'],'O1':high['price']})
    return {'eligible':True,'status':'PROPUESTO_SIMULACION',
            'reason':'PAREJA_SEMANAL_PROPUESTA_NO_CERTIFICADA',
            'mode':mode, 'anchors':{'low':low,'high':high},
            'levels':dict(zip(('ref382','c1','c2','ref786'),grid.values())),
            'pivot_authority':{'low':{'pivot':low['pivot'],'status':low['status']},
                               'high':{'pivot':high['pivot'],'status':high['status']}},
            'simulation_only':True,'operational_blocked':True,
            'requires_pivot_validation':True,
            'requires_explicit_user_trade_approval':True}
