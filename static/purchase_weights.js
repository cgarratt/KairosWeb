/* Editable Fibonacci split for one local BUY simulation only.
   Percentages always total 100%; no persistence, network calls or orders. */
(function(root){
'use strict';
const PRECISION=100; // 0.01 percentage points
const TOTAL=100*PRECISION;
function clampPct(value){
  const n=Number(value);
  return Number.isFinite(n)?Math.min(100,Math.max(0,n)):0;
}
function allocateTicks(values,total){
  const safe=values.map(x=>Math.max(0,Number(x)||0));
  const sum=safe.reduce((a,b)=>a+b,0);
  const weights=sum>0?safe.map(x=>x/sum):safe.map(()=>1/safe.length);
  const raw=weights.map(x=>x*total);
  const out=raw.map(Math.floor);
  let remainder=total-out.reduce((a,b)=>a+b,0);
  const order=raw.map((x,i)=>({i,fraction:x-out[i]}))
    .sort((a,b)=>b.fraction-a.fraction || a.i-b.i);
  for(let k=0;k<remainder;k++)out[order[k%order.length].i]++;
  return out;
}
function normalize(values){
  if(!Array.isArray(values)||values.length!==4)throw Error('Four Fibonacci levels required');
  return allocateTicks(values.map(clampPct),TOTAL).map(t=>t/PRECISION);
}
function rebalance(percentages,changedIndex,newPercent){
  if(!Number.isInteger(changedIndex)||changedIndex<0||changedIndex>3)
    throw Error('Invalid Fibonacci tranche index');
  if(newPercent===null || String(newPercent).trim()==='' || !Number.isFinite(Number(newPercent)))
    return normalize(percentages);
  const previous=normalize(percentages).map(n=>Math.round(n*PRECISION));
  const edited=Math.round(clampPct(newPercent)*PRECISION);
  const remaining=TOTAL-edited;
  const others=[0,1,2,3].filter(i=>i!==changedIndex);
  const redistributed=allocateTicks(others.map(i=>previous[i]),remaining);
  const result=[0,0,0,0];result[changedIndex]=edited;
  others.forEach((i,k)=>{result[i]=redistributed[k]});
  return result.map(t=>t/PRECISION);
}
function asFractions(percentages){return normalize(percentages).map(p=>p/100)}
const api={normalize,rebalance,asFractions};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.KairosPurchaseWeights=api;
})(typeof window!=='undefined'?window:globalThis);
