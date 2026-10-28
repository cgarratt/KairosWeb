/* KairosWeb v1.4.0: simulation-only Fibonacci stage arithmetic. */
(function (root) {
  'use strict';
  const BUY_LEVELS=[.382,.5,.618,.786];
  const SELL_LEVELS=[1.618,2.618,3.618,4.618];
  const DEFAULTS={o2:[0,60,40,0],o3:[20,20,30,30],o4:[0,60,40,0],o5:[20,20,30,30]};
  function shares(v){
    if(!Array.isArray(v)||v.length!==4||v.some(x=>!Number.isFinite(Number(x))||Number(x)<0||Number(x)>100))throw Error('Se requieren cuatro porcentajes entre 0% y 100%.');
    const sum=v.reduce((s,x)=>s+Number(x),0);
    if(Math.abs(sum-100)>1e-6)throw Error('Los cuatro tramos deben sumar 100%.');
    return v.map(x=>Number(x)/100);
  }
  function budget(portfolio,physicalUsdt,qf){
    if([portfolio,physicalUsdt,qf].some(x=>!Number.isFinite(x)||x<0)||qf>physicalUsdt)throw Error('P/USDT/QF inválidos');
    const maximum=Math.max(0,physicalUsdt-qf),target=.25*portfolio;return {maximum,deployable:maximum,shortfall:Math.max(0,target-maximum),minimumTarget:target};
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
  // Shared chart/table/Forecast values. Published VALIDADO and CONFIRMADO
  // are immutable under local Fibonacci selectors or MCP candidate updates.
  function wavePath(p,selectors){
    const labels=['cl','o1','o2','o3','o4','o5'];
    const timeline=root.KairosPivotTimeline||(typeof require!=='undefined'?require('./pivot_timeline.js'):null);
    const errors=timeline.issues({cycle_low:p.published_cl??p.cycle_low,cl_date:p.published_cl_date??p.cl_date,waves:p.waves});
    if(errors.length)return {token:p.token,values:null,locked:[],statuses:{},dates:{},state:'CRONOLOGIA_INVALIDA',timeline_issues:errors};
    const positive=x=>x==null||x===''?null:(Number.isFinite(Number(x))&&Number(x)>0?Number(x):null);
    const approved=s=>s==='VALIDADO'||s==='CONFIRMADO';
    const fixed={},statuses={},dates={},locked=[];
    for(const wave of labels){
      const row=wave==='cl'?{price:p.published_cl,date:p.published_cl_date,status:p.cl_status}:(p.waves?.[wave]||{});
      const status=String(row.status||'PROPUESTO').toUpperCase();
      if(approved(status)){
        const price=positive(row.price);
        if(price===null)return {token:p.token,values:null,locked,statuses,dates,state:'PIVOTE_PUBLICADO_SIN_PRECIO'};
        fixed[wave]=price;locked.push(wave);statuses[wave]=status;dates[wave]=row.date||null;
      }else{statuses[wave]='PROPUESTO';dates[wave]=row.date||null;}
    }
    const cl=fixed.cl??positive(p.cycle_low),o1=fixed.o1??positive(p.o1);
    if(cl===null||o1===null||o1<=cl)return {token:p.token,values:null,locked,statuses,dates,state:cl!==null&&o1!==null?'ANCLAS_INCOMPATIBLES':'N/D'};
    const f=wave=>{const r=Number(selectors?.[wave]);return Number.isFinite(r)&&r>0?r:null;};
    if(['o2','o3','o4','o5'].some(w=>fixed[w]===undefined&&f(w)===null))throw Error('FIBONACCI_CONTROL_INVALIDO');
    const o2=fixed.o2??(o1-f('o2')*(o1-cl));
    const o3=fixed.o3??(o2+f('o3')*(o1-cl));
    const o4=fixed.o4??(o3-f('o4')*(o3-o2));
    const o5=fixed.o5??(o4+f('o5')*(o3-o2));
    const values=[cl,o1,o2,o3,o4,o5];
    let state=values.every(x=>Number.isFinite(x)&&x>0)&&cl<o1&&o2<o1&&o3>o2&&o4<o3&&o5>o4?'ESCENARIO':'ESTRUCTURA_INCOMPATIBLE';
    if(state==='ESCENARIO'&&o4<=o1)state='SOLAPAMIENTO O4 / O1';
    if(state==='ESCENARIO'&&locked.length)state='FIJOS: '+locked.map(w=>w.toUpperCase()+' '+statuses[w]).join(', ');
    return {token:p.token,values,locked,statuses,dates,state};
  }
  const api={BUY_LEVELS,SELL_LEVELS,DEFAULTS,shares,budget,scenarioBuyPrices,scenarioSellPrices,wavePath};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.KairosForecastFibo=api;
})(typeof window!=='undefined'?window:globalThis);
