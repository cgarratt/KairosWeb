"""KairosWeb weekly structural simulation adapter (read-only).

The caller gets snapshot 07_PIVOTES and MCP 1D *closed* records. CL/O1
from 07 are never recertified. Archived cycle data is exploratory only.
"""
from wave_structure import (full_utc_weeks, weekly_o1_candidate, fib_grid,
                            post_o1_daily_low, weekly_wave_candidates, WaveStructureError)
from buy_weekly_policy import select_p1_p2_buy_impulse
from structural_outliers import virtual_flash_cl

def resolve(token, published, archived, data):
    """Build an explicit CL/O1 and Fib O2 reference with traceable evidence."""
    empty={'status':'NO_WEEKLY_ANCHORS','levels':None,'history':{'status':'NO_WEEKLY_ANCHORS'},
           'anchors':{'CL':None,'O1':None},'certified':False}
    if data.get('status')!='OK' or data.get('closed_only') is not True:
        return dict(empty,status='MCP_DATA_ERROR',history={'status':'DATA_ERROR'})
    source=str(data.get('source') or '')
    if token=='HYPE':
        if source!='Hyperliquid Spot' or data.get('pair')!='HYPE/USDC' or data.get('interval')!='1d':
            return dict(empty,status='WRONG_HYPE_SOURCE')
    elif source!='Binance Spot' or data.get('interval')!='1d':
        return dict(empty,status='WRONG_BINANCE_SOURCE')
    records=data.get('records') or []
    weeks=full_utc_weeks(records)
    cl=published.get('cycle_low') or archived.get('cycle_low')
    cl_date=published.get('cl_date') or archived.get('cl_date')
    if token=='VIRTUAL' and virtual_flash_cl(cl,cl_date):
        return dict(empty,status='VIRTUAL_FLASH_CL_EXCLUDED',history={'status':'EXCLUDED_OUTLIER'})
    if not(cl and cl_date):return dict(empty,status='MISSING_DATED_CL')
    try:
        # Confirmed or manually reviewed wave takes precedence; MCP never
        # overwrites one. Historical archive's O1 is a candidate only.
        pub_o1=published.get('waves',{}).get('o1') or {}
        archived_o1={'price':archived['o1'],'date':archived.get('o1_date'),'status':'PROPUESTO'} if archived.get('o1') and archived.get('o1_date') else None
        selected=weekly_o1_candidate(weeks,cl,cl_date,published_o1=pub_o1 if pub_o1.get('price') else archived_o1)
        if not selected.get('price'):return dict(empty,status=selected.get('status','NO_WEEKLY_O1'))
        structural=weekly_wave_candidates(weeks,cl_date)
        levels=fib_grid('O2',{'CL':cl,'O1':selected['price']})
        low=post_o1_daily_low(records,selected['date'])
        history={'status':'PROVISIONAL' if low['status']=='OBSERVED_POST_O1' else low['status'],
                 'estimated_o1':selected['price'],'estimated_o1_date':selected['date'],
                 'post_o1_min':low.get('low'),'post_o1_min_date':low.get('date'),
                 'certified':selected['status']=='CONFIRMADO',
                 'pivot_5l5r':selected.get('pivot_5l5r',False),
                 'source':source+' 1D CLOSED / WEEKLY UTC', 'week_start':selected['week_start']}
        return {'status':'SIMULATION_WITH_CONFIRMED_O1' if selected['status']=='CONFIRMADO' else 'ESTIMATED_WEEKLY_CANDIDATE',
                'certified':selected['status']=='CONFIRMADO',
                'quote_currency':'USDC' if token=='HYPE' else 'USDT', 'levels':{'ref382':levels['O2C1'],'c1':levels['O2C2'],
                    'c2':levels['O2C3'],'ref786':levels['O2C4']},
                'history':history,'weekly_wave_candidates':structural,'anchors':{'CL':float(cl),'CL_date':str(cl_date)[:10],
                  'O1':selected['price'],'O1_date':selected['date'],'O1_status':selected['status'],
                  'O1_source':selected['source'],'O1_pivot_5l5r':selected.get('pivot_5l5r',False)}}
    except (WaveStructureError,TypeError,ValueError,OverflowError):
        return dict(empty,status='INVALID_WEEKLY_SEQUENCE')


def resolve_long_term_buy(token, published, data, archived=None):
    """Compras simulation: dated P1 of any recognized state and weekly-max P2.

    P2 can be proposed; no other 5L/5R/BOS gate is applied to simulations.
    Other modes (including ordinary Ventas and Forecast) remain unrestricted.
    """
    deny={'status':'MCP_DATA_ERROR','eligible':False,'levels':None,
          'reason':'FUENTE_MCP_NO_VERIFICADA','mode':None,'history':{'status':'N/D'}}
    if data.get('status')!='OK' or data.get('closed_only') is not True or data.get('interval')!='1d':return deny
    if token=='HYPE':
        if data.get('source')!='Hyperliquid Spot' or data.get('pair')!='HYPE/USDC':return dict(deny,reason='VENUE_HYPE_INVALIDO')
    elif data.get('source')!='Binance Spot':return dict(deny,reason='VENUE_BINANCE_INVALIDO')
    if token=='VIRTUAL' and virtual_flash_cl(published.get('cycle_low'),published.get('cl_date')):
        return {**deny,'status':'BLOQUEADO','reason':'VIRTUAL_CL_FLASH_EXCLUIDO_REQUIERE_REVISION'}
    try:
        weeks=full_utc_weeks(data.get('records') or [])
        # P1 may be PROPUESTO for simulation; P2 is highest later FULL weekly high.
        decision=select_p1_p2_buy_impulse(weeks,published,archived)
        if not decision['eligible']:
            return {**decision,'history':{'status':'N/D'},'quote_currency':'USDC' if token=='HYPE' else 'USDT'}
        high=decision['anchors']['high']
        low=post_o1_daily_low(data.get('records') or [],high['date'])
        decision['history']={'status':'PROVISIONAL' if low['status']=='OBSERVED_POST_O1' else low['status'],
                             'estimated_o1_date':high['date'],'post_o1_min':low.get('low'),
                             'post_o1_min_date':low.get('date')}
        decision['quote_currency']='USDC' if token=='HYPE' else 'USDT'
        return decision
    except (WaveStructureError,ValueError,TypeError,KeyError) as exc:
        return {**deny,'reason':'INVALID_WEEKLY_SEQUENCE','detail':str(exc)[:140]}


def published_wave_levels(wave_pivots):
    """Reference levels shared by Balancer/Ventas/Compras/Forecast.

    Only when source 07_PIVOTES provides every dated anchor; no synthetic
    anchors, no use of historical C1/C2. Never actionable by itself.
    """
    from wave_structure import fib_grid, WaveStructureError
    requirements={'O2':('CL','O1'),'O3':('CL','O1','O2'),
                  'O4':('O2','O3'),'O5':('O2','O3','O4')}
    result={}
    for token,p in wave_pivots.items():
        waves=p.get('waves') or {}
        anchors={'CL':p.get('cycle_low')}
        dates={'CL':p.get('cl_date')}
        for key in ('O1','O2','O3','O4','O5'):
            row=waves.get(key.lower(),{})
            anchors[key]=row.get('price');dates[key]=row.get('date')
        grid={}
        for wave,needed in requirements.items():
            if all(anchors.get(k) and dates.get(k) for k in needed):
                try:
                    dd=[str(dates[k])[:10] for k in needed]
                    if dd!=sorted(dd) or len(set(dd))!=len(dd):continue
                    grid[wave]=fib_grid(wave,anchors)
                except (WaveStructureError,ValueError,TypeError):continue
        result[token]={'status':'PUBLISHED_REFERENCE_NON_EXECUTABLE',
                        'levels':grid,'dates':dates,'anchors':anchors}
    return result
