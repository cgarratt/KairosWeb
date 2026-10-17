const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root=path.join(__dirname,'..');
vm.runInThisContext(fs.readFileSync(path.join(root,'static/purchase_plan.js'),'utf8'));
const {calculate,classifyDrift} = require('../static/o2_sequential.js');
// Classification uses the 1pp policy from the caller. +/-1pp are neutral.
assert.strictEqual(classifyDrift(.56,.5,1).status,'SOBRE');
assert.strictEqual(classifyDrift(.44,.5,1).status,'INFRA');
assert.strictEqual(classifyDrift(.504,.5,1).status,'NEUTRAL');
assert.strictEqual(classifyDrift(.51,.5,1).status,'NEUTRAL');
assert.strictEqual(classifyDrift(.49,.5,1).status,'NEUTRAL');
assert.strictEqual(classifyDrift(.51,.5,.5).status,'SOBRE');
assert.strictEqual(classifyDrift(.51,.5,2).status,'NEUTRAL');
assert.strictEqual(classifyDrift(.3,.5,NaN).status,'N/D');
const tokens=[{token:'A',price:100,current_usdt:700,target:.5},{token:'B',price:100,current_usdt:300,target:.5}];
const levels={A:{c1:90,c2:80}, B:{c1:90,c2:80}};
const r=calculate(tokens,levels,[25,25,25,25],200,1);
assert.strictEqual(r.snapshots.length,4);
assert.strictEqual(r.snapshots[0].states[0],'SOBRE');
assert.strictEqual(r.snapshots[0].states[1],'INFRA');
assert(r.amounts[1][0]>0,'Infraponderado obtiene compras');
// Previous buys change the composition BEFORE later stages.
assert(r.snapshots[1].weights[1]>r.snapshots[0].weights[1]);
assert(r.snapshots[1].driftsPP[1]>r.snapshots[0].driftsPP[1]);
assert(Math.abs(r.spent-200)<1e-7);
assert(Math.abs(r.consumed.reduce((a,b)=>a+b,0)-r.spent)<1e-7);
// A token can go from SOBRE at an earlier stage to INFRA at a later stage
// thanks to a deeper relative drawdown while prior stage buys are retained.
const shifting=[{token:'A',price:100,current_usdt:600,target:.5},{token:'B',price:100,current_usdt:400,target:.5}];
const shiftingLevels={A:{c1:80,c2:60},B:{c1:99,c2:98}};
const s=calculate(shifting,shiftingLevels,[25,25,25,25],40,1);
assert.strictEqual(s.snapshots[0].states[0],'SOBRE');
assert.strictEqual(s.snapshots[2].states[0],'INFRA', 'A must become INFRA at C3');
assert(s.amounts[0][2]>0,'A should become eligible for buying in C3');
// Missing Fibonacci levels should not display badges and never receive buys.
const missing=calculate(tokens,{A:levels.A,B:{}},[0,0,100,0],100,1);
assert.strictEqual(missing.amounts[1][2],0);
assert.strictEqual(missing.prices[1][2],null);
console.log('O2 drift labels v2.0.3 PASS');
