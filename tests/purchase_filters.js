const assert=require('assert');const {calculate}=require('../static/o2_sequential.js');
const tokens=[{token:'SOL',price:10,current_usdt:10,target:.5},{token:'LINK',price:10,current_usdt:990,target:.5}];
function amount(price,state){return calculate(tokens,{SOL:{ref382:price,c1:price,c2:price,ref786:price},LINK:{ref382:9,c1:9,c2:9,ref786:9}},[100,0,0,0],100,.5,{stageBudgets:[100,0,0,0],orderStates:{SOL:{O2C1:state}}}).amounts[0][0];}
assert(amount(9,'PROPUESTA')>0);
for(const price of [10,11])assert.equal(amount(price,'PROPUESTA'),0);
for(const state of ['CONFIRMADA','PARCIAL','EJECUTADA','FILLED'])assert.equal(amount(9,state),0);
console.log('7 purchase eligibility checks passed');
