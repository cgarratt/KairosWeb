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

// Órdenes: filtros KairosGPT y semáforos.
const {visible,matchesDistance,matchesGroup}=require('../static/orders_inbox.js');
const item=(v,token,tier,stage,dist,category='ESTRUCTURA')=>({dataset:{ordersVenue:v,token,tier,category,ordersCategory:category,stage,wave:stage.startsWith('EXT')?'EXTENSION_1W':'O2',side:'BUY',proximity:dist===null?'PRECIO_PENDIENTE':dist<0?'NIVEL_SUPERADO':'EN_ESPERA',distance:dist===null?'':String(dist)},closest:()=>({dataset:{ordersVenue:v}})});
const a=item('Binance','BTC','T1','O2C2',3.5);
const b=item('KuCoin','VIRTUAL','T3','C2',null);
const c=item('Binance','ETH','T1','O2C1',-2);
assert.equal(visible(a,'Todos','Todos','Todos','','Todos','Todas','Todos','Todos'),true);
assert.equal(visible(a,'Todos','Todos','Todos','','Todos','O2','Todos','Todos'),true);
assert.equal(visible(a,'Todos','Todos','Todos','','Todos','T1','Todos','Todos'),true);
assert.equal(visible(a,'Todos','Todos','Todos','','Todos','Binance','Todos','Todos'),true);
assert.equal(visible(b,'Todos','Todos','Todos','','Todos','TOKEN:VIRTUAL','Todos','Todos'),true);
assert.equal(visible(b,'Todos','Todos','Todos','','Todos','O2','Todos','Todos'),false);
assert.equal(visible(a,'Todos','Todos','Todos','','Todos','O2','T3','Todos'),false);
assert.equal(visible(a,'KuCoin','Todos','Todos','','Todos','Todas','Todos','Todos'),false);
assert.equal(visible(a,'Todos','Todos','Todos','BTC','Todos','Todas','Todos','Todos'),true);
assert.equal(visible(a,'Todos','Todos','Todos','SOL','Todos','Todas','Todos','Todos'),false);
assert.equal(matchesDistance(a,'2-5'),true);
assert.equal(matchesDistance(b,'0-2'),false);
assert.equal(matchesDistance(c,'NIVEL_SUPERADO'),true);
assert.equal(matchesGroup(a,'O2'),true);
assert.equal(matchesGroup(b,'O2'),false);
console.log('Orders v2.0.14 quick views and filters PASS');
