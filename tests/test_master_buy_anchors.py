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

# Published Forecast is independent of historical-provider availability.
import pytest
from wave_macro_context import resolve, published_forecast_context

@pytest.mark.parametrize('state',['PROPUESTO','VALIDADO','CONFIRMADO'])
def test_forecast_published_anchors_without_history(state):
 p={'cycle_low':20.5,'cl_date':'2026-01-19','cl_status':state,
    'waves':{'o1':{'price':76.9,'date':'2026-06-01','status':state}}}
 from copy import deepcopy
 before=deepcopy(p)
 ctx=resolve('BTC',p,{}, {'status':'DATA_ERROR'})
 assert ctx['anchors']['CL']==20.5 and ctx['anchors']['O1']==76.9
 assert ctx['simulation_only'] and ctx['operational_blocked']
 assert not ctx['certified'] and p==before

@pytest.mark.parametrize('cl,day,high',[(0,'2026-01-19',76.9),(float('nan'),'2026-01-19',76.9),
 (20.5,'2026-07-01',76.9),(20.5,'invalid',76.9),(80,'2026-01-19',76.9)])
def test_forecast_rejects_invalid_published_anchors(cl,day,high):
 p={'cycle_low':cl,'cl_date':day,'waves':{'o1':{'price':high,'date':'2026-06-01'}}}
 assert published_forecast_context('BTC',p) is None


def test_forecast_paths_and_no_spot_substitution():
 import subprocess
 script=r"""
 const assert=require('assert');const f=require('./static/forecast_fibo_plan.js');
 const selectors={o2:.618,o3:1.618,o4:.5,o5:1.618};
 for(const token of ['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PLUME','PEPE','VIRTUAL']){
 const p={token,cycle_low:20.5,published_cl:20.5,published_cl_date:'2026-01-19',cl_status:'VALIDADO',o1:76.9,waves:{o1:{price:76.9,date:'2026-06-01',status:'PROPUESTO'}}};
 const w=f.wavePath(p,selectors);assert(w.values);assert.equal(w.values[0],20.5);
 assert.equal(f.holdValues(w.values,2)[3],2*w.values[3]);
 }
 assert.deepEqual(f.holdValues(null,2),Array(6).fill(null));
 const p={token:'HYPE',cycle_low:20.5,published_cl:20.5,published_cl_date:'2026-01-19',cl_status:'CONFIRMADO',o1:76.9,waves:{o1:{price:76.9,date:'2026-06-01',status:'VALIDADO'},o2:{price:51.11,date:'2026-07-01',status:'VALIDADO'}}};
 assert.equal(f.wavePath(p,selectors).values[2],51.11);
 assert.equal(f.wavePath(p,{...selectors,o2:.382}).values[2],51.11);
 """
 subprocess.run(['node','-e',script],check=True)
