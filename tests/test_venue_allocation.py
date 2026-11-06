import json,random,subprocess,unittest
from pathlib import Path
from venue_allocation import proportional_by_venue, free_venue_cash, cash_from_snapshot
from orders_inbox import staged_buy_candidates

ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'static/o2_sequential.js'
class VenueAllocationTests(unittest.TestCase):
    def test_proportional_no_drift_ranking(self):
        a,left=proportional_by_venue([100,300],['Binance']*2,{'Binance':100},100)
        self.assertEqual(a,[25,75]);self.assertEqual(left,{'Binance':0})
    def test_venue_constraint_and_redistribution(self):
        a,left=proportional_by_venue([200,100,300],['Binance','KuCoin','KuCoin'],{'Binance':200,'KuCoin':40},200)
        self.assertAlmostEqual(a[0],160);self.assertAlmostEqual(a[1],10);self.assertAlmostEqual(a[2],30)
        self.assertAlmostEqual(left['Binance'],40);self.assertEqual(left['KuCoin'],0)
    def test_no_transfer_or_missing_venue(self):
        a,_=proportional_by_venue([500,500],['KuCoin','Unknown'],{'Binance':1000},1000)
        self.assertEqual(a,[0,0])
    def test_deficit_ceiling(self):
        a,left=proportional_by_venue([10,20],['Binance']*2,{'Binance':1000},1000)
        self.assertEqual(a,[10,20]);self.assertEqual(left,{'Binance':970})
    def test_deductions_once(self):
        s={'liquidity_venues_USDT':{'Binance':100,'KuCoin':50,'Hyperliquid':15,'Quantfury':20},
           'trading_real_fixed_USDT':20,'reserved_buy_usdt_by_venue':{'Binance':30},
           'foreign_quote_pending':[{'venue':'Hyperliquid','amount':5}]}
        self.assertEqual(cash_from_snapshot(s),{'Binance':70,'KuCoin':50,'Hyperliquid':0,'Quantfury':0})
    def test_additional_protected_cash(self):
        self.assertEqual(free_venue_cash({'B':100},protected={'B':20},commitments={'B':30}),{'B':50})
    def test_bad_cash_blocked(self):
        for x in (-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):proportional_by_venue([100],['B'],{'B':x},10)
        with self.assertRaises(ValueError):free_venue_cash({'B':10},commitments={'B':11})
        with self.assertRaises(ValueError):free_venue_cash({'B':10},protected={'QF':5})
    def test_permutation_invariance(self):
        gaps=[400,200,100,500];venues=['B','B','K','K'];cash={'B':90,'K':140}
        a,_=proportional_by_venue(gaps,venues,cash,200)
        p=[3,1,0,2];b,_=proportional_by_venue([gaps[i] for i in p],[venues[i] for i in p],cash,200)
        for j,i in enumerate(p):self.assertAlmostEqual(a[i],b[j])
    def test_random_python_javascript_parity_and_conservation(self):
        rng=random.Random(1321);cases=[]
        for _ in range(120):
            n=rng.randint(1,12);cases.append({'gaps':[rng.random()*1000 for i in range(n)],
              'venues':[rng.choice(['B','K','H','MISSING']) for i in range(n)],
              'cash':{v:rng.random()*1000 for v in ['B','K','H']},'budget':rng.random()*3000})
        code="const f=require(process.argv[1]).proportionalByVenue;let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(c=>f(c.gaps,c.venues,c.cash,c.budget)))));"
        out=json.loads(subprocess.check_output(['node','-e',code,str(JS)],input=json.dumps(cases).encode()))
        for case,js in zip(cases,out):
            a,left=proportional_by_venue(**case)
            self.assertLessEqual(sum(a),case['budget']+1e-7)
            for i,x in enumerate(a):self.assertAlmostEqual(x,js['alloc'][i]);self.assertLessEqual(x,case['gaps'][i]+1e-7)
            for v in case['cash']:
                used=sum(x for i,x in enumerate(a) if case['venues'][i]==v)
                self.assertAlmostEqual(used+left[v],case['cash'][v]);self.assertGreaterEqual(left[v],0)

class OrdersIntegration(unittest.TestCase):
    def payload(self):
        ts=[{'token':'BTC','price':100,'current_usdt':100,'target':.3},
            {'token':'ETH','price':100,'current_usdt':100,'target':.3},
            {'token':'SUI','price':100,'current_usdt':100,'target':.2},
            {'token':'SOL','price':100,'current_usdt':1700,'target':.2}]
        keys=('ref382','c1','c2','ref786')
        return {'tokens':ts,'o2_levels':{t['token']:dict(zip(keys,[90,80,70,60])) for t in ts},
                'buy_eligibility':{t['token']:True for t in ts},
                'buy_stage_weights':{},'forecast_o2_allocation':[25,25,25,25],
                'venue_free_usdt':{'Binance':90,'KuCoin':20},'drift_band_pp':.5}
    def test_sequential_venue_cash_and_order_invariance(self):
        payload=self.payload();a,left=staged_buy_candidates(payload,400)
        spent={v:sum(x['usdt'] for x in a if x['venue']==v) for v in payload['venue_free_usdt']}
        self.assertAlmostEqual(spent['Binance'],90);self.assertAlmostEqual(spent['KuCoin'],20)
        self.assertAlmostEqual(left,290)
        btc=sum(x['usdt'] for x in a if x['token']=='BTC');eth=sum(x['usdt'] for x in a if x['token']=='ETH')
        self.assertAlmostEqual(btc,eth)
        payload['tokens'].reverse();b,_=staged_buy_candidates(payload,400)
        aa={(x['token'],x['stage']):x['usdt'] for x in a};bb={(x['token'],x['stage']):x['usdt'] for x in b}
        self.assertEqual(aa.keys(),bb.keys())
        for k in aa:self.assertAlmostEqual(aa[k],bb[k])
    def test_missing_cash_no_positive_order(self):
        p=self.payload();p.pop('venue_free_usdt');a,left=staged_buy_candidates(p,400)
        self.assertFalse(any(x['usdt']>0 for x in a));self.assertEqual(left,400)
    def test_confirmed_and_zero_tranches_cannot_consume(self):
        p=self.payload();p['buy_order_states']={'BTC':{'O2C1':'CONFIRMADA'}}
        p['forecast_o2_allocation']=[0,50,25,25]
        a,left=staged_buy_candidates(p,400)
        self.assertFalse(any(x['usdt']>0 and x['stage']=='O2C1' for x in a))
        self.assertLessEqual(sum(x['usdt'] for x in a),110+1e-8)
    def test_browser_and_orders_same_plan(self):
        p=self.payload();a,_=staged_buy_candidates(p,400)
        code="const f=require(process.argv[1]).calculate;let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{const p=JSON.parse(s);console.log(JSON.stringify(f(p.tokens,p.o2_levels,[25,25,25,25],400,.5,{requireEligibility:true,eligibility:p.buy_eligibility,venueFreeUSDT:p.venue_free_usdt,tokenVenues:{BTC:'Binance',ETH:'Binance',SOL:'Binance',SUI:'KuCoin'}})));});"
        js=json.loads(subprocess.check_output(['node','-e',code,str(JS)],input=json.dumps(p).encode()))
        for i,t in enumerate(p['tokens']):
            for j,x in enumerate(js['amounts'][i]):
                expected=sum(r['usdt'] for r in a if r['token']==t['token'] and r['stage']=='O2C'+str(j+1))
                self.assertAlmostEqual(x,expected)
        self.assertAlmostEqual(js['spent'],110)

if __name__=='__main__':unittest.main()

class CurrencyFunding(unittest.TestCase):
    def test_hype_usdc_does_not_consume_usdt(self):
        p=OrdersIntegration().payload()
        p['tokens'][0]['token']='HYPE'
        p['o2_levels']['HYPE']=p['o2_levels'].pop('BTC')
        p['buy_eligibility']['HYPE']=True
        p['venue_free_usdt']={'Hyperliquid':400}
        orders,left=staged_buy_candidates(p,400)
        self.assertFalse(any(x['usdt']>0 for x in orders));self.assertEqual(left,400)
