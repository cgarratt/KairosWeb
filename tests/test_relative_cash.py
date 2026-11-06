import json,subprocess,unittest,random
from pathlib import Path
from drift_policy import classify,relative_band
from venue_allocation import projected_by_venue
ROOT=Path(__file__).resolve().parents[1]
class RelativeAndCash(unittest.TestCase):
 def test_relative_boundaries(self):
  for t in [.2,.15,.1,.05,.025]:
   self.assertEqual(classify(t*.9,t,10),'NEUTRAL');self.assertEqual(classify(t*1.1,t,10),'NEUTRAL')
   self.assertEqual(classify(t*.899,t,10),'INFRA');self.assertEqual(classify(t*1.101,t,10),'SOBRE')
  self.assertEqual(classify(.01,0),'SOBRE');self.assertEqual(classify(0,0),'NEUTRAL')
  self.assertEqual(relative_band({'DRIFT_BAND_PP':{'value':.05,'status':'APROBADO'}}),10)
  with self.assertRaises(ValueError):relative_band({'DRIFT_BAND_RELATIVE_PCT':{'value':10,'status':'PENDIENTE'}})
 def test_full_binance_6200_with_projected_denominator(self):
  # Old pre-buy deficit=4000, yet final target permits all 6200.
  a,left=projected_by_venue([3000,3000,14000],[.25,.25,.5],[True,True,False],['Binance']*3,{'Binance':6200},6200)
  self.assertAlmostEqual(sum(a),6200);self.assertAlmostEqual(a[0],3100);self.assertAlmostEqual(left['Binance'],0)
  for i in [0,1]:self.assertLessEqual((3000+a[i])/26200,.25+1e-9)
 def test_target_limit_without_forced_spend(self):
  a,left=projected_by_venue([1000,9000],[.2,.8],[True,False],['B','B'],{'B':6200},6200)
  self.assertAlmostEqual(sum(a),1250,places=5);self.assertAlmostEqual(left['B'],4950,places=5)
 def test_no_funds_or_no_eligibility(self):
  for perm,cash in [([False,False],{'B':6200}),([True,True],{'K':6200})]:
   a,_=projected_by_venue([100,100],[.5,.5],perm,['B','B'],cash,6200);self.assertEqual(sum(a),0)
 def test_javascript_python_parity(self):
  rng=random.Random(464);cases=[]
  for _ in range(80):
   n=6;ts=[rng.random() for i in range(n)];total=sum(ts)
   cases.append(dict(values=[rng.random()*5000 for i in range(n)],targets=[t/total for t in ts],permitted=[rng.choice([True,False]) for i in range(n)],venues=[rng.choice(['B','K']) for i in range(n)],cash={'B':rng.random()*6000,'K':rng.random()*1000},budget=rng.random()*7000))
  code="const f=require(process.argv[1]).projectedByVenue;let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(x=>f(x.values,x.targets,x.permitted,x.venues,x.cash,x.budget)))));"
  js=json.loads(subprocess.check_output(['node','-e',code,str(ROOT/'static/o2_sequential.js')],input=json.dumps(cases).encode()))
  for c,b in zip(cases,js):
   a,left=projected_by_venue(**c)
   for i,x in enumerate(a):self.assertAlmostEqual(x,b['alloc'][i],places=6)
   for v in left:self.assertAlmostEqual(left[v],b['cash'][v],places=6)
   final=sum(c['values'])+sum(a)
   for i,x in enumerate(a):
    if x>1e-6:self.assertLessEqual((c['values'][i]+x)/final,c['targets'][i]+1e-7)
 def test_settings_percentage_roundtrip(self):
  code="const f=require(process.argv[1]);const e={key:'DRIFT_BAND_RELATIVE_PCT'};console.log(JSON.stringify([f.scale(e),f.toDisplay(10,e),f.fromDisplay('10%',e)]))"
  self.assertEqual(json.loads(subprocess.check_output(['node','-e',code,str(ROOT/'static/settings_format.js')])),['percent-direct','10',10])
 def test_carry_unused_stage_to_next_eligible_and_confirmed(self):
  # First half is confirmed; remaining enabled stage must fund full selected envelope.
  code="const f=require(process.argv[1]).calculate;const t=[{token:'BTC',venue:'Binance',price:100,current_usdt:1000,target:.25},{token:'ETH',venue:'Binance',price:100,current_usdt:1000,target:.25},{token:'SOL',venue:'Binance',price:100,current_usdt:18000,target:.5}];const levels=Object.fromEntries(t.map(x=>[x.token,{ref382:90,c1:80,c2:70,ref786:60}]));const states=Object.fromEntries(t.map(x=>[x.token,{O2C2:'CONFIRMADA'}]));console.log(JSON.stringify(f(t,levels,[0,50,50,0],6200,0,{relativeBandPct:10,venueFreeUSDT:{Binance:6200},orderStates:states})))"
  r=json.loads(subprocess.check_output(['node','-e',code,str(ROOT/'static/o2_sequential.js')]))
  self.assertAlmostEqual(r['consumed'][1],0);self.assertAlmostEqual(r['spent'],6200);self.assertAlmostEqual(r['venueCashRemaining']['Binance'],0)
