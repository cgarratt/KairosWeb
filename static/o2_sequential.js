/* O2 staged purchase simulation. No order submission or Master mutation. */
(function(root){
'use strict';
// La banda se recibe del Master PUBLICADO (DRIFT_BAND_PP), en puntos porcentuales.
function classifyDrift(weight,target,bandPP){
  const actual=Number(weight),objective=Number(target),band=Number(bandPP);
  if(!Number.isFinite(actual)||!Number.isFinite(objective)||!Number.isFinite(band)||band<0)
    return {status:'N/D',driftPP:null};
  const driftPP=(actual-objective)*100;
  return {status:driftPP>band+1e-9?'SOBRE':driftPP< -band-1e-9?'INFRA':'NEUTRAL',driftPP};
}
function calculate(tokens,levelRows,weights,budget,driftBandPP){
  const levels=levelRows||{}, n=tokens.length, w=weights.map(x=>Math.max(0,Number(x)||0)), sumW=w.reduce((a,b)=>a+b,0);
  const amounts=Array.from({length:n},()=>[0,0,0,0]);
  const prices=tokens.map(t=>{const ref=levels[t.token]||{},c1=Number(ref.c1),c2=Number(ref.c2);
    if(!(c1>0&&c2>0&&c1>c2))return [null,null,null,null];
    const rise=(c1-c2)/.118,top=c1+.5*rise;
    return [.382,.5,.618,.786].map(f=>top-f*rise);
  });
  const units=tokens.map(t=>{const spot=Number(t.price);return spot>0?Math.max(0,Number(t.current_usdt)||0)/spot:0;});
  const target=tokens.map(t=>Math.max(0,Number(t.target)||0));
  const consumed=[0,0,0,0], snapshots=[];let cash=Math.max(0,Number(budget)||0);
  for(let j=0;j<4;j++){
    const px=tokens.map((t,i)=>prices[i][j]||Number(t.price));
    const values=px.map((v,i)=>(Number.isFinite(v)&&v>0?units[i]*v:0));
    const crypto=values.reduce((a,b)=>a+b,0);
    // Estado ANTES de comprar en este tramo, con compras previas ya incorporadas.
    const preWeights=values.map(x=>crypto>0?x/crypto:NaN);
    const drift=preWeights.map((v,i)=>classifyDrift(v,target[i],driftBandPP));
    const stageBudget=Math.min(cash,Math.max(0,Number(budget)||0)*(sumW>0?w[j]/sumW:0));
    // Missing Fibonacci anchors have no executable hypothetical limit price.
    // They remain in the portfolio valuation but cannot receive a simulated fill.
    const items=tokens.map((t,i)=>({target:prices[i][j]>0?target[i]:0,current_usdt:values[i]}));
    const plan=root.purchasePlan(stageBudget,items,crypto);
    for(let i=0;i<n;i++){
      const a=prices[i][j]>0?Math.max(0,plan.balance[i]+plan.extra[i]):0;
      amounts[i][j]=a;
      if(a>0)units[i]+=a/prices[i][j];
      consumed[j]+=a;
    }
    cash=Math.max(0,cash-consumed[j]);
    snapshots.push({values,crypto,weights:preWeights,
      states:drift.map(x=>x.status),driftsPP:drift.map(x=>x.driftPP),
      spent:consumed[j],cash});
  }
  return {prices,amounts,consumed,totalByToken:amounts.map(a=>a.reduce((s,x)=>s+x,0)),spent:consumed.reduce((a,b)=>a+b,0),cash,snapshots};
}
const api={calculate,classifyDrift};if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.KairosO2Sequential=api;
})(typeof window!=='undefined'?window:globalThis);
