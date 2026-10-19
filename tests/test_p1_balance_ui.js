const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
vm.runInThisContext(fs.readFileSync('static/purchase_plan.js','utf8'));
const calc=require('../static/o2_sequential.js').calculate;
const items=[
{token:'BTC',price:40,current_usdt:40,target:0.2},
{token:'ETH',price:10,current_usdt:10,target:0.5},
{token:'SOL',price:50,current_usdt:50,target:0.3}
];
const levels=Object.fromEntries(items.map(t=>[t.token,{ref382:t.price,c1:t.price,c2:t.price,ref786:t.price}]));
const sim=calc(items,levels,[100,0,0,0],100,1,{requireEligibility:true,eligibility:{BTC:true,ETH:true,SOL:true}});
assert.ok(sim.amounts[0].every(x=>x<1e-9),'SOBRE BTC should not buy');
assert.ok(sim.amounts[2][0]<1e-9,'SOBRE SOL should not buy at C1');
assert.ok(sim.amounts[1][0]>0,'INFRA ETH should buy');
assert.ok(sim.spent<100,'Remainder must stay in USDT once deficits are covered');
assert.ok(sim.spent<=100+1e-6);
const endValues=items.map((x,i)=>x.current_usdt+sim.totalByToken[i]);
const total=endValues.reduce((a,b)=>a+b,0);
assert.ok(endValues[1]/total<=0.5+1e-9,'ETH cannot exceed its target');
const blocked=calc(items,levels,[100,0,0,0],100,1,{requireEligibility:true,eligibility:{BTC:false,ETH:false,SOL:false}});
assert.equal(blocked.spent,0);
console.log('P1/P2 balance: PASS');

// El % de peso debe ser POST compra en cada tramo, no el peso anterior al fill.
const afterC1=sim.snapshots[0].postWeights;
assert.ok(afterC1[1]>sim.snapshots[0].weights[1], 'Comprar ETH aumenta el peso post-compra');
assert.ok(Math.abs(afterC1.reduce((a,b)=>a+b,0)-1)<1e-9, 'Los pesos post-compra suman 100%');
assert.ok(sim.snapshots.every(step=>Array.isArray(step.postWeights)&&step.postWeights.length===items.length));

// Órdenes: controles activos Exchange / Tier / Operación / Token.
const {visible,init}=require('../static/orders_inbox.js');
const item=(venue,token,tier,side)=>({
 dataset:{ordersVenue:venue,token,tier,side},
 closest:()=>({dataset:{ordersVenue:venue}}),hidden:false
});
const a=item('Binance','BTC','T1','BUY');
const b=item('KuCoin','VIRTUAL','T3','BUY');
const c=item('Binance','ETH','T1','SELL');
assert.equal(visible(a,'Todos','Todos','Todos','Todos'),true);
assert.equal(visible(a,'Binance','T1','BUY','BTC'),true);
assert.equal(visible(a,'KuCoin','T1','BUY','BTC'),false);
assert.equal(visible(a,'Binance','T2','BUY','BTC'),false);
assert.equal(visible(a,'Binance','T1','SELL','BTC'),false);
assert.equal(visible(a,'Binance','T1','BUY','ETH'),false);
assert.equal(visible(b,'KuCoin','T3','BUY','VIRTUAL'),true);
assert.equal(visible(c,'Binance','T1','SELL','ETH'),true);
const controls={};
for(const id of ['orders-venue','orders-tier','orders-side','orders-token']){
 const handlers={};controls[id]={value:'Todos',handlers,addEventListener:(type,cb)=>{handlers[type]=cb;}};
}
const reset={handlers:{},addEventListener:function(type,cb){this.handlers[type]=cb;}};
const empty={hidden:false};const count={textContent:''};
const rows=[a,b,c];
const doc={getElementById:id=>id==='orders-inbox'?{querySelectorAll:()=>rows}:id==='orders-clear-filters'?reset:id==='orders-empty-filter'?empty:id==='orders-filter-count'?count:controls[id]||null};
init(doc);
assert.equal(count.textContent,'3 de 3 propuestas visibles · ninguna colocada');
controls['orders-token'].value='VIRTUAL';controls['orders-token'].handlers.change();
assert.deepEqual(rows.map(x=>!x.hidden),[false,true,false]);
controls['orders-venue'].value='Binance';controls['orders-venue'].handlers.change();
assert.equal(empty.hidden,false);
reset.handlers.click();
assert.deepEqual(rows.map(x=>!x.hidden),[true,true,true]);
assert.ok(Object.values(controls).every(x=>x.value==='Todos'));
console.log('Orders simplified Exchange / Tier / Operation / Token filters PASS');
