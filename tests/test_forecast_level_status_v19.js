const assert=require('node:assert/strict');
const mod=require('../static/forecast_level_status.js');
function c(x){return mod.classify(x)}
assert.equal(c({level:100,spot:99}).status,'hit');
assert.equal(c({level:100,spot:100}).status,'hit');
assert.equal(c({level:100,spot:100.2}).status,'near');
assert.equal(c({level:100,spot:101}).status,'near');
assert.equal(c({level:100,spot:101.01}).status,'pending');
assert.equal(c({level:0,spot:50}).status,'unknown');
assert.equal(c({level:null,spot:50}).status,'unknown');
assert.equal(c({level:100,spot:NaN}).status,'unknown');
assert.equal(c({level:100,spot:105,postO1Low:99,postO1Verified:false}).status,'pending');
assert.equal(c({level:100,spot:105,postO1Low:99,postO1Verified:true}).status,'hit');
assert.equal(c({level:100,spot:105,postO1Low:99,postO1Verified:true}).source,'post_o1_low_verified');
assert.match(mod.tooltip(c({level:100,spot:99}),99,100),/no acredita toque histórico/);
console.log('PASS nivel Fibonacci v1.9: verde, ámbar 1%, N/D, histórico solo con evidencia');
