"""Production reserve/allocator integration, no Flask or market dependency."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from liquidity_reserves import budgets_from_master
from orders_inbox import allocate_infra_buys

def config():
 return {k:{'value':v,'status':'APROBADO'} for k,v in {
 'PORTFOLIO_LIQ_USDT_FRACTION':.7,'PORTFOLIO_LIQ_BALANCER_FRACTION':.2,
 'PORTFOLIO_LIQ_TRADING_FRACTION':.1,'BALANCER_MAX_PORTFOLIO_FRACTION':.06,
 'TRADING_MAX_PORTFOLIO_FRACTION':.03,'BALANCER_MIN_O2_O4_PORTFOLIO_FRACTION':.1}.items()}

class SalesRecycling(unittest.TestCase):
 def test_guard_zeroes_initial_reserve_but_preserves_sale_scenario(self):
  r=budgets_from_master(config(),12679.89171,4225,82656.11,conditional_sell_proceeds=3694)
  self.assertEqual(r['balancer_max'],0)
  self.assertEqual(r['balancer_with_sales_conditional'],3694)
  self.assertEqual(r['compras_max'],8454.89171)
  self.assertEqual(r['usdt_physical'],12679.89171)
  self.assertEqual(r['qf_protected'],4225)
 def test_no_sale_means_no_buy(self):
  self.assertEqual(budgets_from_master(config(),1000,200,10000)['balancer_with_sales_conditional'],0)
 def test_existing_commitments_not_released(self):
  r=budgets_from_master(config(),1250,100,10000,buy_commitments=100,balancer_commitments=50,conditional_sell_proceeds=300)
  self.assertEqual(r['buy_commitments'],100)
  self.assertEqual(r['weekly_uncommitted'],1050)
  self.assertEqual(r['balancer_max'],0)
  self.assertEqual(r['balancer_with_sales_conditional'],300)
 def test_active_reserve_adds_sales_once(self):
  r=budgets_from_master(config(),4000,0,10000,conditional_sell_proceeds=300)
  self.assertEqual(r['balancer_max'],600)
  self.assertEqual(r['balancer_with_sales_conditional'],900)
 def test_cap_applies_to_reserve_not_sale_recycling(self):
  r=budgets_from_master(config(),1000,200,10000,conditional_sell_proceeds=2000)
  self.assertEqual(r['balancer_max'],0)
  self.assertEqual(r['balancer_with_sales_conditional'],2000)
 def test_no_approved_cap_legacy_still_preserves_conditional_sales(self):
  p=config();p.pop('BALANCER_MAX_PORTFOLIO_FRACTION');p.pop('TRADING_MAX_PORTFOLIO_FRACTION')
  r=budgets_from_master(p,1000,200,10000,conditional_sell_proceeds=300)
  self.assertEqual(r['balancer_with_sales_conditional'],300)
 def test_conditional_proceeds_reach_actual_infra_allocator(self):
  r=budgets_from_master(config(),12679.89171,4225,82656.11,conditional_sell_proceeds=3694)
  # Explicitly synthetic post-sale portfolio. Units and cash remain real unchanged.
  rows=[{'token':'BTC','value':5000,'target':.5,'weight':.25,'drift_pp':-25},
        {'token':'HYPE','value':15000,'target':.5,'weight':.75,'drift_pp':25}]
  buys=allocate_infra_buys(rows,r['balancer_with_sales_conditional'],.5)
  self.assertEqual([x['token'] for x in buys],['BTC'])
  self.assertAlmostEqual(sum(x['value'] for x in buys),3694)
 def test_no_infra_leaves_conditional_cash_unspent(self):
  rows=[{'token':'BTC','value':5000,'target':.5,'weight':.5,'drift_pp':0},
        {'token':'HYPE','value':5000,'target':.5,'weight':.5,'drift_pp':0}]
  self.assertEqual(allocate_infra_buys(rows,3694,.5),[])
 def test_gpt_patch_is_identical(self):
  root=Path(__file__).resolve().parents[1]
  self.assertEqual((root/'liquidity_reserves.py').read_bytes(),(root/'compat/kairos_gpt/liquidity_reserves.py').read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
