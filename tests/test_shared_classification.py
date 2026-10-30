import pytest
from order_classification import classify_buy_order

@pytest.mark.parametrize('spot,expected,icon,allowed',[(106,'PROPUESTA','🟢',True),(105,'PROPUESTA','🟡',True),(101,'PROPUESTA','🟡',True),(100,'PROPUESTA','🟡',False),(99,'NO_APLICA','⚪',False)])
def test_price_boundaries(spot,expected,icon,allowed):
 c=classify_buy_order(spot=spot,target=100,stage_pct=40)
 assert (c['effective_status'],c['indicator'],c['may_allocate'])==(expected,icon,allowed)
 assert c['deviation_pct']==pytest.approx(spot-100)

@pytest.mark.parametrize('state',['CONFIRMADA','EJECUTADA','PARCIAL','FILLED','OPEN'])
def test_registered_status_priority_over_zero_and_price(state):
 c=classify_buy_order(spot=50,target=100,stage_pct=0,state=state)
 assert c['indicator']=='🔵' and not c['may_allocate']
 assert c['effective_status'] in ('CONFIRMADA','EJECUTADA','PARCIAL')

def test_zero_allocation_is_no_aplica_even_without_prices():
 assert classify_buy_order(stage_pct=0)['effective_status']=='NO_APLICA'

@pytest.mark.parametrize('spot,target,pct',[(None,100,40),(100,None,40),(float('nan'),100,40),(100,100,None),(100,100,101)])
def test_unknown_data_does_not_become_no_aplica(spot,target,pct):
 c=classify_buy_order(spot=spot,target=target,stage_pct=pct)
 assert c['effective_status']=='PENDIENTE_DATOS' and c['indicator']=='—' and not c['may_allocate']

def test_cancelled_retains_evidence_status():
 assert classify_buy_order(spot=120,target=100,stage_pct=40,state='CANCELLED')['effective_status']=='CANCELADA'

def test_views_preserve_real_status_and_disable_proposals_by_spot():
 from orders_inbox import classify_purchase_views
 b={'tokens':[{'token':'SOL','price':90}], 'o2_levels':{'SOL':{'ref382':110,'c1':100,'c2':80,'ref786':70}},'forecast_o2_allocation':[0,40,40,20]}
 records=[{'token':'SOL','lado':'BUY','tramo':'O2C2','estado':s} for s in ('PROPUESTA','CONFIRMADA','EJECUTADA')]
 candidates=[{'token':'SOL','side':'BUY','stage':'O2C2','usdt':100,'quantity':1}]
 classify_purchase_views(b,candidates,records)
 assert [r['effective_status'] for r in records]==['NO_APLICA','CONFIRMADA','EJECUTADA']
 assert [r['estado'] for r in records]==['PROPUESTA','CONFIRMADA','EJECUTADA']
 assert candidates[0]['usdt']==0 and candidates[0]['display_status']=='NO_APLICA'
