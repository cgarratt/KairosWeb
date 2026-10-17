const assert=require('assert');
global.purchasePlan=require('fs').readFileSync(require('path').join(__dirname,'../static/purchase_plan.js'),'utf8');
const vm=require('vm');vm.runInThisContext(global.purchasePlan);
const {calculate}=require('../static/o2_sequential.js');
const tokens=[{token:'A',price:100,current_usdt:800,target:.5},{token:'B',price:100,current_usdt:200,target:.5}];
const levels={A:{c1:90,c2:80},B:{c1:90,c2:80}};
const r=calculate(tokens,levels,[25,25,25,25],200);
assert.strictEqual(r.amounts.length,2);
assert(Math.abs(r.spent-200)<1e-6);
assert(r.totalByToken[1]>r.totalByToken[0]);
assert(Math.abs(r.consumed.reduce((a,b)=>a+b,0)-r.spent)<1e-7);
// Zero-weight levels must not consume cash.
const z=calculate(tokens,levels,[0,0,100,0],100);
assert(z.consumed[0]===0&&z.consumed[1]===0&&z.consumed[3]===0);
console.log('O2 staged regression PASS');
