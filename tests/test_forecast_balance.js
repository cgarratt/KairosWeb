const assert=require('node:assert/strict');
const {allocateBuys,allocateSales,drifts}=require('../static/forecast_balance.js');
// O4: direct all available USDT to underweights before target-proportional excess.
let before=[
 {token:'BTC',current:40,target:.2,eligible:true},
 {token:'ETH',current:5,target:.4,eligible:true},
 {token:'SOL',current:55,target:.4,eligible:true}
];
let purchase=allocateBuys(20,before);
assert(Math.abs(purchase.total-20)<1e-7);
assert.equal(purchase.amounts[0],0,'BTC overweight cannot receive budget when deficits exist');
assert(purchase.amounts[1]>purchase.amounts[2],'the larger shortage must receive more');
let preAbs=drifts(before).reduce((s,r)=>s+Math.abs(r.drift),0);
let postAbs=drifts(before.map((x,i)=>({...x,current:x.current+purchase.amounts[i]}))).reduce((s,r)=>s+Math.abs(r.drift),0);
assert(postAbs<preAbs,'O4 should improve drift when shortages are reachable');
// O3: eligible overweight should be sold first; undershoot is not forced if caps allow.
let sale=allocateSales(20,[{current:60,capacity:40,target:.4},{current:20,capacity:15,target:.4}],100,.3);
assert(Math.abs(sale.total-20)<1e-6);
assert(sale.amounts[0]>sale.amounts[1]);
assert(sale.amounts.every((x,i)=>x> -1e-9&&x<=[40,15][i]+1e-8));
// HODL locked: capacity=0 despite positive nominal holding.
sale=allocateSales(10,[{current:90,capacity:0,target:.4},{current:10,capacity:10,target:.4}],100,.3);
assert.equal(sale.amounts[0],0);
assert(Math.abs(sale.amounts[1]-10)<1e-6);
assert.throws(()=>allocateSales(10,[{current:30,capacity:20,target:.3}],100,1.01));
console.log('PASS Forecast balance purchase/sale simulation tests');
