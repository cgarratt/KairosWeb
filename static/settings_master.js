(() => {
  'use strict';
  const titles={units:'Maestro de unidades',targets:'Objetivos y Tiers',tier_custody:'Custodia por Tier',
    liquidity:'Liquidez por venue',parameters:'Parámetros y plan de ventas',pivots:'Pivotes y referencias'};
  const desc={units:'02_POSICIONES · HODL, Core, Exchange y costo promedio. Compras confirmadas a Exchange; evidencias obligatorias.',
    targets:'02_POSICIONES · porcentajes de la manga cripto excluyendo USDT. Los 12 targets deben sumar 100%.',
    tier_custody:'04_CUSTODIA · distribuciones para Forecast; solo simulaciones, sin mover Ledger.',
    liquidity:'03_LIQUIDEZ · saldos por venue. Quantfury se incluye una sola vez.',
    parameters:'12_PARAMETROS_KAIROS · porcentajes O3/O5, tramos O5, Balancer, riesgo y alertas. Cada reparto debe sumar 100%.',
    pivots:'07_PIVOTES · entradas históricas como pendientes de certificación. Nunca habilitan LIMIT por sí mismas.'};
  const cols={units:[['hodl','HODL'],['core','Core'],['exchange','Exchange'],['average_cost','Costo medio']],
    targets:[['tier','Tier'],['target','Objetivo (fracción)']],tier_custody:[['hodl','HODL'],['core','Core'],['exchange','Exchange']],
    liquidity:[['usdt','USDT físico']],parameters:[['value','Valor']],
    pivots:[['cycle_low','Cycle Low'],['o1','O1'],['o2','O2'],['o3','O3'],['o4','O4'],['o5','O5'],['c1_reference','C1 ref'],['c2_reference','C2 ref']]};
  const nav=document.getElementById('settings-nav'), body=document.getElementById('settings-data'),
    status=document.getElementById('settings-msg'),preview=document.getElementById('settings-preview'),
    publish=document.getElementById('settings-publish');
  let state=null,tab='units',draft=null;
  function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
  function show(m){status.textContent=m;}
  function changed(a,b){return String(a??'')!==String(b??'');}
  function draw(){
    document.getElementById('settings-title').textContent=titles[tab];
    document.getElementById('settings-desc').textContent=desc[tab];
    document.getElementById('settings-snapshot').textContent=state?'Snapshot: '+state.snapshot_id+' · Corte: '+state.fecha_corte+(state.write_configured?' · Edición configurada':' · Lectura solamente'):'—';
    body.replaceChildren();draft=null;publish.disabled=true;
    if(!state){body.textContent='Google Sheets no disponible.';return;}
    const rows=state.sections[tab] || [];
    if(!rows.length){body.textContent='No hay filas configuradas.';return;}
    rows.forEach((entry,index)=>{
      const key=tab==='liquidity'?'venue':tab==='tier_custody'?'tier':tab==='parameters'?'key':'token';
      const item=el('div','settings-row '+(tab==='parameters'?'param':'')+(tab==='pivots'?' pivots':''));
      if(tab==='pivots'){item.style.gridTemplateColumns='repeat(4,minmax(100px,1fr))';}
      item.append(el('strong','token-name',entry[key]));
      cols[tab].forEach(([field,label])=>{
        const holder=el('div','settings-field'),name=el('label','',label);
        let input;
        if(field==='tier'){
          input=el('select');['T1','T2','T3'].forEach(k=>{const option=el('option','',k);option.value=k;input.append(option);});input.value=entry[field];
        }else{
          input=el('input');input.type=tab==='parameters'&&typeof entry.value==='string'?'text':'number';
          if(input.type==='number'){input.min='0';input.step='any';}
          input.value=entry[field]??'';
        }
        input.dataset.index=String(index);input.dataset.field=field;
        input.addEventListener('input',()=>{draft=null;publish.disabled=true;});
        holder.append(name,input);item.append(holder);
      });
      if(tab==='pivots')item.append(el('small','settings-hint','Estado: '+entry.status+' · Edición = no certificado'));
      body.append(item);
    });
  }
  function collect(){
    if(!state)return [];
    const originals=state.sections[tab],fields=cols[tab].map(x=>x[0]),key=tab==='liquidity'?'venue':tab==='tier_custody'?'tier':tab==='parameters'?'key':'token';
    let changes=[];
    originals.forEach((base,index)=>{
      const entry={[key]:base[key]};let dirty=false;
      for(const field of fields){
        const input=body.querySelector(`[data-index="${index}"][data-field="${field}"]`);
        if(!input)throw Error('Falta un campo del formulario');
        const value=input.type==='number'?(input.value===''?null:Number(input.value)):input.value;
        if(input.type==='number'&&value!==null&&!Number.isFinite(value))throw Error('Número inválido: '+field);
        if(changed(value,base[field]))dirty=true;
        if(tab==='pivots' && value===null)continue;
        entry[field]=value;
      }
      if(dirty) changes.push(entry);
    });
    return changes;
  }
  function payload(){
    const entries=collect();
    if(!entries.length)throw Error('No hay cambios respecto de la versión cargada.');
    return {expected_snapshot_id:state.snapshot_id,section:tab,entries,
      evidence:document.getElementById('settings-evidence').value.trim(),
      as_of_date:document.getElementById('settings-asof').value || null};
  }
  async function api(url,body){
    const pass=document.getElementById('settings-admin').value;
    if(!pass)throw Error('Introduce la clave administrativa de KairosWeb.');
    const response=await fetch(url,{method:'POST',credentials:'same-origin',
      headers:{'Content-Type':'application/json','X-Kairos-Admin-Key':pass},body:JSON.stringify(body)});
    const data=await response.json();
    if(!response.ok)throw Error(data.reason||data.message||data.status||'Operación fallida');
    return data;
  }
  async function load(){
    draft=null;publish.disabled=true;body.textContent='Leyendo Google Sheets…';
    try{const res=await fetch('/api/settings/data',{cache:'no-store',credentials:'same-origin'});
      const json=await res.json();if(!res.ok || json.status!=='OK')throw Error(json.message||'DATA_ERROR');
      state=json;draw();show(json.write_configured?'Lectura validada. Completa, valida y publica los cambios que autorices.':'Lectura validada. Escritura DESHABILITADA: configura una cuenta editora separada en Render.');
    }catch(e){state=null;draw();show('DATA ERROR: '+e.message);}
  }
  nav.addEventListener('click',e=>{const btn=e.target.closest('button[data-tab]');if(!btn)return;
    tab=btn.dataset.tab;nav.querySelectorAll('.settings-tab').forEach(x=>x.classList.toggle('selected',x===btn));draw();show('Sin cambios publicados.');});
  preview.addEventListener('click',async()=>{preview.disabled=true;publish.disabled=true;
    try{const body=payload();const res=await api('/api/settings/preview',body);
      draft={...body,preview_token:res.preview_token};publish.disabled=!state.write_configured;
      show(`Validado: ${res.changed_fields} campos. No se modificó el Master. ${state.write_configured?'Revisa y pulsa Publicar revisión.':'Falta configurar editor para publicar.'}`);
    }catch(e){draft=null;show('NO VALIDADO: '+e.message);}finally{preview.disabled=false;}});
  publish.addEventListener('click',async()=>{
    if(!draft)return;
    const accepted=window.confirm('Publicar estos cambios en Google Sheets como NUEVO snapshot? Esta acción cambia datos operativos y registra una nueva revisión.');
    if(!accepted)return;
    publish.disabled=true;
    try{const res=await api('/api/settings/publish',{...draft,confirm:'PUBLICAR'});
      show('PUBLICADO: '+res.snapshot_id+' · '+res.written_fields+' campos. '+res.warning);
      await load();
    }catch(e){show('NO PUBLICADO: '+e.message);}
  });
  document.getElementById('settings-reload').addEventListener('click',load);
  load();
})();
