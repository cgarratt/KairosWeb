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
function calculate(tokens,levelRows,weights,budget,driftBandPP,policy={}){
  const levels=levelRows||{}, n=tokens.length, w=weights.map(x=>Math.max(0,Number(x)||0)), sumW=w.reduce((a,b)=>a+b,0);
  const bandPP=(driftBandPP===undefined||driftBandPP===null)?1:driftBandPP;
  const strict=policy.requireEligibility===true;
  const allowed=tokens.map(t=>!strict || policy.eligibility?.[t.token]===true);
  const stageWeights=tokens.map(t=>{const v=policy.weightsByToken?.[t.token]||weights;
    const arr=v.map(x=>Math.max(0,Number(x)||0));const sum=arr.reduce((a,b)=>a+b,0);
    return sum>0?arr.map(x=>x/sum):[0,0,0,0];});
  const amounts=Array.from({length:n},()=>[0,0,0,0]);
  // Prices MUST arrive from published/candidate WEEKLY CL->O1; NEVER invert
  // old C1/C2 (50/61.8) to fabricate a structural wave pivot.
  const prices=tokens.map((t,i)=>{
    const ref=levels[t.token]||{};
    const arr=['ref382','c1','c2','ref786'].map(k=>Number(ref[k]));
    return allowed[i]&&arr.every(x=>Number.isFinite(x)&&x>0) ? arr : [null,null,null,null];
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
    const drift=preWeights.map((v,i)=>classifyDrift(v,target[i],bandPP));
    // Blocked-token target shares are NOT redistributed.  That cash remains physical USDT.
    const stageBudget=strict
      ?Math.min(cash,Math.max(0,Number(budget)||0)*tokens.reduce((s,t,i)=>s+(prices[i][j]>0&&allowed[i]?target[i]*stageWeights[i][j]:0),0))
      :Math.min(cash,Math.max(0,Number(budget)||0)*(sumW>0?w[j]/sumW:0));
    // Missing Fibonacci anchors have no executable hypothetical limit price.
    // They remain in the portfolio valuation but cannot receive a simulated fill.
    // Canonical Balancer buys: INFRA only (DRIFT_BAND_PP from published
    // 12_PARAMETROS_KAIROS), with maximum fill capped at the target weight.
    // Includes units bought in earlier steps and values all positions at this
    // step's prices. Tokens missing Fib anchors never receive liquidity.
    const permitted=tokens.map((_,i)=>prices[i][j]>0 && allowed[i] && drift[i].status==='INFRA');
    const gap0=permitted.map((yes,i)=>yes?Math.max(0,target[i]*crypto-values[i]):0);
    const g0=gap0.reduce((a,b)=>a+b,0);
    const targetShare=permitted.reduce((a,yes,i)=>a+(yes?target[i]:0),0);
    // Buying changes the crypto sleeve denominator. Solve for the spend
    // that reaches targets without moving an asset from INFRA to SOBRE.
    const maxBalancedSpend=targetShare>=1-1e-10?stageBudget:g0/(1-targetShare);
    const stageSpend=Math.min(stageBudget,Math.max(0,maxBalancedSpend));
    const headroom=gap0.map((gap,i)=>permitted[i]?Math.max(0,gap+target[i]*stageSpend):0);
    const headroomTotal=headroom.reduce((a,b)=>a+b,0);
    for(let i=0;i<n;i++){
      const a=permitted[i]&&headroomTotal>1e-10
        ?Math.min(headroom[i],stageSpend*headroom[i]/headroomTotal):0;
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
