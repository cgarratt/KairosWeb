/* Kairos Forecast: deterministic simulation-only portfolio allocation engine.
 * These functions have no network calls, exchange actions, or persistence.
 */
(function(root){
 'use strict';
 const EPS=1e-8;
 const positive=n=>Math.max(0,Number(n)||0);
 function allocateBuys(budget,items){
   // items: {current, target, eligible}; current values all crypto at the current hypothetical price.
   budget=positive(budget);
   const total=items.reduce((s,x)=>s+positive(x.current),0);
   const eligible=items.map(x=>Boolean(x.eligible)&&positive(x.target)>0);
   const out=items.map(()=>0), balance=items.map(()=>0), extra=items.map(()=>0);
   const gaps=items.map((x,i)=>eligible[i]?positive(positive(x.target)*(total+budget)-positive(x.current)):0);
   const gapTotal=gaps.reduce((a,b)=>a+b,0);
   const initial=Math.min(budget,gapTotal);
   if(gapTotal>EPS)for(let i=0;i<items.length;i++)balance[i]=initial*gaps[i]/gapTotal;
   const rest=positive(budget-initial),wt=items.reduce((s,x,i)=>s+(eligible[i]?positive(x.target):0),0);
   if(rest>EPS&&wt>EPS)for(let i=0;i<items.length;i++)if(eligible[i])extra[i]=rest*positive(items[i].target)/wt;
   for(let i=0;i<items.length;i++)out[i]=balance[i]+extra[i];
   return {amounts:out,balance,extra,total:out.reduce((a,b)=>a+b,0),unfilled:wt>EPS?0:budget};
 }
 function allocateSales(budget,items,totalCrypto,btcShare){
   // Minimise squared target drift with a water-filling solution, subject to per-token sell caps.
   // items: {current,capacity,target}; protected HODL and BTC are excluded by caller.
   budget=positive(budget);totalCrypto=positive(totalCrypto);btcShare=Number(btcShare);
   if(!Number.isFinite(btcShare)||btcShare<0||btcShare>1)throw Error('Porcentaje BTC inválido');
   const cap=items.map(x=>Math.min(positive(x.capacity),positive(x.current)));
   const actual=Math.min(budget,cap.reduce((a,b)=>a+b,0));
   if(actual<=EPS)return {amounts:items.map(()=>0),total:0,unfilled:budget};
   const after=positive(totalCrypto-(1-btcShare)*actual);
   const over=items.map(x=>positive(x.current)-positive(x.target)*after);
   const weights=items.map(x=>Math.max(positive(x.target),1e-9));
   // x_i = clamp(over_i - lambda * target_i, 0, maxSell_i).
   let low=Infinity,high=-Infinity;
   for(let i=0;i<items.length;i++){
     low=Math.min(low,(over[i]-cap[i])/weights[i]);
     high=Math.max(high,over[i]/weights[i]);
   }
   for(let n=0;n<90;n++){
     const mid=(low+high)/2;
     let amount=0;
     for(let i=0;i<items.length;i++)amount+=Math.min(cap[i],Math.max(0,over[i]-mid*weights[i]));
     if(amount>actual)low=mid;else high=mid;
   }
   const out=items.map((x,i)=>Math.min(cap[i],Math.max(0,over[i]-high*weights[i])));
   let missing=actual-out.reduce((a,b)=>a+b,0);
   // Correct only floating-point residue, without selling more than eligible units.
   if(missing>EPS)for(let i=0;i<out.length&&missing>EPS;i++){
     const x=Math.min(missing,cap[i]-out[i]);out[i]+=x;missing-=x;
   }
   const sold=out.reduce((a,b)=>a+b,0);
   return {amounts:out,total:sold,unfilled:Math.max(0,budget-sold)};
 }
 function drifts(items){
   const total=items.reduce((s,x)=>s+positive(x.current),0);
   return items.map(x=>({token:x.token,target:positive(x.target)*100,actual:total>EPS?100*positive(x.current)/total:0,drift:total>EPS?100*(positive(x.current)/total-positive(x.target)):0}));
 }
 const api={allocateBuys,allocateSales,drifts};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 root.KairosForecastBalance=api;
})(typeof window!=='undefined'?window:globalThis);
