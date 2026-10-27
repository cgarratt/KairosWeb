(function (root) {
  'use strict';
  const fractionKeys = new Set(['STRUCTURAL_USDT_TARGET',
    'O3_BTC_PROCEEDS_FRACTION','O3_USDT_PROCEEDS_FRACTION',
    'O5_BTC_PROCEEDS_FRACTION','O5_USDT_PROCEEDS_FRACTION',
    'QF_MARGIN_CAP_PER_POSITION',
    'QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL','PROXIMITY_BAND']);
  const percentDirectKeys=new Set(['TRIGGER_STRICT_GT']);
  const labels={BALANCER_MAX_PORTFOLIO_FRACTION:'Reserva Balancer: máximo del portafolio',TRADING_MAX_PORTFOLIO_FRACTION:'Reserva Trading: máximo del portafolio',DRIFT_BAND_PP:'Tolerancia de desvío del Balancer',STRUCTURAL_USDT_TARGET:'Objetivo estructural de liquidez',
    O3_BTC_PROCEEDS_FRACTION:'Ventas O3: proporción destinada a BTC',O3_USDT_PROCEEDS_FRACTION:'Ventas O3: proporción mantenida en USDT',
    O5_BTC_PROCEEDS_FRACTION:'Ventas O5: proporción propuesta para BTC',O5_USDT_PROCEEDS_FRACTION:'Ventas O5: proporción mantenida en USDT',
    O5_STAGED_TRANCHES:'Tramos de venta históricos de O5 (referencia, no editar)',
    FORECAST_O2_FIB_ALLOCATION:'Forecast O2: reparto de compras Fib 38.2 / 50 / 61.8 / 78.6',
    FORECAST_O3_FIB_ALLOCATION:'Forecast O3: reparto de ventas Fib 1.618 / 2.618 / 3.618 / 4.618',
    FORECAST_O4_FIB_ALLOCATION:'Forecast O4: reparto de recompras Fib 38.2 / 50 / 61.8 / 78.6',
    FORECAST_O5_FIB_ALLOCATION:'Forecast O5: reparto de ventas Fib 1.618 / 2.618 / 3.618 / 4.618',
    RISK_REWARD_MIN:'Relación recompensa/riesgo mínima',QF_MARGIN_CAP_PER_POSITION:'Margen máximo por posición QF',
    QF_ACCOUNT_RISK_PER_TRADE:'Riesgo máximo por operación QF',QF_ACCOUNT_RISK_TOTAL:'Riesgo agregado máximo QF',
    MAX_LEVERAGE:'Apalancamiento máximo',MAX_OPEN_POSITIONS:'Número máximo de posiciones QF',
    TRIGGER_STRICT_GT:'Umbral de activación BSI',PROXIMITY_BAND:'Distancia de proximidad para alertas'};
  for(const stage of ['O2','O3','O4','O5']){
    const levels=(stage==='O2'||stage==='O4')?[['382','38.2%'],['500','50%'],['618','61.8%'],['786','78.6%']]:[['1618','1.618'],['2618','2.618'],['3618','3.618'],['4618','4.618']];
    for(const [suffix,description] of levels){
      const idx=levels.findIndex(x=>x[0]===suffix)+1;const action=stage==='O2'||stage==='O4'?'C':'V';
      labels[`FORECAST_${stage}_FIB_${suffix}_PCT`]=`${stage}${action}${idx} · Fib ${description} · asignación`; 
    }
  }
  function scale(entry){const k=entry.key||'';
    if(/^FORECAST_O[2345]_FIB_(?:382|500|618|786|1618|2618|3618|4618)_PCT$/.test(k))return 'percent-direct';
    if(k==='DRIFT_BAND_PP')return 'pp';
    if(percentDirectKeys.has(k))return 'percent-direct';
    if(fractionKeys.has(k)||String(entry.unit||'').includes('fraction'))return 'fraction';
    if(k==='O5_STAGED_TRANCHES'||/^FORECAST_O[2345]_FIB_ALLOCATION$/.test(k))return 'percent-list';
    return 'raw';
  }
  function toDisplay(value,entry){if(value===null||value===undefined)return '';
    const s=scale(entry);
    if(s==='fraction')return String(Number((Number(value)*100).toPrecision(12)));
    if(s==='percent-list')return String(value).split(',').map(x=>x.trim()+'%').join(' · ');
    return String(value);
  }
  function fromDisplay(value,entry){const kind=scale(entry);const v=String(value).trim().replace(/%/g,'').replace(',','.');
    const k=entry.key||'';
    if(kind==='percent-list'){
      const xs=String(value).split(/[,;·]/).map(x=>x.replace(/%/g,'').trim());
      if(xs.length!==4||xs.some(x=>!/^\d+(?:\.\d+)?$/.test(x)))throw Error('Cuatro porcentajes obligatorios');
      if(Math.abs(xs.reduce((a,x)=>a+Number(x),0)-100)>0.000001)throw Error('Los cuatro tramos deben sumar 100%');
      if(k==='O5_STAGED_TRANCHES'&&xs.some(x=>!Number.isInteger(Number(x))))throw Error('Tramos O5 históricos deben ser porcentajes enteros');
      return xs.join(',');
    }
    if(!v||!/^\d+(?:\.\d+)?$/.test(v))throw Error('Número no válido');
    const n=Number(v);
    if(!Number.isFinite(n))throw Error('Valor no finito');
    if(kind==='fraction' || kind==='percent-direct'){
      if(n>100)throw Error('Porcentaje no puede superar 100%');
      return kind==='fraction'?n/100:n;
    }
    return n;
  }
  const api={scale,toDisplay,fromDisplay,labels};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.KairosFormatting=api;
})(typeof window!=='undefined'?window:globalThis);
