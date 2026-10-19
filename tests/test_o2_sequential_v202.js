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

// Slider is a WATERFALL. Each % is a cap over total available USDT,
// NOT a slice of partial slider-selected budget.
const plan1=W.waterfall(2587.80,19145,[20,30,40,10]);
assert.deepStrictEqual(plan1.stageCapacities,[3829,5743.5,7658,1914.5]);
assert.deepStrictEqual(plan1.stageBudgets,[2587.8,0,0,0]);
assert.deepStrictEqual(W.waterfall(3829,19145,master).stageBudgets,[3829,0,0,0]);
assert.deepStrictEqual(W.waterfall(4000,19145,master).stageBudgets,[3829,171,0,0]);
assert.deepStrictEqual(W.waterfall(9572.5,19145,master).stageBudgets,[3829,5743.5,0,0]);
assert.deepStrictEqual(W.waterfall(19145,19145,master).stageBudgets,[3829,5743.5,7658,1914.5]);
assert.deepStrictEqual(W.waterfall(40000,19145,master).stageBudgets,[3829,5743.5,7658,1914.5]);
assert.deepStrictEqual(W.waterfall(0,19145,master).stageBudgets,[0,0,0,0]);
// Slider is a percent of available USDT, NOT of patrimony P.
assert.strictEqual(W.budgetFromAvailablePercent(0,19145),0);
assert.strictEqual(W.budgetFromAvailablePercent(100,19145),19145);
assert.strictEqual(W.budgetFromAvailablePercent(50,19145),9572.5);
assert.strictEqual(W.budgetFromAvailablePercent(13.5,19145),2584.58);
assert.strictEqual(W.budgetFromAvailablePercent(200,19145),19145);
assert.strictEqual(W.budgetFromAvailablePercent(-5,19145),0);
assert.strictEqual(W.budgetFromAvailablePercent(100,0),0);
assert.deepStrictEqual(W.waterfall(W.budgetFromAvailablePercent(13.5,19145),19145,master).stageBudgets,[2584.58,0,0,0]);
// Fixed drafts: changing one field does not silently rewrite the other three.
assert.deepStrictEqual(W.validateDraft(['50.00','18.75','25','6.25']).values,[50,18.75,25,6.25]);
assert.equal(W.validateDraft(['50','30','40','10']).valid,false);
assert.equal(W.validateDraft(['50','18.75','25','6.25']).valid,true);
assert.equal(W.validateDraft(['50','18,75','25','6,25']).valid,true);
assert.equal(W.validateDraft(['20','','40','10']).valid,false);
assert.equal(W.validateDraft(['20','30','40','10.001']).valid,false);
assert.equal(W.validateDraft(['100','0','0','0']).valid,true);
assert.equal(W.validateDraft(['0','0','0','0']).valid,false);
const staged=calculate(tokens,levels,[20,30,40,10],2587.80,1,{
  stageBudgets:plan1.stageBudgets});
assert.deepStrictEqual(staged.stageBudgets,[2587.8,0,0,0]);
assert.ok(staged.consumed.slice(1).every(v=>v===0));
assert.ok(staged.spent<=2587.80+1e-8);
assert.throws(()=>calculate(tokens,levels,[25,25,25,25],100,1,{stageBudgets:[100,100,0,0]}),/exceed slider/);
console.log('Waterfall C1→C4 + fixed percentage draft regression PASS');

// v2.0.18: post-buy coloring uses the target-weight difference in pp,
// NEVER historical price touches, and NEVER colors zero-USDT rows.
const {postBuySemaphore:lamp}=require('../static/o2_sequential.js');
assert.deepStrictEqual(lamp(0,.08,.10),{state:'none',driftPP:null});
assert.deepStrictEqual(lamp(0,.10,.10),{state:'none',driftPP:null});
assert.deepStrictEqual(lamp(.004,.10,.10),{state:'none',driftPP:null}); // rounds to $0.00
assert.strictEqual(lamp(.005,.10,.10).state,'green'); // first cent displayed
assert.strictEqual(lamp(10,.10,.10).state,'green'); // exact target
assert.strictEqual(lamp(10,.11,.10).state,'green'); // above target
assert.strictEqual(lamp(10,.099,.10).state,'amber'); // -0.1 pp
assert.strictEqual(lamp(10,.09,.10).state,'amber'); // -1.0 pp inclusive
assert.strictEqual(lamp(10,.08999,.10).state,'red'); // more than 1 pp short
assert.strictEqual(lamp(10,NaN,.10).state,'none');
assert.strictEqual(lamp(10,undefined,.10).state,'none');
const probe=calculate(tokens,levels,[25,25,25,25],200,1);
for(let j=0;j<4;j++)for(let i=0;i<tokens.length;i++){
  const selected=probe.amounts[i][j];
  const classified=lamp(selected,probe.snapshots[j].postWeights[i],tokens[i].target);
  if(selected<0.005) assert.strictEqual(classified.state,'none');
  else assert.notStrictEqual(classified.state,'none');
}
console.log('Post-buy target drift coloring PASS');
