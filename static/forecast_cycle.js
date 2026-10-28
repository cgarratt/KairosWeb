/* Pure one-wave ledger. Same rules as kairos_gpt.forecast.simulate_wave. */
(function(root){'use strict';
const Balance=root.KairosForecastBalance||(typeof require!=='undefined'?require('./forecast_balance.js'):null);
function simulateWave(input){
 const {stage,weights,grid,qf=0,btcShare=0,coreO5Eligible=false,fee=0,deploy=1,buyCommitments=0}=input;
 const assets=input.assets.map(x=>({...x}));let cash=Number(input.cash),btcBought=0;const events=[];
 if(!['o2','o3','o4','o5'].includes(stage)||!Array.isArray(weights)||weights.length!==4||weights.some(w=>!Number.isFinite(w)||w<0)||weights.reduce((s,w)=>s+w,0)>1+1e-8||cash<qf||fee<0||fee>=1||btcShare<0||btcShare>1||deploy<0||deploy>1)throw Error('FORECAST_INPUT_INVALID');
 const buy=['o2','o4'].includes(stage),cap={T1:.3,T2:.7,T3:1};
 const pools=assets.map(a=>a.token==='BTC'?0:stage==='o3'?Math.max(0,Math.min(a.ex-(a.reserved||0),(a.hodl+a.core+a.ex)*cap[a.tier]-(a.reserved||0))):Math.max(0,a.ex-(a.reserved||0))+(coreO5Eligible?a.core:0));
 if(pools.some(p=>!Number.isFinite(p)||p<0))throw Error('FORECAST_TIER_INVALID');
 const sold=assets.map(()=>0),budget=Math.min(input.budget??(cash-qf-buyCommitments),cash-qf-buyCommitments)*deploy;
 let spent=0,grossTotal=0;
 for(let j=0;j<4;j++){
  const prices=grid[j];if(!prices||prices.length!==assets.length)throw Error('FORECAST_GRID_INVALID');
  const valid=prices.map(p=>Number.isFinite(p)&&p>0);
  const marks=assets.map((a,i)=>valid[i]?prices[i]:a.spot);
  if(marks.some(p=>!Number.isFinite(p)||p<=0))throw Error('FORECAST_PRICE_INVALID');
  if(buy){
   const amount=Math.min(budget*weights[j],Math.max(0,cash-qf-buyCommitments));
   const allocation=Balance.allocateBuys(amount,assets.map((a,i)=>({current:(a.hodl+a.core+a.ex)*marks[i],target:a.target,eligible:valid[i]})));
   assets.forEach((a,i)=>{if(valid[i]){const fill=allocation.amounts[i];a.ex+=fill/prices[i];cash-=fill;spent+=fill;}});
   events.push({budget_USDT:allocation.total,cash_after_USDT:cash});
  }else{
   const intended=assets.map((a,i)=>valid[i]?pools[i]*weights[j]*deploy*prices[i]:0);
   let amounts=intended;
   if(stage==='o3'){
    const values=assets.map((a,i)=>(a.hodl+a.core+a.ex)*marks[i]);
    amounts=Balance.allocateSales(intended.reduce((s,n)=>s+n,0),assets.map((a,i)=>({current:values[i],capacity:valid[i]?Math.min(Math.max(0,a.ex-(a.reserved||0)),Math.max(0,pools[i]-sold[i]))*prices[i]:0,target:a.target})),values.reduce((s,n)=>s+n,0),(1-fee)*btcShare).amounts;
   }
   let gross=0;
   assets.forEach((a,i)=>{if(!valid[i]||a.token==='BTC')return;
    const available=Math.max(0,a.ex-(a.reserved||0))+(stage==='o5'&&coreO5Eligible?a.core:0);
    const qty=Math.min(available,amounts[i]/prices[i]);const ex=Math.min(Math.max(0,a.ex-(a.reserved||0)),qty);
    a.ex-=ex;a.core-=qty-ex;sold[i]+=qty;gross+=qty*prices[i];
   });
   const btcIndex=assets.findIndex(a=>a.token==='BTC');if(!valid[btcIndex]&&gross>0)throw Error('FORECAST_BTC_PRICE_INVALID');
   const net=gross*(1-fee),btcAmount=net*btcShare,btcQty=btcAmount/(prices[btcIndex]||1);
   assets[btcIndex].ex+=btcQty;btcBought+=btcQty;cash+=net-btcAmount;grossTotal+=gross;
   events.push({gross_USDT:gross,btc_buy_simulated_USDT:btcAmount,cash_after_USDT:cash,o3_40pct_cap_applied:false});
  }
 }
 return {assets,cash,btcBought,spent,gross:grossTotal,events,sold};
}
const api={simulateWave};root.KairosForecastCycle=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
