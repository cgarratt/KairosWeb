/* Semáforo Fibonacci O2 - solo informativo y sin acciones sobre Sheets.
   Verde si Spot observado está en/bajo el nivel, o si se proporciona evidencia
   explícita posterior a O1 en el futuro. Nunca inferir un toque histórico
   usando un mínimo global o una ancla O1 sin fecha homologada. */
(function(root){
  'use strict';
  function classify({level,spot,postO1Low=null,postO1Verified=false}){
    const l=Number(level),s=Number(spot);
    if(!Number.isFinite(l)||l<=0||!Number.isFinite(s)||s<=0)return {status:'unknown',distance:null,source:null};
    if(postO1Verified===true && postO1Low!==null && Number.isFinite(Number(postO1Low)) && Number(postO1Low)>0 && Number(postO1Low)<=l)
      return {status:'hit',distance:(s/l-1)*100,source:'post_o1_low_verified'};
    const d=(s/l-1)*100;
    if(s<=l)return {status:'hit',distance:d,source:'spot_now'};
    if(d<=1+1e-9)return {status:'near',distance:d,source:'spot_now'};
    return {status:'pending',distance:d,source:'spot_now'};
  }
  function tooltip(result,spot,level){
    if(!result || result.status==='unknown')return 'N/D · no hay nivel o Spot válido; sin señal';
    const pct=Math.abs(result.distance).toFixed(2);
    if(result.status==='hit')return result.source==='post_o1_low_verified'
      ?'Verde · mínimo post-O1 con evidencia alcanzó el nivel (referencia no certificada)'
      :'Verde · Spot actual en o bajo el nivel ('+pct+'%); no acredita toque histórico post-O1';
    if(result.status==='near')return 'Ámbar · Spot '+pct+'% sobre el nivel; referencia simulada';
    return 'Pendiente · Spot '+pct+'% sobre el nivel; referencia simulada';
  }
  const api={classify,tooltip};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.KairosForecastLevelStatus=api;
})(typeof window!=='undefined'?window:globalThis);
