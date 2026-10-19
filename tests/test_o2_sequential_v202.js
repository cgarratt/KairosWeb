const assert=require('assert');
global.purchasePlan=require('fs').readFileSync(require('path').join(__dirname,'../static/purchase_plan.js'),'utf8');
const vm=require('vm');vm.runInThisContext(global.purchasePlan);
const {calculate}=require('../static/o2_sequential.js');
const tokens=[{token:'A',price:100,current_usdt:800,target:.5},{token:'B',price:100,current_usdt:200,target:.5}];
const levels={A:{ref382:95,c1:90,c2:85,ref786:80},B:{ref382:95,c1:90,c2:85,ref786:80}};
const r=calculate(tokens,levels,[25,25,25,25],200);
assert.strictEqual(r.amounts.length,2);
assert(Math.abs(r.spent-200)<1e-6);
assert(r.totalByToken[1]>r.totalByToken[0]);
assert(Math.abs(r.consumed.reduce((a,b)=>a+b,0)-r.spent)<1e-7);
// Zero-weight levels must not consume cash.
const z=calculate(tokens,levels,[0,0,100,0],100);
assert(z.consumed[0]===0&&z.consumed[1]===0&&z.consumed[3]===0);
console.log('O2 staged regression PASS');

// Editable scenario percentages: exact 100% with proportional redistribution.
const W=require('../static/purchase_weights.js');
const master=W.normalize([20,30,40,10]);
assert.deepStrictEqual(master,[20,30,40,10]);
const custom=W.rebalance(master,0,50);
assert.deepStrictEqual(custom,[50,18.75,25,6.25]);
assert.strictEqual(custom.reduce((a,b)=>a+b,0),100);
assert.deepStrictEqual(W.rebalance(master,2,100),[0,0,100,0]);
assert.deepStrictEqual(W.rebalance([0,0,100,0],2,25),[25,25,25,25]);
assert.deepStrictEqual(W.normalize([0,0,0,0]),[25,25,25,25]);
assert.deepStrictEqual(W.rebalance(master,1,-30),[28.57,0,57.14,14.29]);
for(const v of [0,2.37,11.99,50,99.99,100]){
  const changed=W.rebalance(master,1,v);
  assert(Math.abs(changed.reduce((a,b)=>a+b,0)-100)<1e-9);
  assert(changed.every(x=>x>=0&&x<=100));
}
// O2/O4 local split overriding per-token historical mix, sequential safeguards intact.
const split=W.asFractions(custom), customW={A:split,B:split};
const scenario=calculate(tokens,levels,split,1000,1,{weightsByToken:customW});
assert.deepStrictEqual(scenario.stageBudgets.map(x=>Math.round(x)),[500,188,250,63]);
assert(Math.abs(scenario.stageBudgets.reduce((a,b)=>a+b,0)-1000)<1e-7);
assert(scenario.consumed.every((x,i)=>x<=scenario.stageBudgets[i]+1e-7));
assert(scenario.spent<=1000+1e-7);
console.log('Scenario Fibonacci % override PASS');
