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

// Forecast cycle SVG: current Spot MCP is a purely informational overlay.
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../templates/forecast.html'),'utf8');
const fragment=html.split('function drawCurve(waves){')[1].split('\n\nfunction runCycle(){')[0];
assert.ok(fragment,'missing wave chart code');
class TestSVG {
  constructor(tag){this.tag=tag;this.attrs={};this.children=[];this.textContent='';}
  setAttribute(k,v){this.attrs[k]=String(v)}
  appendChild(x){this.children.push(x);return x}
  replaceChildren(){this.children=[]}
}
const svg=new TestSVG('svg');
const selected={value:'BTC'};const info={textContent:''};
const fc={tokens:[{token:'BTC',price:150}],generated_at:'2026-10-21T12:00:00Z'};
const vmContext={fc,document:{createElementNS:(ns,tag)=>new TestSVG(tag)},
  $:(id)=>({'waves-chart':svg,'chart-token':selected,'chart-info':info})[id],
  price:(p)=>'$'+Number(p).toFixed(2)};
vm.runInNewContext('function drawCurve(waves){'+fragment,vmContext);
const wave={token:'BTC',values:[100,140,110,160,130,180],locked:['cl'],statuses:{cl:'VALIDADO'},dates:{}};
vmContext.drawCurve([wave]);
const line=svg.children.find(n=>n.attrs['data-spot-reference']==='binance-mcp');
assert.ok(line,'Spot line must appear when MCP quote exists');
assert.ok(Math.abs(Number(line.attrs.y1)-133.25)<.0001);
assert.match(info.textContent,/Spot MCP/);
assert.ok(svg.children.some(n=>n.tag==='polyline'),'wave progression unchanged');
fc.tokens[0].price=250;vmContext.drawCurve([wave]);
const outside=svg.children.find(n=>n.attrs['data-spot-reference']==='binance-mcp');
assert.ok(Number(outside.attrs.y1)>=62&&Number(outside.attrs.y1)<=252,'out-of-range price rescaled into plot');
fc.tokens[0].price=null;vmContext.drawCurve([wave]);
assert.ok(!svg.children.some(n=>n.attrs['data-spot-reference']==='binance-mcp'),'missing Spot must not be fabricated');
assert.match(info.textContent,/Spot MCP N\/D/);
console.log('PASS Forecast: line Spot MCP dynamic, out of range, missing price N/D');
