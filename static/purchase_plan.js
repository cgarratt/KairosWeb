/* Shared Kairos purchase plan; simulation only. */
function purchasePlan(budget,items,crypto){
  const n=items.length, weights=items.map(x=>Number(x.target)), current=items.map(x=>Number(x.current_usdt));
  const totals=weights.reduce((a,b)=>a+b,0);if(!(totals>0))return {balance:items.map(()=>0),extra:items.map(()=>0),required:0};
  const targets=weights.map(w=>w/totals);
  const required=Math.max(0,...items.map((x,i)=>targets[i]>0?current[i]/targets[i]-crypto:0));
  const balance=Array(n).fill(0),extra=Array(n).fill(0);
  const first=Math.min(budget,required);
  if(first>1e-9){
    if(budget>=required-1e-7){
      // Llega al balance exacto; todos los activos cumplen su target al final de la etapa.
      for(let i=0;i<n;i++) balance[i]=Math.max(0,targets[i]*(crypto+required)-current[i]);
    }else{
      // Balanceo parcial hacia la composición objetivo tras invertir el capital indicado.
      // No compramos activos ya sobreponderados frente a ese total objetivo.
      const gaps=items.map((x,i)=>Math.max(0,targets[i]*(crypto+first)-current[i]));
      const total=gaps.reduce((a,b)=>a+b,0);
      if(total>0) for(let i=0;i<n;i++)balance[i]=first*gaps[i]/total;
    }
  }
  const second=Math.max(0,budget-first);
  for(let i=0;i<n;i++)extra[i]=second*targets[i];
  return {balance,extra,required};
}

