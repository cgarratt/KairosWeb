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
