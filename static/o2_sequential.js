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
// Visual traffic light for positive simulated BUY fills only, based on the
// weight AFTER the same tranche. Drift thresholds are percentage POINTS.
// This does not modify trade eligibility: INFRA/targets/QF stay independent.
function postBuySemaphore(amount,postWeight,targetWeight,relativeBandPct=null){
  const fill=Number(amount),post=Number(postWeight),target=Number(targetWeight);
  if(!Number.isFinite(fill)||fill<0.005 || !Number.isFinite(post)||post<0 ||
     !Number.isFinite(target)||target<0 || target>1 || post>1)
    return {state:'none',driftPP:null};
  const driftPP=100*(post-target);
  if(relativeBandPct!==null && target>0){
    const driftRelativePct=100*(post/target-1),band=Number(relativeBandPct);
    if(!Number.isFinite(band)||band<0)return {state:'none',driftPP:null};
    return {state:Math.abs(driftRelativePct)<=band+1e-8?'green':Math.abs(driftRelativePct)<=2*band+1e-8?'amber':'red',driftPP,driftRelativePct};
  }
  const epsilon=1e-8; // avoid float noise at exactly target or -1 pp
  if(driftPP>=-epsilon)return {state:'green',driftPP};
  if(driftPP>=-1-epsilon)return {state:'amber',driftPP};
  return {state:'red',driftPP};
}
function proportionalByVenue(gaps,venues,cash,budget){
  const valid=x=>typeof x==='number'&&Number.isFinite(x)&&x>=0;
  if(!Array.isArray(gaps)||gaps.length!==venues.length||gaps.some(x=>!valid(x))||!valid(budget)||!cash||typeof cash!=='object'||Object.values(cash).some(x=>!valid(x)))throw Error('Invalid venue cash/deficit');
  const free={...cash},alloc=gaps.map(()=>0);
  for(let round=0;round<gaps.length+Object.keys(free).length+2;round++){
    const remaining=Math.max(0,budget-alloc.reduce((a,b)=>a+b,0));
    const room=gaps.map((x,i)=>(free[venues[i]]||0)>1e-10?Math.max(0,x-alloc[i]):0);
    const total=room.reduce((a,b)=>a+b,0);if(remaining<=1e-10||total<=1e-10)break;
    const take=Math.min(remaining,total),proposals=room.map(x=>take*x/total),demand={};
    proposals.forEach((x,i)=>{demand[venues[i]]=(demand[venues[i]]||0)+x});
    const delta=proposals.map((p,i)=>demand[venues[i]]>0?p*Math.min(1,(free[venues[i]]||0)/demand[venues[i]]):0);
    if(delta.reduce((a,b)=>a+b,0)<=1e-10)break;
    delta.forEach((x,i)=>{alloc[i]+=x});
    Object.keys(free).forEach(v=>{free[v]=Math.max(0,free[v]-delta.reduce((a,x,i)=>a+(venues[i]===v?x:0),0))});
  }
  return {alloc,cash:free};
}
function projectedByVenue(values,targets,permitted,venues,cash,budget){
 const crypto=values.reduce((a,b)=>a+b,0),ceiling=Math.min(budget,Object.values(cash).reduce((a,b)=>a+b,0));
 const plan=spend=>proportionalByVenue(values.map((v,i)=>permitted[i]?Math.max(0,targets[i]*(crypto+spend)-v):0),venues,cash,spend);
 let result=plan(ceiling);if(result.alloc.reduce((a,b)=>a+b,0)>=ceiling-1e-8)return result;
 let lo=0,hi=ceiling;for(let k=0;k<80;k++){const mid=(lo+hi)/2,r=plan(mid);if(r.alloc.reduce((a,b)=>a+b,0)>=mid-1e-9)lo=mid;else hi=mid;}
 return plan(lo);
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
  // Presupuesto hipotético: 100% repartido entre C1/C2/C3/C4 según pesos
  // aprobados O2/O4, INDEPENDIENTEMENTE de cuántos tokens sean comprables.
  // La ejecución simulada posterior respeta INFRA, precios válidos y objetivos.
  const plannedBudget=Math.max(0,Number(budget)||0);
  const targetSum=target.reduce((a,b)=>a+b,0);
  const stageMix=[0,0,0,0];
  for(let i=0;i<n;i++)for(let j=0;j<4;j++)
    stageMix[j]+=targetSum>0?(target[i]/targetSum)*stageWeights[i][j]:0;
  const totalMix=stageMix.reduce((a,b)=>a+b,0);
  const defaults=sumW>0?w.map(x=>x/sumW):[0,0,0,0];
  const normalizedMix=totalMix>0?stageMix.map(v=>v/totalMix):defaults;
  const stageBudgets=normalizedMix.map(v=>plannedBudget*v);
  // Avoid carrying floating point residue outside the 100% envelope.
  stageBudgets[3]=Math.max(0,plannedBudget-stageBudgets[0]-stageBudgets[1]-stageBudgets[2]);
  // Optional scenario-only waterfall from the UI: staged caps are computed
  // against full cash minus QF. No redistribution when tokens are blocked.
  if(policy.stageBudgets!==undefined){
    const planned=policy.stageBudgets;
    if(!Array.isArray(planned)||planned.length!==4||planned.some(x=>!Number.isFinite(Number(x))||Number(x)<0))
      throw Error('Four nonnegative planned tranche budgets required');
    const sum=planned.reduce((a,b)=>a+Number(b),0);
    if(sum>plannedBudget+0.011)
      throw Error('Stage budgets cannot exceed slider-selected USDT');
    for(let j=0;j<4;j++)stageBudgets[j]=Number(planned[j]);
  }
  const consumed=[0,0,0,0], snapshots=[];let cash=plannedBudget;
  let venueCash={...(policy.venueFreeUSDT||{})};
  const venueInitial={...venueCash};
  const venues=tokens.map(t=>{const v=t.venue||policy.tokenVenues?.[t.token];return t.token==='HYPE'&&v==='Hyperliquid'?null:v;});
  for(let j=0;j<4;j++){
    const px=tokens.map((t,i)=>prices[i][j]||Number(t.price));
    const values=px.map((v,i)=>(Number.isFinite(v)&&v>0?units[i]*v:0));
    const crypto=values.reduce((a,b)=>a+b,0);
    // Estado ANTES de comprar en este tramo, con compras previas ya incorporadas.
    const preWeights=values.map(x=>crypto>0?x/crypto:NaN);
    const drift=preWeights.map((v,i)=>classifyDrift(v,target[i],policy.relativeBandPct!==undefined?Number(policy.relativeBandPct)*target[i]:bandPP));
    // The four theoretical tranches ALWAYS sum to the full slider budget.
    // A structurally blocked or overweight token cannot diminish the PLAN;
    // its unspent portion remains physical USDT, not an invented fill.
    const stageBudget=Math.min(cash,stageBudgets.slice(0,j+1).reduce((a,b)=>a+b,0)-consumed.reduce((a,b)=>a+b,0));
    // Missing Fibonacci anchors have no executable hypothetical limit price.
    // They remain in the portfolio valuation but cannot receive a simulated fill.
    // Canonical Balancer buys: INFRA only (DRIFT_BAND_PP from published
    // 12_PARAMETROS_KAIROS), with maximum fill capped at the target weight.
    // Includes units bought in earlier steps and values all positions at this
    // step's prices. Tokens missing Fib anchors never receive liquidity.
    const permitted=tokens.map((t,i)=>{
      const stage=(policy.modes?.[t.token]==='O4'?'O4':'O2')+'C'+(j+1);
      const state=policy.orderStates?.[t.token]?.[stage]||'PROPUESTA';
      return stageWeights[i][j]>0 && prices[i][j]>0 && prices[i][j]<Number(t.price) && state==='PROPUESTA' && allowed[i] && drift[i].status==='INFRA';
    });
    const gap0=permitted.map((yes,i)=>yes?Math.max(0,target[i]*crypto-values[i]):0);
    const distribution=projectedByVenue(values,target,permitted,venues,venueCash,stageBudget);
    venueCash=distribution.cash;
    for(let i=0;i<n;i++){
      const a=distribution.alloc[i];
      amounts[i][j]=a;
      if(a>0)units[i]+=a/prices[i][j];
      consumed[j]+=a;
    }
    cash=Math.max(0,cash-consumed[j]);
    const postValues=px.map((p,i)=>Number.isFinite(p)&&p>0?units[i]*p:0);
    const postCrypto=postValues.reduce((a,b)=>a+b,0);
    const postWeights=postValues.map(v=>postCrypto>0?v/postCrypto:NaN);
    snapshots.push({values,crypto,weights:preWeights,postValues,postCrypto,postWeights,
      states:drift.map(x=>x.status),driftsPP:drift.map(x=>x.driftPP),
      spent:consumed[j],cash,venueCashRemaining:{...venueCash}});
  }
  return {venueCashInitial:venueInitial,venueCashRemaining:venueCash,allocationPolicy:"PROPORTIONAL_DEFICIT_BY_VENUE",prices,amounts,stageBudgets,unallocated:Math.max(0,plannedBudget-consumed.reduce((a,b)=>a+b,0)),consumed,totalByToken:amounts.map(a=>a.reduce((s,x)=>s+x,0)),spent:consumed.reduce((a,b)=>a+b,0),cash,snapshots};
}
const api={calculate,classifyDrift,postBuySemaphore,proportionalByVenue,projectedByVenue};if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.KairosO2Sequential=api;
})(typeof window!=='undefined'?window:globalThis);
