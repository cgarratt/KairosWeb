/* Kairos VENTAS · simulación sin side effects. Parámetros SIEMPRE del Master PUBLICADO. */
(function(root){
  'use strict';
  const EPS=1e-8, capsTier={T1:.30,T2:.70,T3:1};
  function finite(x,label){const n=Number(x);if(!Number.isFinite(n)||n<0)throw Error('DATA ERROR: '+label);return n;}
  function project(ideal,caps,amount){
    if(amount<=EPS)return ideal.map(()=>0);
    if(caps.reduce((s,x)=>s+x,0)+EPS<amount)throw Error('DATA ERROR: insuficiente Exchange');
    let lo=Math.min(...ideal.map(v=>-v))-Math.max(0,...caps)-amount;
    let hi=Math.max(...ideal.map((v,i)=>caps[i]-v))+amount;
    for(let j=0;j<110;j++){
      const mid=(lo+hi)/2,used=ideal.reduce((s,v,i)=>s+Math.min(caps[i],Math.max(0,v+mid)),0);
      if(used<amount)lo=mid;else hi=mid;
    }
    const out=ideal.map((v,i)=>Math.min(caps[i],Math.max(0,v+(lo+hi)/2)));
    let delta=amount-out.reduce((s,x)=>s+x,0);
    if(Math.abs(delta)>1e-7)for(let i=0;i<out.length;i++){
      let change=Math.max(-out[i],Math.min(caps[i]-out[i],delta));out[i]+=change;delta-=change;
      if(Math.abs(delta)<=1e-7)break;
    }
    return out;
  }
  function calculate(items,physicalCash,targetPct,bandPp,qf=0){
    const cash=finite(physicalCash,'USDT'),target=finite(targetPct,'target %'),band=finite(bandPp,'banda'),reserve=finite(qf,'QF');
    if(items.length!==12||target>100||band>100||reserve>cash)throw Error('DATA ERROR: ventas parámetros');
    const unique=new Set(items.map(x=>x.token));if(unique.size!==12||!unique.has('BTC'))throw Error('DATA ERROR: universo 12 tokens');
    const targets=items.map(x=>finite(x.target,'target token'));
    if(Math.abs(targets.reduce((s,x)=>s+x,0)-1)>1e-8)throw Error('DATA ERROR: suma de targets');
    const prices=items.map(x=>finite(x.price,'MCP Spot'));
    const values=items.map((x,i)=>finite(x.units,'units')*prices[i]);
    const limits=items.map((x,i)=>{
      const units=finite(x.units,'total units'),exchange=finite(x.exchange_units,'Exchange units'),reserved=finite(x.reserved_sell_units||0,'reserved SELL');
      if(!Object.hasOwn(capsTier,x.tier)||prices[i]<=0||exchange>units+EPS)throw Error('DATA ERROR: Tier/Spot/Exchange');
      return x.token==='BTC'?0:prices[i]*Math.max(0,Math.min(exchange-reserved,units*capsTier[x.tier]-reserved));
    });
    const crypto=values.reduce((s,x)=>s+x,0),P=crypto+cash;
    if(crypto<=EPS)throw Error('DATA ERROR: manga cripto 0');
    const requested=Math.max(0,target/100*P-cash);
    const permitted=Math.min(requested,limits.reduce((s,x)=>s+x,0));
    const stage1=items.map(()=>0),now=values.slice(),orders=[];
    let left=permitted;
    for(let k=0;k<256&&left>EPS;k++){
      const sleeve=now.reduce((s,x)=>s+x,0);
      if(sleeve<=EPS)break;
      const candidates=items.map((x,i)=>({i,drift:100*(now[i]/sleeve-targets[i]),room:limits[i]-stage1[i]}))
        .filter(x=>items[x.i].token!=='BTC'&&x.drift>band+1e-9&&x.room>EPS&&targets[x.i]<1)
        .sort((a,b)=>b.drift-a.drift||a.i-b.i);
      if(!candidates.length)break;
      const {i,room}=candidates[0];
      const toTarget=Math.max(0,(now[i]-targets[i]*sleeve)/(1-targets[i]));
      const take=Math.min(left,room,toTarget);if(take<=EPS)break;
      stage1[i]+=take;now[i]-=take;left-=take;
      orders.push({stage:1,token:items[i].token,usdt:take,units:take/prices[i],price:prices[i]});
    }
    const rooms=limits.map((x,i)=>Math.max(0,x-stage1[i]));
    const stage2Amount=Math.min(left,rooms.reduce((s,x)=>s+x,0));
    let stage2=items.map(()=>0);
    if(stage2Amount>EPS){
      const finalCrypto=crypto-stage1.reduce((s,x)=>s+x,0)-stage2Amount;
      if(finalCrypto<=EPS)throw Error('DATA ERROR: manga cripto final cero');
      stage2=project(now.map((x,i)=>x-targets[i]*finalCrypto),rooms,stage2Amount);
      items.map((x,i)=>({i,amount:stage2[i]})).filter(x=>x.amount>EPS)
        .sort((a,b)=>b.amount-a.amount||a.i-b.i).forEach(x=>orders.push({stage:2,token:items[x.i].token,usdt:x.amount,units:x.amount/prices[x.i],price:prices[x.i]}));
    }
    const sales=stage1.map((x,i)=>x+stage2[i]),total=sales.reduce((s,x)=>s+x,0),cryptoAfter=crypto-total;
    if(cryptoAfter<=EPS||sales.some((v,i)=>v>limits[i]+1e-5))throw Error('DATA ERROR: restricciones de ventas');
    return {status:requested-total<.01?'TARGET_REACHED':'CAPACITY_LIMITED',target_percent:target,P,cash_before:cash,cash_after:cash+total,
      cash_pct_after:100*(cash+total)/P,requested_usdt:requested,stage1_usdt:stage1.reduce((s,x)=>s+x,0),
      stage2_usdt:stage2.reduce((s,x)=>s+x,0),total_usdt:total,unmet_usdt:Math.max(0,requested-total),
      positions:items.map((x,i)=>({token:x.token,stage1_usdt:stage1[i],stage2_usdt:stage2[i],sell_usdt:sales[i],sell_units:sales[i]/prices[i],
        before_pct:100*values[i]/crypto,after_pct:100*(values[i]-sales[i])/cryptoAfter,target_pct:100*targets[i],cap_usdt:limits[i]})),
      orders:orders.map((x,i)=>({...x,priority:i+1})),simulated:true};
  }
  root.KairosSalesOptimizer={calculate};
})(typeof window!=='undefined'?window:globalThis);
