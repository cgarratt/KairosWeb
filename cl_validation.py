"""CL weekly technical assessment. Read-only, no Elliott/human certification.

Technical status requires strict weekly 5L/5R + bullish BOS of a prior
confirmed weekly swing high. An attestation only authorizes a reviewed
technical state transition in a draft; it does not grant CONFIRMADO.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
import hashlib
import hmac
import json
import os
import time


def review_cl(weeks, price, day, *, left=5, right=5):
    from wave_structure import iso_date, positive
    d=iso_date(day,'CL date'); p=positive(price,'CL price')
    out={'status':'PROPUESTO','validated':False,'low_5l5r':False,'bos_week':None,
         'protected_high':None,'weekly_source':'CLOSED_UTC_MON_SUN','cl_week':None}
    k=next((i for i,w in enumerate(weeks) if w['week_start']<=d.isoformat()<=w['week_end']),None)
    if k is None:
        out['reason']='La fecha CL no está cubierta por una semana UTC cerrada';return out
    w=weeks[k];out['cl_week']=w['week_start']
    if w.get('low_date')!=d.isoformat() or abs(float(w['low'])-p)>max(1e-10,p*1e-5):
        out['reason']='CL no coincide con el mínimo de su semana cerrada';return out
    if k<left or k+right>=len(weeks):
        out['reason']='Faltan 5 semanas cerradas anteriores o posteriores';return out
    if not all(p<float(x['low']) for x in weeks[k-left:k]+weeks[k+1:k+right+1]):
        out['reason']='No es un mínimo semanal estricto 5L/5R';return out
    out['low_5l5r']=True
    # A BOS demands a *previous* weekly structural swing high, not merely a
    # daily candle or an ad-hoc threshold. Require its own 5L/5R confirmation.
    highs=[]
    for i in range(left,k):
        if i+right>=k:break
        val=float(weeks[i]['high'])
        if all(val>float(x['high']) for x in weeks[i-left:i]+weeks[i+1:i+right+1]):
            highs.append((i,val))
    if not highs:
        out['reason']='Sin máximo estructural semanal previo 5L/5R para verificar BOS';return out
    protected_i,protected_val=highs[-1];out['protected_high']=protected_val
    # Breakout AFTER the CL pivot was confirmed by 5R, using weekly CLOSE.
    post=[x for x in weeks[k+right+1:] if float(x['close'])>protected_val]
    if not post:
        out['reason']='BOS alcista por cierre semanal pendiente';return out
    out.update(status='VALIDADO',validated=True,bos_week=post[0]['week_start'],
               reason='5L/5R y BOS alcista semanal verificados; pendiente confirmación humana')
    return out


def _payload(token,price,day,snapshot,at):
    return json.dumps({'token':token,'price':float(price),'date':day,'snapshot':snapshot,'iat':at},
                      sort_keys=True,separators=(',',':')).encode('utf-8')


def sign_review(token,price,day,snapshot,*,now=None):
    key=os.getenv('KAIROS_SESSION_SECRET','')
    if len(key)<32:raise ValueError('KAIROS_SESSION_SECRET debe tener al menos 32 caracteres')
    at=int(time.time() if now is None else now)
    tag=hmac.new(key.encode(),_payload(token,price,day,snapshot,at),hashlib.sha256).hexdigest()
    return f'{at}.{tag}'


def verify_review(token,price,day,snapshot,proof,*,now=None):
    if not isinstance(proof,str) or len(proof)>96 or '.' not in proof:return False
    raw,digest=proof.split('.',1)
    if not raw.isdigit() or len(digest)!=64:return False
    at=int(raw);current=int(time.time() if now is None else now)
    if current-at<0 or current-at>900:return False
    try:expected=sign_review(token,price,day,snapshot,now=at)
    except (ValueError,TypeError):return False
    return hmac.compare_digest(expected,proof)


def review_wave(weeks, price, day, wave, *, left=5, right=5):
    """Review O1/O3/O5 HIGH or O2/O4 LOW from CLOSED weekly candles.

    An individual candidate may be technically validated, NEVER human-confirmed.
    The BOS comes after the right-hand five weeks and breaks a previously
    protected opposite swing by a weekly closing price.
    """
    from wave_structure import iso_date, positive
    if wave not in ('o1','o2','o3','o4','o5'):
        raise ValueError('Invalid wave')
    field='high' if wave in ('o1','o3','o5') else 'low'
    opposite='low' if field=='high' else 'high'
    d=iso_date(day,'wave date').isoformat();p=positive(price,'wave price')
    out={'status':'PROPUESTO','validated':False,'wave':wave,'direction':field.upper(),
         'reason':'Pivote semanal no validado'}
    k=next((i for i,w in enumerate(weeks) if w['week_start']<=d<=w['week_end']),None)
    if k is None or k<left or k+right>=len(weeks):
        out['reason']='Sin semana completa o cinco semanas anteriores/posteriores';return out
    w=weeks[k];datefield=field+'_date'
    if w.get(datefield)!=d or abs(float(w[field])-p)>max(1e-10,p*1e-5):
        out['reason']='Precio/fecha no coinciden con extremo semanal';return out
    neighbors=weeks[k-left:k]+weeks[k+1:k+right+1]
    test=(lambda x: p>float(x[field])) if field=='high' else (lambda x:p<float(x[field]))
    if not all(test(x) for x in neighbors):
        out['reason']='No cumple pivote estricto 5L/5R';return out
    if field=='high':
        # An O1/O3/O5 swing HIGH belongs to a bullish LOW→HIGH impulse.
        # Validate its bullish BOS after the prior low was confirmed; requiring
        # a new *bearish* break after this high would reject valid rising trends.
        from buy_weekly_policy import _pivot_indices, _observed_bull_bos
        lows=_pivot_indices(weeks,'low',left,right)
        highs=_pivot_indices(weeks,'high',left,right)
        preceding=[j for j in lows if j<k and j+right<k]
        if not preceding:
            out['reason']='Falta mínimo semanal 5L/5R previo al máximo';return out
        li=preceding[-1]
        bos=_observed_bull_bos(weeks,li,k,highs,right)
        if not bos:
            out['reason']='Falta BOS alcista semanal del impulso previo';return out
        return {**out,'status':'VALIDADO','validated':True,'bos_week':bos['bos_week'],
                'protected_level':bos['protected_high'],
                'reason':'Máximo 5L/5R + BOS alcista del impulso verificados; confirmación humana pendiente'}
    prior=[]
    for j in range(left,k-right):
        v=float(weeks[j][opposite]);ad=weeks[j-left:j]+weeks[j+1:j+right+1]
        if all(v<float(x[opposite]) for x in ad) if opposite=='low' else all(v>float(x[opposite]) for x in ad):
            prior.append((j,v))
    if not prior:
        out['reason']='Falta pivote contrario protegido previo para BOS';return out
    level=prior[-1][1]
    future=weeks[k+right+1:]
    bos=next((x for x in future if float(x['close'])>level),None)
    if not bos:
        out['reason']='Falta BOS alcista semanal posterior a 5R';return out
    return {**out,'status':'VALIDADO','validated':True,'bos_week':bos['week_start'],
            'protected_level':level,'reason':'5L/5R + BOS semanal verificados, falta confirmación humana'}
