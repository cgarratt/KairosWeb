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
// Draft percentages do not mutate neighboring fields: the user commits all four
// ONLY after the exact total reaches 100.00%. Accept comma decimal separator.
function validateDraft(rawValues){
  if(!Array.isArray(rawValues)||rawValues.length!==4)return {valid:false,reason:'Cuatro porcentajes requeridos',total:null};
  let ticks=[];
  for(const raw of rawValues){
    const value=String(raw).trim().replace(',', '.');
    if(!/^(?:\d{1,3})(?:\.\d{1,2})?$/.test(value))
      return {valid:false,reason:'Introduce porcentajes entre 0 y 100, con hasta 2 decimales',total:null};
    const cents=Math.round(Number(value)*100);
    if(cents<0||cents>TOTAL)
      return {valid:false,reason:'Cada porcentaje debe estar entre 0 y 100',total:null};
    ticks.push(cents);
  }
  const totalTicks=ticks.reduce((a,b)=>a+b,0);
  return {valid:totalTicks===TOTAL,total:totalTicks/100,
    values:ticks.map(t=>t/100),
    reason:totalTicks===TOTAL?'':'El total debe ser exactamente 100.00%'};
}
// Fill C1 first, then C2/C3/C4. The percentages determine tranche CAPS
// against the FULL available USDT, not a proportional split of a partial slider.
// Work in USDT cents so displayed amounts conserve the budget exactly.
// Compras slider scale: 0–100% of available USDT (physical USDT minus QF).
// No relationship to the portfolio's total market value P.
function budgetFromAvailablePercent(percent,maximum){
  const pct=Number(percent),cap=Number(maximum);
  const normalized=Number.isFinite(pct)?Math.min(100,Math.max(0,pct)):0;
  const cents=Number.isFinite(cap)?Math.max(0,Math.round(cap*100)):0;
  return Math.round(cents*normalized/100)/100;
}
function waterfall(budget,maximum,percentages){
  const limit=Math.max(0,Math.round((Number(maximum)||0)*100));
  const spend=Math.min(limit,Math.max(0,Math.round((Number(budget)||0)*100)));
  const pct=normalize(percentages);
  const capacities=allocateTicks(pct,limit);
  const allocated=[];
  let left=spend;
  for(const cap of capacities){const use=Math.min(cap,left);allocated.push(use/100);left-=use;}
  return {stageBudgets:allocated,stageCapacities:capacities.map(x=>x/100),
    selectedBudget:spend/100,remaining:Math.max(0,left/100)};
}
const api={normalize,rebalance,asFractions,validateDraft,waterfall,budgetFromAvailablePercent};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.KairosPurchaseWeights=api;
})(typeof window!=='undefined'?window:globalThis);
