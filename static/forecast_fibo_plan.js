/* KairosWeb v1.4.0: simulation-only Fibonacci stage arithmetic. */
(function (root) {
  'use strict';
  const BUY_LEVELS=[.382,.5,.618,.786];
  const SELL_LEVELS=[1.618,2.618,3.618,4.618];
  const DEFAULTS={o2:[0,60,40,0],o3:[40,30,20,10],o4:[0,60,40,0],o5:[20,20,30,30]};
  function shares(v){
    if(!Array.isArray(v)||v.length!==4||v.some(x=>!Number.isFinite(Number(x))||Number(x)<0||Number(x)>100))throw Error('Se requieren cuatro porcentajes entre 0% y 100%.');
    const sum=v.reduce((s,x)=>s+Number(x),0);
    if(Math.abs(sum-100)>1e-6)throw Error('Los cuatro tramos deben sumar 100%.');
    return v.map(x=>Number(x)/100);
  }
  function budget(portfolio,physicalUsdt,qf){
    if([portfolio,physicalUsdt,qf].some(x=>!Number.isFinite(x)||x<0)||qf>physicalUsdt)throw Error('P/USDT/QF inválidos');
    const maximum=.25*portfolio;return {maximum,deployable:Math.min(maximum,Math.max(0,physicalUsdt-qf)),shortfall:Math.max(0,maximum-(physicalUsdt-qf))};
  }
  function scenarioBuyPrices(w,step){
    if(!w||!w.values)return null;
    const [cl,o1,o2,o3,o4]=w.values;
    if(step==='o2'){
      const rise=o1-cl;return BUY_LEVELS.map(f=>o1-f*rise);
    }
    if(step==='o4'){
      const diff=o3-o2;return BUY_LEVELS.map(f=>o3-f*diff);
    }
    throw Error('Onda no permitida');
  }
  function scenarioSellPrices(w,step){
    if(!w||!w.values)return null;
    const [cl,o1,o2,o3,o4]=w.values;
    if(step==='o3')return SELL_LEVELS.map(f=>o2+f*(o1-cl));
    if(step==='o5')return SELL_LEVELS.map(f=>o4+f*(o3-o2));
    throw Error('Onda no permitida');
  }
  const api={BUY_LEVELS,SELL_LEVELS,DEFAULTS,shares,budget,scenarioBuyPrices,scenarioSellPrices};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.KairosForecastFibo=api;
})(typeof window!=='undefined'?window:globalThis);
