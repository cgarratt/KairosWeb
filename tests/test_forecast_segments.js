const assert=require('node:assert/strict');
const {STAGES,buildForecastSegments}=require('../static/forecast_segments.js');
function near(a,b){assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`)}
const waves=[
 {token:'BTC',values:[5,15,10,25,18,36],state:'ESCENARIO'},
 {token:'SOL',values:null,state:'N/D'}
];
const tokens=[
 {token:'BTC',price:12,units:2,current_usdt:24},
 {token:'SOL',price:3,units:10,current_usdt:30}
];
const stages=buildForecastSegments(waves,tokens,40);
assert.equal(stages.length,4);
assert.equal(STAGES[0].name,'O1 → O2');
assert.equal(STAGES[3].name,'O4 → O5');
for(let i=0;i<4;i++){
 const s=stages[i],a=s.rows[0],b=s.rows[1];
 assert.equal(s.rows.length,2);
 assert.equal(b.state,'SPOT_FIJO_ND');
 assert.equal(b.end_price,null);
 near(b.end_usdt,30);
 near(s.points[0].liquidity_usdt,40);
 for(const p of s.points) near(p.portfolio_usdt,p.crypto_usdt+p.liquidity_usdt);
 near(s.total.start_crypto,a.start_usdt+b.start_usdt);
 near(s.total.end_crypto,a.end_usdt+b.end_usdt);
 near(s.total.delta,s.total.end_crypto-s.total.start_crypto);
 if(i>0) near(stages[i-1].total.end_portfolio,s.total.start_portfolio);
}
// Reversals on falling segments, appreciation on rising segments
assert.ok(stages[0].total.delta<0);
assert.ok(stages[1].total.delta>0);
assert.ok(stages[2].total.delta<0);
assert.ok(stages[3].total.delta>0);
assert.throws(()=>buildForecastSegments(waves,tokens,-1),/SCENARIO_INPUT_INVALID/);
console.log('PASS: 4 tramos, continuidad, liquidez fija, totales, token N/D y cambios de valor');
