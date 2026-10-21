'use strict';
const assert = require('assert');
const fs=require('fs'),vm=require('vm'),path=require('path');
const ctx={};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'..','static','sales_optimizer.js'),'utf8'),ctx);
const run=ctx.KairosSalesOptimizer.calculate;
const TOKENS=['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE'];
const UNITS=[.12681,3.62437,59.94,398.9885,182.5,52812,3139.4,6775.75,580124,100887,2252.54,376765766];
const EX=[.02681,.62437,29.94,98.9885,32.5,33747,1807.4,3559.95,455124,86420,2252.54,222423248];
const PX=[82808.12,2449.24,106.28,12.351,81.64,.08347,1.0273,.4525,.004774,.01823,.6794,.00000449];
const TG=[.2,.15,.15,.1,.1,.05,.05,.05,.05,.05,.025,.025];
const items=TOKENS.map((token,i)=>({token,units:UNITS[i],exchange_units:EX[i],tier:i<5?'T1':i<10?'T2':'T3',target:TG[i],price:PX[i]}));
const near=(a,b,eps=1e-5)=>assert(Math.abs(a-b)<eps, `${a} != ${b}`);
const r=run(items,22545,40,.5,7225);
assert.strictEqual(r.status,'TARGET_REACHED');near(r.cash_pct_after,40);
near(r.stage1_usdt,4059.20,.12);near(r.stage2_usdt,8056.03,.12);
assert.strictEqual(r.positions.find(p=>p.token==='SOL').sell_usdt,0);
assert.strictEqual(r.positions.find(p=>p.token==='BTC').sell_usdt,0);
assert.strictEqual(r.orders[0].token,'HYPE');assert.strictEqual(r.orders[1].token,'HBAR');
near(r.positions.reduce((s,p)=>s+p.after_pct,0),100);
for(const pct of [0,12.5,26,35,40,55,70,100]){
 const res=run(items,22545,pct,.5,7225);
 assert(res.cash_after>=22545);
 assert(res.positions.every((p,i)=>p.sell_units<=Math.min(EX[i],UNITS[i]*({T1:.3,T2:.7,T3:1}[items[i].tier]))+1e-6));
 if(pct===100){assert.strictEqual(res.status,'CAPACITY_LIMITED');assert(res.unmet_usdt>0);}
}
assert.throws(()=>run(items,22545,101,.5,7225),/DATA ERROR/);
assert.throws(()=>run(items.slice(1),22545,40,.5,7225),/DATA ERROR/);
assert.throws(()=>run(items,22545,40,.5,30000),/DATA ERROR/);
const reserved=items.map(x=>({...x,reserved_sell_units:x.token==='HYPE'?32.5:0}));
assert.strictEqual(run(reserved,22545,40,.5,7225).positions.find(x=>x.token==='HYPE').sell_units,0);
console.log('KairosWeb sales optimizer: all tests passed');
