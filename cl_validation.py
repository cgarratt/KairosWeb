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
    out={'status':'CANDIDATO','validated':False,'low_5l5r':False,'bos_week':None,
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
    out.update(status='VALIDADO_TECNICAMENTE',validated=True,bos_week=post[0]['week_start'],
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
