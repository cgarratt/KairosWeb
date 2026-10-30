import pytest
from orders_inbox import zero_weight_purchase_states,staged_buy_candidates

def payload():
 return dict(tokens=[dict(token='SOL',price=10,current_usdt=10,target=.5),dict(token='LINK',price=10,current_usdt=990,target=.5)],o2_levels={t:dict(ref382=9,c1=8,c2=7,ref786=6) for t in ['SOL','LINK']},buy_eligibility={'SOL':True,'LINK':True},buy_stage_weights={'SOL':[0,50,25,25],'LINK':[0,50,25,25]},forecast_o2_allocation=[0,50,25,25],weekly_context={'SOL':{'mode':'O2'},'LINK':{'mode':'O2'}},drift_band_pp=.5)

@pytest.mark.parametrize('status',['PROPUESTA','CONFIRMADA','PARCIAL','EJECUTADA'])
def test_zero_target_only_disables_proposals(status):
 b=payload();b['buy_order_states']={'SOL':{'O2C1':status}}
 rec={'token':'SOL','lado':'BUY','tramo':'O2C1','estado':status}
 states=zero_weight_purchase_states(b,[rec])
 assert states['SOL']['O2C1']==('NO_APLICA' if status=='PROPUESTA' else status)
 assert rec['effective_status']==('NO_APLICA' if status=='PROPUESTA' else status)
 assert rec['estado']==status

def test_o4_weights_independent_of_o2():
 b=payload();b['weekly_context']['SOL']['mode']='O4';b['buy_stage_weights']['SOL']=[50,0,25,25]
 states=zero_weight_purchase_states(b)
 assert 'O4C1' not in states['SOL']
 assert states['SOL']['O4C2']=='NO_APLICA'

def test_nonzero_tranche_remains_proposed_and_manual_not_changed():
 b=payload();rec={'token':'SOL','lado':'BUY','tramo':'BALANCER','estado':'PROPUESTA'}
 states=zero_weight_purchase_states(b,[rec])
 assert states.get('SOL',{}).get('O2C2','PROPUESTA')=='PROPUESTA'
 assert rec['effective_status']=='PROPUESTA'

def test_zero_tranches_remain_visible_without_sizing():
 rows,remaining=staged_buy_candidates(payload(),100)
 disabled=[r for r in rows if r['stage']=='O2C1']
 assert len(disabled)==2
 assert all(r['order_status']=='NO_APLICA' and r['usdt']==0 and r['quantity']==0 for r in disabled)
 assert remaining>=0
