const assert=require('node:assert/strict');
const f=require('../static/forecast_fibo_plan.js');
assert.equal(f.BUY_LEVELS[3],.786);
assert.deepEqual(f.shares([0,40,40,20]),[0,.4,.4,.2]);
assert.throws(()=>f.shares([20,30,20,20]),/100%/);
const budget=f.budget(100000,18000,3000);
assert.deepEqual(budget,{maximum:15000,deployable:15000,shortfall:10000,minimumTarget:25000});
const wave={values:[50,100,69.1,150,110,230]};
const buys=f.scenarioBuyPrices(wave,'o2');
assert.ok(Math.abs(buys[3]-(100-.786*50))<1e-9);
const prices=f.scenarioSellPrices(wave,'o3');
assert.ok(Math.abs(prices[0]-(69.1+1.618*50))<1e-9);
const o4=f.scenarioBuyPrices(wave,'o4');
assert.ok(Math.abs(o4[2]-(150-.618*(150-69.1)))<1e-9);
console.log('PASS: sin techo 25% P, 4 niveles 100%, Fib 78.6%, compras y ventas por tramo');

// Forecast trajectory: published VALIDADO/CONFIRMADO cannot be overwritten by selectors.
const pivots={token:'HYPE',cycle_low:21,o1:80,published_cl:20.5,published_cl_date:'2026-01-21',cl_status:'CONFIRMADO',
  waves:{o1:{price:76.9,date:'2026-06-16',status:'VALIDADO'},
    o2:{price:51.11,date:'2026-08-02',status:'VALIDADO'},
    o3:{price:97.885,date:'2026-09-23',status:'PROPUESTO'},
    o4:{price:null,date:null,status:'PROPUESTO'},o5:{price:null,date:null,status:'PROPUESTO'}}};
const choicesA={o2:.382,o3:1.618,o4:.5,o5:1.618};
const choicesB={o2:.786,o3:4.618,o4:.786,o5:4.618};
const a=f.wavePath(pivots,choicesA),b=f.wavePath(pivots,choicesB);
assert.deepEqual(a.values.slice(0,3),[20.5,76.9,51.11]);
assert.deepEqual(b.values.slice(0,3),[20.5,76.9,51.11]);
assert.deepEqual(a.locked,['cl','o1','o2']);
assert.equal(a.statuses.o2,'VALIDADO');
assert.notEqual(a.values[3],b.values[3]); // only PROPUESTO O3 is adjustable
assert.notEqual(a.values[4],b.values[4]);
const fixedO3={...pivots,waves:{...pivots.waves,o3:{price:101,date:'2026-09-23',status:'CONFIRMADO'}}};
const c=f.wavePath(fixedO3,choicesA),d=f.wavePath(fixedO3,choicesB);
assert.equal(c.values[3],101);assert.equal(d.values[3],101);
assert.equal(c.statuses.o3,'CONFIRMADO');
const fixedAll={...pivots,waves:{...pivots.waves,
  o2:{price:51.11,date:'2026-08-02',status:'VALIDADO'},
  o3:{price:97.885,date:'2026-09-23',status:'CONFIRMADO'},
  o4:{price:70,date:'2026-11-01',status:'VALIDADO'},
  o5:{price:140,date:'2027-01-01',status:'CONFIRMADO'}}};
const allA=f.wavePath(fixedAll,choicesA),allB=f.wavePath(fixedAll,choicesB);
assert.deepEqual(allA.values,[20.5,76.9,51.11,97.885,70,140]);
assert.deepEqual(allA.values,allB.values);
assert.deepEqual(allA.locked,['cl','o1','o2','o3','o4','o5']);
const proposal={...pivots,cl_status:'PROPUESTO',waves:{...pivots.waves,o1:{price:76.9,date:'2026-06-16',status:'PROPUESTO'},o2:{price:51.11,date:'2026-08-02',status:'PROPUESTO'}}};
assert.notEqual(f.wavePath(proposal,choicesA).values[2],f.wavePath(proposal,choicesB).values[2]);
const impossible={...pivots,waves:{...pivots.waves,o2:{price:90,date:'2026-08-02',status:'VALIDADO'}}};
assert.equal(f.wavePath(impossible,choicesA).values[2],90);
assert.equal(f.wavePath(impossible,choicesA).state,'ESTRUCTURA_INCOMPATIBLE');
const noPublishedPrice={...pivots,waves:{...pivots.waves,o2:{price:null,status:'CONFIRMADO'}}};
assert.equal(f.wavePath(noPublishedPrice,choicesA).state,'PIVOTE_PUBLICADO_SIN_PRECIO');
console.log('PASS: Forecast fixed VALIDADO/CONFIRMADO, changing only PROPUESTO');
