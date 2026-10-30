import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from buy_weekly_policy import published_buy_impulse,select_p1_p2_buy_impulse
from wave_macro_context import resolve_long_term_buy

class MasterAnchors(unittest.TestCase):
 def setUp(self):
  self.p=dict(cycle_low=.6359,cl_date='2026-08-18',cl_status='PROPUESTO',waves={'o1':dict(price=1.2938,date='2026-09-21',status='PROPUESTO')})
 def test_sui_without_market_data(self):
  r=resolve_long_term_buy('SUI',self.p,{})
  self.assertTrue(r['eligible']);self.assertEqual(r['anchors']['high']['price'],1.2938)
  self.assertAlmostEqual(r['levels']['c1'],.96485)
  self.assertAlmostEqual(r['levels']['c2'],.8872178)
  self.assertAlmostEqual(r['levels']['ref382'],1.0424822)
  self.assertAlmostEqual(r['levels']['ref786'],.7766906)
 def test_conflicting_market_data_ignored(self):
  r=select_p1_p2_buy_impulse([{'invalid':'ignored'}],self.p)
  self.assertTrue(r['eligible']);self.assertEqual(r['anchors']['low']['price'],.6359)
 def test_no_certification_or_mutation(self):
  original=copy.deepcopy(self.p);r=published_buy_impulse(self.p)
  self.assertEqual(self.p,original);self.assertTrue(r['operational_blocked'])
  self.assertEqual(r['anchors']['high']['status'],'PROPUESTO')
 def test_confirmed_preserved(self):
  self.p['cl_status']='CONFIRMADO';self.p['waves']['o1']['status']='CONFIRMADO'
  self.assertEqual(published_buy_impulse(self.p)['anchors']['high']['status'],'CONFIRMADO')
 def test_chronology_still_enforced(self):
  self.p['waves']['o1']['date']='2026-08-01'
  self.assertFalse(published_buy_impulse(self.p)['eligible'])
 def test_non_bullish_still_rejected(self):
  self.p['waves']['o1']['price']=.5
  self.assertFalse(published_buy_impulse(self.p)['eligible'])
 def test_missing_pair_falls_back(self):
  self.p['waves']={}
  self.assertIsNone(published_buy_impulse(self.p))
  self.assertFalse(select_p1_p2_buy_impulse([],self.p)['eligible'])
 def test_latest_low_selects_o4(self):
  self.p['waves'].update(o2=dict(price=.8,date='2026-09-28',status='VALIDADO'),o3=dict(price=2,date='2026-10-12',status='PROPUESTO'))
  r=published_buy_impulse(self.p)
  self.assertEqual(r['mode'],'O4');self.assertEqual(r['anchors']['low']['price'],.8)
 def test_hype_native_history_not_required_for_master_pair(self):
  r=resolve_long_term_buy('HYPE',self.p,{'status':'DATA_ERROR'})
  self.assertTrue(r['eligible']);self.assertEqual(r['quote_currency'],'USDC')
if __name__=='__main__':unittest.main()
