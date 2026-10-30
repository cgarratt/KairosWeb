import math
import pytest
from liquidity_reserves import budgets_from_master,balancer_purchase_threshold,LiquidityPolicyError,BALANCER_O2_O4_MIN_KEY

def config(threshold=.1):
 return {k:{'value':v,'status':'APROBADO'} for k,v in {
 'PORTFOLIO_LIQ_USDT_FRACTION':.7,'PORTFOLIO_LIQ_BALANCER_FRACTION':.2,
 'PORTFOLIO_LIQ_TRADING_FRACTION':.1,'BALANCER_MAX_PORTFOLIO_FRACTION':.06,
 'TRADING_MAX_PORTFOLIO_FRACTION':.03,BALANCER_O2_O4_MIN_KEY:threshold}.items()}

@pytest.mark.parametrize('physical,disabled',[(1249.98,True),(1250.,False),(1250.01,False)])
def test_strict_boundary(physical,disabled):
 # No QF; normal Balancer=20% cash, so weekly=80%; P=10000.
 r=budgets_from_master(config(),physical,0,10000)
 assert r['balancer_liquidity_guard']['disabled'] is disabled
 assert (r['balancer_max']==0) is disabled
 assert r['weekly_uncommitted']+r['balancer_uncommitted']==pytest.approx(r['compras_max'])

def test_qf_excluded_and_no_oscillation():
 args=(config(),12679.89171,4225.,81604.1350457442)
 first=budgets_from_master(*args);second=budgets_from_master(*args)
 assert first==second
 assert first['balancer_max']==0
 assert first['weekly_uncommitted']==pytest.approx(8454.89171)
 assert first['qf_protected']==4225.
 assert first['balancer_liquidity_guard']['baseline_o2_o4_usdt']<8160.41351

def test_existing_commitments_stay_protected_with_conditional_sales():
 r=budgets_from_master(config(),1250,100,10000,buy_commitments=100,balancer_commitments=50,conditional_sell_proceeds=300)
 assert r['balancer_max']==0
 assert r['weekly_uncommitted']==1050
 assert r['buy_commitments']==100 and r['qf_protected']==100
 assert r['balancer_with_sales_conditional']==300

def test_configurable_zero_disables_guard():
 assert budgets_from_master(config(0),1000,0,10000)['balancer_max']==200
 assert budgets_from_master(config(.2),1250,0,10000)['balancer_max']==0

@pytest.mark.parametrize('bad',[-.1,1.1,float('nan'),float('inf'),True,'0.1'])
def test_invalid_threshold_rejected(bad):
 with pytest.raises(LiquidityPolicyError):balancer_purchase_threshold(config(bad))

def test_unapproved_threshold_rejected():
 p=config();p[BALANCER_O2_O4_MIN_KEY]['status']='PROPUESTO'
 with pytest.raises(LiquidityPolicyError):balancer_purchase_threshold(p)

def test_authorized_default_and_no_qf_release():
 p=config();p.pop(BALANCER_O2_O4_MIN_KEY)
 assert balancer_purchase_threshold(p)==.1
 r=budgets_from_master(p,1000,900,10000)
 assert r['weekly_uncommitted']==100 and r['qf_protected']==900

def test_setting_is_created_then_updated_without_inventory_mutations():
 from threshold_master_fixture import demo_master
 from copy import deepcopy
 from kairos_sheets_features import prepare_changes,portfolio_goals_data,SHEETS
 raw=demo_master();before=deepcopy(raw)
 targets={r[0]:r[3] for r in raw[SHEETS['positions']][1:] if r and r[0] in {'BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE'}}
 entries=[{'group':'portfolio','crypto':.7,'liquidity':.3},{'group':'tiers','T1':.7,'T2':.25,'T3':.05},{'group':'liquidity','usdt':.7,'balancer':.2,'trading':.1,'balancer_min_o2_o4':.1},*({'group':'custody','tier':t,'hodl':h,'core':c,'exchange':e} for t,h,c,e in [('T1',.4,.3,.3),('T2',0,.3,.7),('T3',0,0,1)]),{'group':'token_targets','targets':[{'token':t,'tier':'T1' if v>=.1 else 'T2' if v==.05 else 'T3','target':v} for t,v in targets.items()]}]
 writes,state=prepare_changes(raw,'portfolio_goals',entries,evidence='Umbral configurable autorizado por usuario')
 assert raw==before
 assert state['parameters'][BALANCER_O2_O4_MIN_KEY]['value']==.1
 assert all(name not in ('liquidity','orders','fills') for name,*_ in writes)
 for name,row,col,val in writes:
  rows=raw[SHEETS[name]]
  while len(rows)<=row:rows.append([])
  while len(rows[row])<=col:rows[row].append(None)
  rows[row][col]=val
 entries[2]['balancer_min_o2_o4']=.15
 writes,state=prepare_changes(raw,'portfolio_goals',entries,evidence='Ajuste del umbral por usuario')
 assert state['parameters'][BALANCER_O2_O4_MIN_KEY]['value']==.15
 assert portfolio_goals_data(raw)['balancer_min_o2_o4_fraction']==.1
