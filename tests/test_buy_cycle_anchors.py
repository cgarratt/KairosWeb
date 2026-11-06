import copy
import unittest
from buy_weekly_policy import published_buy_impulse, select_p1_p2_buy_impulse
from wave_macro_context import resolve_long_term_buy, published_forecast_context

class CycleAnchors(unittest.TestCase):
    def base(self):
        return {'cycle_low':100,'cl_date':'2026-01-01','cl_status':'VALIDADO',
                'waves':{'o1':{'price':200,'date':'2026-02-01','status':'PROPUESTO'}}}
    def advanced(self):
        p=self.base();p['waves'].update(o2={'price':150,'date':'2026-03-01','status':'VALIDADO'},
                                      o3={'price':300,'date':'2026-04-01','status':'PROPUESTO'})
        return p
    def test_original_pair(self):
        r=published_buy_impulse(self.base());self.assertEqual((r['mode'],r['anchor_pair']),('O2','CL/O1'))
        self.assertAlmostEqual(r['levels']['c1'],150)
    def test_proposed_o2_does_not_move_low(self):
        p=self.base();p['waves']['o2']={'price':160,'date':'2026-03-01','status':'PROPUESTO'}
        before=copy.deepcopy(p);r=published_buy_impulse(p)
        self.assertEqual(r['anchors']['low']['pivot'],'CL');self.assertTrue(r['eligible']);self.assertEqual(p,before)
    def test_dynamic_o4(self):
        r=published_buy_impulse(self.advanced());self.assertEqual(r['anchor_pair'],'O2/O3');self.assertEqual(r['mode'],'O4')
        self.assertAlmostEqual(r['levels']['c1'],225);self.assertTrue(r['simulation_only']);self.assertTrue(r['operational_blocked'])
    def test_o3_price_without_date_does_not_switch(self):
        p=self.base();p['waves']['o3']={'price':300};self.assertEqual(published_buy_impulse(p)['mode'],'O2')
    def test_chronology_blocks(self):
        p=self.advanced();p['waves']['o3']['date']='2026-02-15';self.assertFalse(published_buy_impulse(p)['eligible'])
    def test_missing_predecessor_blocks(self):
        p=self.advanced();del p['waves']['o2'];self.assertFalse(published_buy_impulse(p)['eligible'])
    def test_incomplete_master_not_replaced_by_history(self):
        p=self.base();del p['waves']['o1'];self.assertFalse(select_p1_p2_buy_impulse([],p)['eligible'])
    def test_invalid_high_blocks(self):
        p=self.base();p['waves']['o1']['price']=90;self.assertFalse(published_buy_impulse(p)['eligible'])
    def test_invalid_o2_price_blocks_o4(self):
        p=self.advanced();p['waves']['o2']['price']=80;self.assertFalse(published_buy_impulse(p)['eligible'])
    def test_confirmed_o2_waits_for_o3(self):
        p=self.base();p['waves']['o2']={'price':150,'date':'2026-03-01','status':'CONFIRMADO'}
        r=published_buy_impulse(p);self.assertEqual(r['cycle_phase'],'O3_EN_DESARROLLO');self.assertFalse(r['eligible'])
        self.assertEqual(r['anchor_pair'],'CL/O1')
    def test_confirmed_o4_waits_for_new_cycle(self):
        p=self.advanced();p['waves']['o4']={'price':220,'date':'2026-05-01','status':'CONFIRMADO'}
        r=published_buy_impulse(p);self.assertEqual(r['cycle_phase'],'O5_EN_DESARROLLO');self.assertFalse(r['eligible'])
    def test_confirmed_o5_terminal(self):
        p=self.advanced();p['waves'].update(o4={'price':220,'date':'2026-05-01','status':'VALIDADO'},o5={'price':350,'date':'2026-06-01','status':'CONFIRMADO'})
        r=published_buy_impulse(p);self.assertEqual(r['cycle_phase'],'CICLO_COMPLETO');self.assertFalse(r['eligible'])
    def test_proposed_o4_does_not_select_o4_o5(self):
        p=self.advanced();p['waves'].update(o4={'price':220,'date':'2026-05-01','status':'PROPUESTO'},o5={'price':350,'date':'2026-06-01','status':'PROPUESTO'})
        self.assertEqual(published_buy_impulse(p)['anchor_pair'],'O2/O3')
    def test_adapter_without_market_uses_master(self):
        r=resolve_long_term_buy('BTC',self.base(),{});self.assertEqual(r['anchor_pair'],'CL/O1');self.assertTrue(r['eligible'])
    def test_forecast_stays_original(self):
        r=published_forecast_context('BTC',self.advanced());self.assertEqual(r['anchors']['CL'],100);self.assertEqual(r['anchors']['O1'],200)

if __name__=='__main__':unittest.main()
