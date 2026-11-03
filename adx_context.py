"""Wilder ADX(14), strength confirmation only; no financial mutations."""
import math

def adx_values(bars, period=14):
    if len(bars)<2*period+1:
        raise ValueError('ADX requiere más velas OHLC')
    candles=[]
    for bar in bars:
        values=[bar[k] for k in ('high','low','close')]
        if any(isinstance(v,bool) for v in values):raise ValueError('OHLC inválido')
        high,low,close=map(float,values)
        if any(not math.isfinite(v) or v<=0 for v in (high,low,close)) or not low<=close<=high:
            raise ValueError('OHLC inválido')
        candles.append((high,low,close))
    tr=[];plus=[];minus=[]
    for previous,current in zip(candles,candles[1:]):
        ph,pl,pc=previous;h,l,c=current
        up,down=h-ph,pl-l
        tr.append(max(h-l,abs(h-pc),abs(l-pc)))
        plus.append(up if up>0 and up>down else 0.)
        minus.append(down if down>0 and down>up else 0.)
    atr=sum(tr[:period])/period
    p=sum(plus[:period])/period;m=sum(minus[:period])/period
    dx=[];pdi=mdi=0.
    for i in range(period-1,len(tr)):
        if i>=period:
            atr=(atr*(period-1)+tr[i])/period
            p=(p*(period-1)+plus[i])/period
            m=(m*(period-1)+minus[i])/period
        pdi=100*p/atr if atr else 0.
        mdi=100*m/atr if atr else 0.
        dx.append(100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else 0.)
    value=sum(dx[:period])/period
    for x in dx[period:]:value=(value*(period-1)+x)/period
    return {'adx':min(100.,max(0.,value)),'plus_di':pdi,'minus_di':mdi}

def confirmed_signal(signal, adx):
    if type(adx) not in (int,float) or not math.isfinite(adx) or not 0<=adx<=100:
        return 'N/D'
    if adx<=23:return 'NEUTRAL'
    return signal if signal in ('COMPRAR','VENDER','ESPERAR') else 'N/D'

def enrich_context(item, series, valid=False):
    item.update(adx=None,plus_di=None,minus_di=None,adx_status='N/D',
                adx_reason='Faltan máximos/mínimos válidos del mismo período y proveedor.')
    if valid and series:
        try:
            item.update(adx_values(series['records']),adx_status='OK',adx_reason='')
        except (ValueError,TypeError,KeyError,OverflowError):pass
    item['combined_signal']=confirmed_signal(item['signal'],item['adx'])
    signal=item['combined_signal']
    if signal=='N/D':
        text='No hay datos completos para una recomendación conjunta. Actualizar históricos y revisar la causa en valores y fuentes.'
    elif signal=='NEUTRAL':
        text='ADX no supera 23: contexto neutral. Esperar fuerza de tendencia antes de considerar una compra o venta por esta señal.'
    elif signal=='ESPERAR':
        text='ADX supera 23, pero RSI y Stoch RSI no cumplen simultáneamente las reglas de compra o venta. Esperar alineación.'
    elif signal=='COMPRAR':
        text='Compra técnica confirmada: RSI < 30 y sobre su media, K > D y ADX > 23. Evaluar BTC solo si está INFRA y existe presupuesto libre.'
    else:
        text='Venta técnica confirmada: RSI > 70 y bajo su media, K < D y ADX > 23. BTC NEVER SELL bloquea esta venta; conservar BTC.'
    item['recommendation_summary']=text
    return item
