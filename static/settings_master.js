(() => {
  'use strict';
  const fmt=window.KairosFormatting;
  const names={units:'Maestro de unidades',targets:'Objetivos y Tiers',tier_custody:'Custodia por Tier',
    liquidity:'Liquidez por venue',parameters:'Parámetros y plan de ventas',pivots:'Pivotes y referencias'};
  const desc={units:'02_POSICIONES · Unidades HODL, Core y Exchange; inversión remanente. Total y costo medio se calculan automáticamente.',
    targets:'02_POSICIONES · Objetivos de los 12 activos; la suma debe ser 100%.',
    tier_custody:'04_CUSTODIA · Porcentajes simulados por Tier; no realiza traspasos reales.',
    liquidity:'03_LIQUIDEZ · Saldos USDT por venue; Quantfury se cuenta una sola vez.',
    parameters:'12_PARAMETROS_KAIROS · Valores aprobados, porcentajes y planes de ventas. Cada parámetro describe su impacto.',
    pivots:'07_PIVOTES · Candidatos MCP para revisión manual; guardar NO los certifica ni genera órdenes.'};
  const sectionFields={units:[['hodl','HODL'],['core','Core'],['exchange','Exchange'],['investment_total','Inversión remanente (USDT)']],
    targets:[['tier','Tier'],['target','Objetivo (%)']],
    tier_custody:[['hodl','HODL (%)'],['core','Core (%)'],['exchange','Exchange (%)']],
    liquidity:[['usdt','USDT físico']],parameters:[['value','Valor']],
    pivots:[['cycle_low','Cycle Low'],['o1','O1'],['o2','O2'],['o3','O3'],['o4','O4'],['o5','O5'],['c1_reference','C1 ref'],['c2_reference','C2 ref']]};
  const nav=document.getElementById('settings-nav'), body=document.getElementById('settings-data');
  const status=document.getElementById('settings-msg'), save=document.getElementById('settings-save');
  const hint=document.getElementById('settings-admin-state');const more=document.getElementById('settings-pivots-tools');
  const totals=document.getElementById('settings-totals');
  let state=null,tab='units',pivots={},preliminaryLoaded=false;
  function el(t,c,value){const x=document.createElement(t);if(c)x.className=c;if(value!==undefined)x.textContent=String(value);return x;}
  function message(m){status.textContent=m;}
  function numerical(v){const x=Number(v);return Number.isFinite(x)?x:0;}
  function cleanFloat(v){return String(Number(Number(v).toPrecision(12)));}
  const pc=(n)=>`${cleanFloat(n)}%`;
  const money=(n)=>'US$'+Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  function rowKey(){return tab==='liquidity'?'venue':tab==='tier_custody'?'tier':tab==='parameters'?'key':'token';}
  function inputValue(field,entry){const value=entry[field];
    if(tab==='targets'&&field==='target' ||tab==='tier_custody')return cleanFloat(numerical(value)*100);
    if(tab==='parameters'&&field==='value')return fmt.toDisplay(value,entry);
    return value===null||value===undefined?'':String(value);
  }
  function makeField(item,entry,index,field,label){const holder=el('div','settings-field');const name=el('label','',label);
    let input;if(field==='tier'){
      input=el('select');for(const v of ['T1','T2','T3']){const option=el('option','',v);option.value=v;input.append(option);}input.value=entry[field];
    }else{
      input=el('input');input.type='text';input.inputMode='decimal';input.value=inputValue(field,entry);
      if(field==='value'&&fmt.scale(entry)==='percent-list'){input.placeholder='20%, 20%, 30%, 30%';}
    }
    input.dataset.index=String(index);input.dataset.field=field;input.setAttribute('aria-label',label+' '+(entry.token||entry.key||entry.tier||entry.venue||''));
    input.addEventListener('input',updateComputed);
    holder.append(name,input);item.append(holder);
  }
  function rowNum(index,field){const v=body.querySelector(`[data-index="${index}"][data-field="${field}"]`);return v?numerical(v.value):0;}
  function renderTotals(){totals.replaceChildren();if(!state)return;
    const box=el('div','settings-total-panel');
    if(tab==='units'){
      const initial=state.sections.units;
      let sumCost=0;
      initial.forEach((r,i)=>sumCost+=rowNum(i,'investment_total'));
      box.append(el('strong','',`Inversión remanente total: ${money(sumCost)}`),el('span','', 'Total de unidades y costo medio visibles por token. No se suman unidades de monedas distintas.'));
    }else if(tab==='targets'){
      const value=state.sections.targets.reduce((s,_,i)=>s+rowNum(i,'target'),0);
      box.append(el('strong','',`Total objetivos: ${pc(value)}`));
      box.append(el('span',Math.abs(value-100)>.000001?'invalid-value':'valid-value',Math.abs(value-100)>.000001?'Debe sumar 100%':'Validación: 100%'));
    }else if(tab==='tier_custody'){
      state.sections.tier_custody.forEach((r,i)=>{let t=['hodl','core','exchange'].reduce((s,f)=>s+rowNum(i,f),0);
        box.append(el('span',Math.abs(t-100)>.000001?'invalid-value':'valid-value',`${r.tier}: ${pc(t)} / 100%`));});
    }else if(tab==='liquidity'){
      const total=state.sections.liquidity.reduce((s,_,i)=>s+rowNum(i,'usdt'),0);
      const qf=state.sections.liquidity.reduce((s,r,i)=>s+(r.classification==='TRADING_QF'?rowNum(i,'usdt'):0),0);
      const prev=state.sections.liquidity.reduce((s,r)=>s+Number(r.usdt),0);
      box.append(el('strong','',`Total acumulado: ${money(total)}`),el('span','',`Reserva QF (incluida): ${money(qf)}`),
        el('span','',`Liquidez operativa: ${money(total-qf)}`),el('span','',`Total Master publicado: ${money(prev)}`),
        el('span','',`Variación propuesta: ${money(total-prev)} · se conciliará al guardar`));
    }else return;
    totals.append(box);
  }
  function updateComputed(){
    if(!state)return;
    if(tab==='units'){
      state.sections.units.forEach((r,i)=>{
        const t=['hodl','core','exchange'].reduce((s,k)=>s+rowNum(i,k),0);
        const v=rowNum(i,'investment_total');
        const total=body.querySelector(`[data-computed="total-${i}"]`);
        const avg=body.querySelector(`[data-computed="avg-${i}"]`);
        if(total)total.textContent=Number(t).toLocaleString('en-US',{maximumFractionDigits:10});
        if(avg)avg.textContent=t>0?money(v/t):'N/D';
      });
    }
    renderTotals();
  }
  function draw(){
    document.getElementById('settings-title').textContent=names[tab];
    document.getElementById('settings-desc').textContent=desc[tab];
    document.getElementById('settings-snapshot').textContent=state?`Snapshot: ${state.snapshot_id} · Corte: ${state.fecha_corte} · Cambios auditados`:'';
    body.replaceChildren();totals.replaceChildren();more.hidden=tab!=='pivots';
    if(!state){body.textContent='Google Sheets no disponible.';return;}
    const rows=state.sections[tab]||[];
    for(let index=0;index<rows.length;index++){
      const entry=rows[index];const item=el('div','settings-row '+(tab==='parameters'?'param ':''));
      if(tab==='pivots')item.classList.add('pivots');
      if(tab==='units')item.classList.add('units');
      const primary=el('div','settings-token');
      if(tab==='parameters'){
        primary.append(el('strong','token-name',fmt.labels[entry.key]||entry.key),el('small','settings-key',entry.key));
        if(entry.description)primary.append(el('p','parameter-description',entry.description));
        primary.append(el('small','settings-hint',`Área: ${entry.module_name} · Estado: ${entry.status} · Fuente: ${entry.source||'Master'}`));
      }else primary.append(el('strong','token-name',entry[rowKey()]));
      item.append(primary);
      for(const [field,label] of sectionFields[tab])makeField(item,entry,index,field,label);
      if(tab==='units'){
        for(const [field,label] of [['total','Total unidades'],['avg','Costo medio (USDT/unidad)']]){
          const cell=el('div','settings-field computed');cell.append(el('span','settings-hint',label));
          const value=el('strong','computed-value','—');value.dataset.computed=field+'-'+index;cell.append(value);item.append(cell);
        }
      }
      if(tab==='pivots'){
        const text=el('p','pivot-candidate-hint');text.dataset.pivotInfo=entry.token;
        text.textContent='Actual: '+(entry.status||'SIN_DATO')+' · C1/C2 históricas son referencias; editar no certifica';
        item.append(text);
      }
      body.append(item);
    }
    updateComputed();
  }
  function fromInput(field,value,entry){
    if(field==='tier')return value;
    if(tab==='parameters'&&field==='value')return fmt.fromDisplay(value,entry);
    if(value.trim()===''&&tab==='pivots')return null;
    const n=Number(value.replace(',','.'));
    if(!value.trim()||!Number.isFinite(n)||n<0)throw Error(`Valor inválido: ${entry.token||entry.key||entry.venue||entry.tier} · ${field}`);
    if((tab==='targets'&&field==='target')||tab==='tier_custody'){
      if(n>100)throw Error('El porcentaje no puede superar 100%');
      return n/100;
    }
    return n;
  }
  function collect(){const originals=state.sections[tab]||[];const out=[];
    originals.forEach((entry,index)=>{const data={[rowKey()]:entry[rowKey()]};let dirty=false;
      for(const [field] of sectionFields[tab]){
        const input=body.querySelector(`[data-index="${index}"][data-field="${field}"]`);
        if(!input)throw Error('Falta un campo');
        const value=fromInput(field,input.value,entry);
        if(value===null&&tab==='pivots')continue;
        if(typeof value==='number'){
          if(Math.abs(value-Number(entry[field]??0))>Math.max(1e-11,Math.abs(value)*1e-10))dirty=true;
        }else if(String(value)!==String(entry[field]??''))dirty=true;
        data[field]=value;
      }
      if(dirty)out.push(data);
    });
    return out;
  }
  async function api(path,payload,csrf){
    const response=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Kairos-Csrf':csrf||''},body:JSON.stringify(payload)});
    const data=await response.json();if(!response.ok||data.status!=='OK')throw Error(data.reason||data.message||data.status||'Error de servidor');
    return data;
  }
  async function load(){body.textContent='Leyendo Google Sheets…';
    try{const res=await fetch('/api/settings/data',{cache:'no-store',credentials:'same-origin'}),data=await res.json();
      if(!res.ok||data.status!=='OK')throw Error(data.message||'Master no disponible');
      state=data;draw();
      hint.replaceChildren();
      if(!data.is_admin){const a=el('a','settings-admin-link','Iniciar sesión de administrador para editar');a.href='/admin/login';hint.append(a);}else{
        hint.append(el('span','valid-value','Sesión administrativa activa · cambios auditados'));
        const out=el('button','tiny-control','Cerrar sesión');out.type='button';out.addEventListener('click',async()=>{
          try{await api('/admin/logout',{},state.csrf_token);window.location.reload();}catch(e){message('Error: '+e.message);}});hint.append(out);
      }
      save.disabled=!data.is_admin||!data.write_configured;
      message(!data.write_configured?'Sin permisos de escritura configurados. Solo consulta.':data.is_admin?'Listo. Modifica los valores y pulsa Guardar cambios.':'Consulta activa; inicia sesión administrativa para guardar.');
    }catch(e){state=null;draw();message('DATA ERROR: '+e.message);}
  }
  nav.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;
    nav.querySelectorAll('button').forEach(x=>x.classList.toggle('selected',x===b));draw();message('Edición local; aún no se ha publicado ningún cambio.');
    if(tab==='pivots'&&!preliminaryLoaded){preliminaryLoaded=true;loadPreliminary();}
  });
  save.addEventListener('click',async()=>{
    if(!state||!state.is_admin)return;
    const evidence=document.getElementById('settings-evidence').value.trim();
    let entries;try{entries=collect();if(!entries.length)throw Error('No hay cambios para guardar.');
      if(evidence.length<8)throw Error('Indica justificación o evidencia (mínimo 8 caracteres).');
      if(tab==='targets'&&Math.abs(state.sections.targets.reduce((s,_,i)=>s+rowNum(i,'target'),0)-100)>.000001)throw Error('Los objetivos deben sumar 100%.');
      if(tab==='tier_custody')for(let i=0;i<state.sections.tier_custody.length;i++)if(Math.abs(['hodl','core','exchange'].reduce((s,f)=>s+rowNum(i,f),0)-100)>.000001)throw Error('Custodia de cada Tier debe sumar 100%.');
    }catch(e){message('NO VALIDADO: '+e.message);return;}
    const accepted=window.confirm('Se validará y publicará una nueva revisión auditada de Google Sheets. ¿Continuar?');if(!accepted)return;
    save.disabled=true;message('Validando integridad, publicando y recargando el Master…');
    try{const res=await api('/api/settings/save',{expected_snapshot_id:state.snapshot_id,section:tab,entries,evidence},state.csrf_token);
      message(`PUBLICADO: ${res.snapshot_id}. ${res.written_fields} campos auditados. Recargando…`);
      await load();message(`Guardado confirmado en Google Sheets: ${res.snapshot_id}. KairosGPT leerá esta revisión en la siguiente ejecución.`);
    }catch(e){message('NO PUBLICADO / VERIFICAR: '+e.message);}finally{save.disabled=!state?.is_admin||!state?.write_configured;}
  });
  async function loadPreliminary(){
    const button=document.getElementById('settings-preliminary');button.disabled=true;message('Consultando velas históricas MCP, podría tardar…');
    try{const r=await fetch('/api/settings/pivots/preliminary',{cache:'no-store',credentials:'same-origin'}),json=await r.json();
      if(!r.ok||json.status!=='OK')throw Error(json.reason||'MCP no disponible');
      for(const rec of json.records){pivots[rec.token]=rec;
        const ix=(state.sections.pivots||[]).findIndex(x=>x.token===rec.token);if(ix<0)continue;
        const row=state.sections.pivots[ix];
        for(const field of ['cycle_low','o1','o2','o3','o4','o5']){
          const control=body.querySelector(`[data-index="${ix}"][data-field="${field}"]`);
          if(control && (row[field]===null||row[field]===undefined||row[field]==='')&&control.value===''&&rec[field]!==null&&rec[field]!==undefined){
            control.value=String(rec[field]);
          }
        }
        const label=body.querySelector(`[data-pivot-info="${rec.token}"]`);
        if(label)label.textContent=rec.status==='DATA_ERROR'?`${rec.token}: ${rec.warning}`:
          `CH: ${rec.cycle_high??'N/D'} (${rec.ch_date??'s/f'}) · CL: ${rec.cycle_low??'N/D'} (${rec.cl_date??'s/f'}) · ${rec.source} · ${rec.warning}`;
      }
      message('Candidatos MCP precargados para revisión. Verifica y corrige los campos antes de Guardar. Ningún pivote fue certificado.');
    }catch(err){preliminaryLoaded=false;message('DATA ERROR MCP: '+err.message);}finally{button.disabled=false;}
  }
  document.getElementById('settings-preliminary').addEventListener('click',()=>{preliminaryLoaded=true;loadPreliminary();});
  load();
})();
