from orders_inbox import staged_buy_candidates,build_order_inbox,VENUES


def _inputs():
    tokens=[
        {'token':'BTC','price':101,'target':.50,'units':1,'current_usdt':101},
        {'token':'SUI','price':5,'target':.25,'units':20,'current_usdt':100},
        {'token':'HYPE','price':20,'target':.25,'units':5,'current_usdt':100},
    ]
    buy={'tokens':tokens,'buy_eligibility':{'BTC':True,'SUI':False,'HYPE':True},
         'buy_stage_weights':{t['token']:[25,25,25,25] for t in tokens},
         'forecast_o2_allocation':[25,25,25,25],
         'o2_levels':{'BTC':{'ref382':100,'c1':90,'c2':80,'ref786':70},
                      'SUI':{'ref382':4,'c1':3,'c2':2,'ref786':1},
                      'HYPE':{'ref382':19,'c1':18,'c2':17,'ref786':16}},
         'weekly_context':{'BTC':{'mode':'O2','provisional':True},
                           'HYPE':{'mode':'RETROCESO_ALCISTA','provisional':True}}}
    d={'usdt_operating':400.,'usdt_total':500.,'trading_reserve':100.,
       'liquidity_venues':{'Binance':300.,'KuCoin':100.,'Hyperliquid':0.},
       'rows':[{'token':'BTC','price':101,'exchange_units':0.5},
               {'token':'SUI','price':5,'exchange_units':12},
               {'token':'HYPE','price':20,'exchange_units':2}]}
    bal={'sells':[{'token':'BTC','value':500,'units':10},
                  {'token':'SUI','value':25,'units':5},
                  {'token':'HYPE','value':30,'units':2}]}
    return d,buy,bal


def test_inbox_ignores_nd_and_never_sells_btc():
    d,b,balance=_inputs()
    inbox=build_order_inbox(d,b,balance)
    assert all(not (i['side']=='BUY' and i['token']=='SUI') for i in inbox['candidates'])
    assert all(not (i['side']=='SELL' and i['token']=='BTC') for i in inbox['candidates'])
    assert all(i['order_status']=='PROPUESTA_NO_COLOCADA' for i in inbox['candidates'])
    assert inbox['buy_planned']+inbox['buy_unassigned']<=400.001
    assert inbox['venues']['KuCoin']['sells_proposed_usdt']==25.
    assert any(i['venue']=='Hyperliquid' and i['token']=='HYPE' for i in inbox['candidates'])
    assert all(i['limit'] is None and i['distance_pct'] is None for i in inbox['candidates'] if i['side']=='SELL')


def test_proximity_and_stage_order():
    d,b,bal=_inputs()
    inbox=build_order_inbox(d,b,bal)
    btc=[i for i in inbox['candidates'] if i['token']=='BTC' and i['side']=='BUY']
    assert len(btc)==4
    assert btc[0]['stage']=='O2C1'
    assert btc[0]['proximity']=='CERCA'
    assert all(i['quantity']>0 and i['limit']>0 for i in btc)
    assert len({i['proposal_key'] for i in inbox['candidates']})==len(inbox['candidates'])


def test_full_web_page_is_read_only():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text()
    page=(root/'templates/ordenes.html').read_text()
    assert "{'slug':'ordenes'" in app
    assert "@app.route('/mode/ordenes')" in app
    assert 'Órdenes' in page and 'PROPUESTAS' in page
    assert 'send_order' not in page and 'submit_order' not in page
    assert "'/api/orders/place'" not in app


def test_venue_mapping_keeps_hype_separate():
    assert VENUES['BTC']=='Binance' and VENUES['SUI']=='KuCoin'
    assert VENUES['HYPE']=='Hyperliquid'


# Phase 1.1: Portfolio and price-structure are independent sources.
def test_structural_weekly_sells_use_published_three_anchors_without_sizing():
    d,b,bal=_inputs()
    published={'SUI':{'levels':{'O3':{'O3V1':6.0,'O3V2':8.5,'O3V3':11.0,'O3V4':13.5}}}}
    inbox=build_order_inbox(d,b,bal,wave_levels=published)
    sells=[x for x in inbox['categories']['ESTRUCTURA'] if x['side']=='SELL' and x['token']=='SUI']
    assert len(sells)==4
    assert sells[0]['stage']=='O3V1'
    assert sells[0]['limit']==6.0
    assert sells[0]['quantity'] is None and sells[0]['usdt'] is None
    assert all(x['actionable_alert'] is False for x in sells)
    assert all(x['venue']=='KuCoin' for x in sells)
    assert inbox['coverage'][1]['token']=='SUI'
    assert inbox['coverage'][1]['origin']=='ESTRUCTURA'
    assert inbox['coverage'][1]['side']=='SELL'
    assert inbox['coverage'][1]['limit']==6.0


def test_generic_weekly_extension_not_labeled_o3_o5():
    d,b,bal=_inputs()
    b['weekly_context']['HYPE']['anchors']={
        'low':{'price':10,'date':'2026-01-05'},
        'high':{'price':15,'date':'2026-07-06'}}
    inbox=build_order_inbox(d,b,bal)
    hy=[x for x in inbox['categories']['ESTRUCTURA'] if x['token']=='HYPE' and x['side']=='SELL']
    assert hy and all(x['wave']=='EXTENSION_1W' for x in hy)
    assert all(x['limit']>0 and x['quote_currency']=='USDC' for x in hy)
    assert all(x['distance_pct'] is None and x['proximity']=='COTIZACION_NO_HOMOLOGADA' for x in hy)
    assert all(x['venue']=='Hyperliquid' for x in hy)
    assert not any(x['side']=='SELL' and x['token']=='BTC' for x in inbox['candidates'])


def test_balance_proposals_have_no_fibonacci_prices_and_nd_is_not_order():
    d,b,bal=_inputs()
    bal['buys']=[{'token':'SUI','value':10}]
    inbox=build_order_inbox(d,b,bal)
    s=inbox['categories']['BALANCE']
    assert {(x['token'],x['side']) for x in s}=={('SUI','BUY'),('SUI','SELL'),('HYPE','SELL')}
    assert all(x['limit'] is None and x['distance_pct'] is None for x in s)
    assert inbox['coverage'][1]['origin']=='BALANCE'
    assert inbox['coverage'][1]['limit'] is None
    assert inbox['coverage'][1]['status']=='SIN_LIMIT'
    assert all(x['actionable_alert'] is False for x in inbox['candidates'])


def test_no_structure_and_no_balance_yields_unavailable_not_fake_order():
    d,b,bal=_inputs()
    b['buy_eligibility']={k:False for k in b['buy_eligibility']}
    bal['sells']=[]
    inbox=build_order_inbox(d,b,bal)
    assert len(inbox['coverage'])==3
    assert all(c['status']=='N/D' and c['side'] is None for c in inbox['coverage'])
    assert inbox['candidates']==[]


def test_nearest_future_not_previous_touched_level():
    d,b,bal=_inputs()
    # BTC has 4 structurally valid BUY refs beneath 101, nearest is $100.
    inbox=build_order_inbox(d,b,bal)
    row=inbox['coverage'][0]
    assert row['token']=='BTC' and row['limit']==100
    assert row['side']=='BUY' and 0<row['distance_pct']<=1.01
    assert row['status']=='CERCANO'


def test_template_separates_two_sources_and_preserves_no_exchange_writes():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    template=(root/'templates/ordenes.html').read_text()
    assert "item.category=='ESTRUCTURA'" in template
    assert "item.category=='ESTRUCTURA' else 'BALANCE'" in template
    assert 'Referencia técnica más cercana por token' in template
    assert 'POR DEFINIR' in template
    assert 'data-orders-category' in template
    assert '/api/orders/place' not in template


def test_hype_does_not_compare_binance_usdt_spot_to_hyperliquid_usdc():
    d,b,bal=_inputs()
    inbox=build_order_inbox(d,b,bal)
    h=[x for x in inbox['categories']['ESTRUCTURA'] if x['token']=='HYPE']
    assert h and all(x['quote_currency']=='USDC' for x in h)
    assert all(x['distance_pct'] is None for x in h)
    assert all(x['actionable_alert'] is False for x in h)
