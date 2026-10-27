(() => {
  'use strict';
  const fmt=window.KairosFormatting;
  const names={portfolio_goals:'Objetivos de gestión del portafolio',units:'Maestro de unidades',targets:'Objetivos y Tiers',tier_custody:'Custodia por Tier',
    liquidity:'Liquidez por venue',capital_targets:'Objetivos de liquidez y ReservaTrading (%)',parameters:'Parámetros',pivots:'Pivotes y referencias',mcp:'Estado de conexiones MCP'};
  const desc={portfolio_goals:'Una sola vista: Cripto vs Liquidez, Tier 1/2/3, objetivos de USDT/Reservas y HODL/Core/Exchange. Los cuatro grupos se validan y publican en la misma revisión, sin modificar saldos físicos.',units:'02_POSICIONES · Unidades HODL, Core y Exchange; inversión remanente. Total y costo medio se calculan automáticamente.',
    targets:'02_POSICIONES · Objetivos de los 12 activos; la suma debe ser 100%.',
    tier_custody:'04_CUSTODIA · Porcentajes simulados por Tier; no realiza traspasos reales.',
    liquidity:'03_LIQUIDEZ · Saldos USDT reales por venue; Quantfury se cuenta una sola vez. Para porcentajes objetivo abre «Objetivos de liquidez y ReservaTrading (%)».',
    capital_targets:'08_INTEGRAL · Objetivos de distribución del capital histórico (%). Liquidez y Trading/ReservaTrading son objetivos, NO saldos reales ni políticas de ejecución. Los cuatro segmentos deben sumar 100%; no altera 03_LIQUIDEZ ni la reserva física Quantfury.',
    parameters:'12_PARAMETROS_KAIROS · Valores aprobados, porcentajes y planes de ventas. Cada parámetro describe su impacto.',
    pivots:'07_PIVOTES · CL y O1–O5: PROPUESTO → VALIDADO (5L/5R+BOS 1W) → CONFIRMADO. «Actualizar candidatos desde MCP» actualiza solo PROPUESTO; VALIDADO y CONFIRMADO conservan precio, fecha y estado. «Validar → Publicar» registra cambios administrativos sin ejecutar órdenes.',mcp:'Diagnóstico MCP independiente del Master. Consultas de solo lectura y reconexión sin reiniciar Render.'};
  const PARAM_GROUPS=[
    {id:'portfolio',name:'Portafolio',description:'Meta de liquidez, tolerancia de desvío y topes de reservas sobre el portafolio Spot.',keys:['STRUCTURAL_USDT_TARGET','DRIFT_BAND_PP','BALANCER_MAX_PORTFOLIO_FRACTION','TRADING_MAX_PORTFOLIO_FRACTION']},
    {id:'o2',name:'Compras O2 · Forecast',description:'Cuatro retrocesos independientes: 100% del presupuesto máximo de 25% P de O2.',prefix:'FORECAST_O2_FIB_'},
    {id:'o3',name:'Ventas O3 · Forecast',description:'Cuatro extensiones independientes: 100% de las unidades elegibles para O3. Objetivo 40% USDT.',prefix:'FORECAST_O3_FIB_',keys:['O3_BTC_PROCEEDS_FRACTION','O3_USDT_PROCEEDS_FRACTION']},
    {id:'o4',name:'Compras O4 · Forecast',description:'Cuatro retrocesos independientes: 100% del presupuesto máximo de 25% P de O4.',prefix:'FORECAST_O4_FIB_'},
    {id:'o5',name:'Ventas O5 · Forecast',description:'Cuatro extensiones independientes: 100% de las unidades elegibles. O5 no se detiene por el piso 40% USDT.',prefix:'FORECAST_O5_FIB_',keys:['O5_BTC_PROCEEDS_FRACTION','O5_USDT_PROCEEDS_FRACTION']},
    {id:'trading',name:'Trading QF',description:'Riesgo, margen y apalancamiento. TradingBot seguirá WATCH sin verificar Quantfury.',keys:['RISK_REWARD_MIN','QF_MARGIN_CAP_PER_POSITION','QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL','MAX_LEVERAGE','MAX_OPEN_POSITIONS']},
    {id:'bsi',name:'Indicadores y BSI',description:'Los umbrales no desbloquean por sí solos BSI SELL.',keys:['TRIGGER_STRICT_GT']},
    {id:'alerts',name:'Alertas',description:'Proximidad de las alertas de Kairos.',keys:['PROXIMITY_BAND']}
  ];
  function parameterGroup(entry){return PARAM_GROUPS.find(g=>(g.keys||[]).includes(entry.key)||g.prefix&&entry.key.startsWith(g.prefix))||PARAM_GROUPS[0];}
  // Order presentation by canonical Fib level, NOT by Google Sheets row order.
  // Preserve the original data-index: collect() and audited writes must continue
  // addressing the exact parameter key, even when fields are reordered visually.
  const FIB_DISPLAY_ORDER={O2:['382','500','618','786'],O3:['1618','2618','3618','4618'],
    O4:['382','500','618','786'],O5:['1618','2618','3618','4618']};
  function parameterVisualRank(entry){
    const group=parameterGroup(entry).id;
    const groupIndex=PARAM_GROUPS.findIndex(g=>g.id===group);
    const match=String(entry.key||'').match(/^FORECAST_(O[2345])_FIB_(\d{3,4})_PCT$/);
    const fibRank=match?FIB_DISPLAY_ORDER[match[1]].indexOf(match[2]):-1;
    return groupIndex*100+(fibRank<0?50:fibRank);
  }
  const sectionFields={units:[['hodl','HODL'],['core','Core'],['exchange','Exchange'],['investment_total','Inversión remanente (USDT)']],
    targets:[['tier','Tier'],['target','Objetivo (%)']],
    tier_custody:[['hodl','HODL (%)'],['core','Core (%)'],['exchange','Exchange (%)']],
    liquidity:[['usdt','USDT físico']],capital_targets:[['target','Objetivo (%)']],parameters:[['value','Valor']],
    pivots:[['cycle_low','Cycle Low'],['o1','O1'],['o2','O2'],['o3','O3'],['o4','O4'],['o5','O5']]};
  const nav=document.getElementById('settings-nav'), body=document.getElementById('settings-data');
  const status=document.getElementById('settings-msg'), save=document.getElementById('settings-save');
  const hint=document.getElementById('settings-admin-state');const more=document.getElementById('settings-pivots-tools');
  const totals=document.getElementById('settings-totals');
  let state=null,tab='portfolio_goals',pivots={},archiveLoaded=false,refreshingPivots=false,autoO1Started=false;
  const clReviewProofs={};
  const waveReviewProofs={};

  let bulkReviewing=false;
  function el(t,c,value){const x=document.createElement(t);if(c)x.className=c;if(value!==undefined)x.textContent=String(value);return x;}
  function message(m){status.textContent=m;}
  // Shared, decorative token logos in Configuración. Only approved tokens
  // receive a logo; other settings keys/venues/tiers remain plain text.
  // Assets match the catalog already used by the KairosWeb dashboard.
  const SETTINGS_COIN_LOGOS=Object.freeze({
    BTC:'bitcoin-btc', ETH:'ethereum-eth', SOL:'solana-sol',
    LINK:'chainlink-link', HYPE:'hyperliquid-hype', HBAR:'hedera-hbar',
    SUI:'sui-sui', ONDO:'ondo-finance-ondo',
    PUMP:'pump-fun-pump', PUMPFUN:'pump-fun-pump',
    PLUME:'plume-plume', PEPE:'pepe-pepe',
    VIRTUAL:'virtual-protocol-virtual'
  });
  function settingsTokenLabel(token){
    const key=String(token??'').toUpperCase();
    const wrap=el('span','settings-token-identity');
    const logo=SETTINGS_COIN_LOGOS[key];
    if(logo){
      const icon=el('span','coin-icon settings-coin-icon');
      const fallback=el('span','coin-fallback',key==='PUMPFUN'?'PU':key.slice(0,2));
      const img=el('img');
      img.loading='lazy';img.decoding='async';img.alt='';
      img.src='https://cryptologos.cc/logos/'+logo+'-logo.png';
      img.addEventListener('error',()=>{img.remove();icon.classList.add('missing');});
      icon.append(fallback,img);wrap.append(icon);
    }
    wrap.append(el('strong','token-name',String(token??'')));
    return wrap;
  }
  function numerical(v){const x=Number(v);return Number.isFinite(x)?x:0;}
  function cleanFloat(v){return String(Number(Number(v).toPrecision(12)));}
  const pc=(n)=>`${cleanFloat(n)}%`;
  const money=(n)=>'US$'+Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const price5=(n)=>{const v=Number(n);return !Number.isFinite(v)?'N/D':v>0&&v<0.00001?'US$<0.00001':'US$'+v.toLocaleString('en-US',{maximumFractionDigits:5});};
  function rowKey(){return tab==='capital_targets'?'segment':tab==='liquidity'?'venue':tab==='tier_custody'?'tier':tab==='parameters'?'key':'token';}
  function inputValue(field,entry){const value=entry[field];
    if((tab==='targets'||tab==='capital_targets')&&field==='target' ||tab==='tier_custody')return cleanFloat(numerical(value)*100);
    if(tab==='parameters'&&field==='value')return fmt.toDisplay(value,entry);
    if(tab==='units'&&field==='investment_total')return Number(value).toFixed(2);
    return value===null||value===undefined?'':String(value);
  }
  function makeField(item,entry,index,field,label){const holder=el('div','settings-field');const name=el('label','',tab==='parameters'&&entry.key?.endsWith('_PCT')?'Asignación (%)':label);
    let input;if(field==='tier'){
      input=el('select');for(const v of ['T1','T2','T3']){const option=el('option','',v);option.value=v;input.append(option);}input.value=entry[field];
    }else{
      input=el('input');input.type='text';input.inputMode='decimal';input.value=inputValue(field,entry);
      if(field==='value'&&fmt.scale(entry)==='percent-list'){input.placeholder='Ej.: 0%, 40%, 40%, 20%';}
      if(tab==='units'&&field==='investment_total'){input.inputMode='decimal';input.placeholder='0.00';}
    }
    input.dataset.index=String(index);input.dataset.field=field;input.setAttribute('aria-label',label+' '+(entry.token||entry.key||entry.tier||entry.venue||''));
    input.addEventListener('input',()=>{input.dataset.userEdited='true';updateComputed();});
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
    }else if(tab==='capital_targets'){
      const total=state.sections.capital_targets.reduce((s,_,i)=>s+rowNum(i,'target'),0);
      const capital=state.sections.capital_targets.reduce((s,r)=>s+Number(r.target_usdt),0);
      box.append(el('strong','',`Suma objetivos: ${pc(total)} / 100%`));
      box.append(el('span',Math.abs(total-100)>0.000001?'invalid-value':'valid-value',Math.abs(total-100)>0.000001?'Ajusta otros segmentos para completar el 100%':'Objetivos coherentes con 100%'));
      box.append(el('span','',`Base de capital histórico: ${money(capital)}. Solo modifica objetivos de 08_INTEGRAL; no mueve saldos de Quantfury ni cambia el objetivo estructural de 12_PARAMETROS_KAIROS.`));
    }else if(tab==='liquidity'){
      const total=state.sections.liquidity.reduce((s,_,i)=>s+rowNum(i,'usdt'),0);
      const qf=state.sections.liquidity.reduce((s,r,i)=>s+(r.classification==='TRADING_QF'?rowNum(i,'usdt'):0),0);
      const prev=state.sections.liquidity.reduce((s,r)=>s+Number(r.usdt),0);
      box.append(el('strong','',`Total acumulado: ${money(total)}`),el('span','',`Reserva QF (incluida): ${money(qf)}`),
        el('span','',`Liquidez operativa: ${money(total-qf)}`),el('span','',`Total Master publicado: ${money(prev)}`),
        el('span','',`Variación propuesta: ${money(total-prev)} · se conciliará al guardar`));
    }else if(tab==='parameters'){
      for(const stage of ['O2','O3','O4','O5']){
        const group=state.sections.parameters.map((r,i)=>({r,i})).filter(x=>x.r.key.startsWith(`FORECAST_${stage}_FIB_`) && x.r.key.endsWith('_PCT'));
        if(group.length!==4)continue;
        const total=group.reduce((s,x)=>s+rowNum(x.i,'value'),0);
        const tag=el('span',Math.abs(total-100)>1e-6?'invalid-value':'valid-value',`${stage} · suma de tramos: ${pc(total)} / 100%`);
        box.append(tag);
      }
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
        if(avg)avg.textContent=t>0?price5(v/t):'N/D';
      });
    }
    if(tab==='capital_targets'){
      const cap=state.sections.capital_targets.reduce((s,r)=>s+Number(r.target_usdt),0);
      state.sections.capital_targets.forEach((r,i)=>{
        const target=body.querySelector(`[data-computed="capital-target-${i}"]`);
        if(target)target.textContent=`Objetivo: ${money(cap*rowNum(i,'target')/100)}`;
      });
    }
    renderTotals();
  }
  // Technical MCP evidence is only a draft until explicitly published to 07_PIVOTES.
  // Distinguish persistent Master state from visual draft state; never auto-write.
  function updatePivotPublicationHint(){
    const marker=document.getElementById('settings-pivots-publication-state');
    const go=document.getElementById('settings-go-publish');
    if(!marker||!go)return;
    if(tab!=='pivots'||!state?.sections?.pivots){marker.textContent='';go.hidden=true;return;}
    let publishedValidated=0,publishedConfirmed=0,draftValidated=0,draftChanged=0;
    for(const rec of state.sections.pivots){
      for(const field of ['cl',...WAVE_NAMES]){
        const key=field==='cl'?'cl_status':field+'_status';
        const original=rec[key]||'PROPUESTO';
        if(original==='VALIDADO')publishedValidated++;
        if(original==='CONFIRMADO')publishedConfirmed++;
        const input=document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${key}"]`);
        const current=input?.value||original;
        if(current==='VALIDADO'&&original!=='VALIDADO')draftValidated++;
        if(current!==original)draftChanged++;
      }
    }
    marker.textContent=`Master PUBLICADO: ${publishedValidated} pivotes VALIDADOS, ${publishedConfirmed} CONFIRMADOS. `+
      (draftChanged?`BORRADOR SIN PUBLICAR: ${draftValidated} nuevos VALIDADOS, ${draftChanged} cambios de estado. Para conservarlos al recargar, completa «Validar → Publicar pivotes» (dos confirmaciones).`:
      'Los resultados de MCP no se guardan hasta que autorices «Validar → Publicar pivotes».');
    go.hidden=!(draftChanged&&state.is_admin);
  }
  const WAVE_NAMES=['o1','o2','o3','o4','o5'];
  function pivotControl(type,value,token,field,locked=false){
    const node=el('input','pivot-matrix-input');node.type=type;
    node.value=value??'';node.dataset.pivotToken=token;node.dataset.pivotField=field;
    node.disabled=locked;node.setAttribute('aria-label',token+' '+field);
    node.addEventListener('input',()=>{node.dataset.userEdited='true';});
    return node;
  }
  function drawPivotTable(){
    const mount=document.getElementById('settings-pivot-matrix');mount.hidden=false;mount.replaceChildren();
    const help=el('p','settings-hint','CL y O1–O5: PROPUESTO → VALIDADO → CONFIRMADO. El MCP solo modifica PROPUESTO; VALIDADO queda fijo hasta edición manual y CONFIRMADO requiere revisión formal. Fechas UTC.');mount.append(help);
    const wrap=el('div','pivot-matrix-scroll'),table=el('table','pivot-wave-table');
    const head=el('thead'),header=el('tr');['Token','Cycle Low (1W)','O1','O2','O3','O4','O5'].forEach(label=>header.append(el('th','',label)));head.append(header);table.append(head);
    const tbody=el('tbody');
    state.sections.pivots.forEach(rec=>{
      const row=el('tr');row.dataset.pivotRow=rec.token;const tokenHead=el('th','settings-pivot-token');tokenHead.append(settingsTokenLabel(rec.token));row.append(tokenHead);
      const cl=el('td','pivot-wave-cell');
      const clLocked=rec.cl_status==='CONFIRMADO'||rec.o1_status==='CONFIRMADO';
      cl.classList.toggle('pivot-locked',clLocked);
      cl.append(pivotControl('number',rec.cycle_low,rec.token,'cycle_low',clLocked),pivotControl('date',rec.cl_date,rec.token,'cl_date',clLocked));
      const clSelect=el('select','pivot-wave-status');clSelect.dataset.pivotToken=rec.token;clSelect.dataset.pivotField='cl_status';
      for(const [value,label] of [['PROPUESTO','PROPUESTO'],['VALIDADO','VALIDADO'],['CONFIRMADO','CONFIRMADO']]){
        const opt=el('option','',label);opt.value=value;clSelect.append(opt);
      }
      clSelect.value=rec.cl_status||'PROPUESTO';clSelect.disabled=clLocked;
      clSelect.setAttribute('aria-label',rec.token+' CL estado');
      clSelect.addEventListener('change',()=>{clSelect.dataset.userEdited='true';updatePivotPublicationHint();});
      cl.append(clSelect);
      if(clLocked)cl.append(el('span','pivot-immutable','🔒 CL bloqueado'));
      row.append(cl);
      WAVE_NAMES.forEach(w=>{
        const locked=rec[w+'_status']==='CONFIRMADO';
        const cell=el('td','pivot-wave-cell'+(locked?' pivot-locked':''));
        const price=pivotControl('number',rec[w],rec.token,w,locked);price.min='0';price.step='any';price.placeholder='N/D';cell.append(price);
        const day=pivotControl('date',rec[w+'_date'],rec.token,w+'_date',locked);cell.append(day);
        const statusSelect=el('select','pivot-wave-status');statusSelect.dataset.pivotToken=rec.token;statusSelect.dataset.pivotField=w+'_status';
        for(const val of ['PROPUESTO','VALIDADO','CONFIRMADO']){const option=el('option','',val);option.value=val;statusSelect.append(option);}
        statusSelect.value=rec[w+'_status']||'PROPUESTO';statusSelect.disabled=locked;
        statusSelect.setAttribute('aria-label',rec.token+' '+w+' estado');
        statusSelect.addEventListener('change',()=>{statusSelect.dataset.userEdited='true';updatePivotPublicationHint();});
        cell.append(statusSelect);
        if(locked)cell.append(el('span','pivot-immutable','🔒 Confirmado y bloqueado'));
        row.append(cell);
      });
      tbody.append(row);
    });
    table.append(tbody);wrap.append(table);mount.append(wrap);
    mount.append(el('p','settings-hint','El MCP nunca reemplaza ni degrada un VALIDADO o CONFIRMADO. Puedes editar manualmente un VALIDADO con nueva evidencia 1W y publicación; CONFIRMADO permanece protegido y requiere revisión formal.'));
    updatePivotPublicationHint();
  }
  function collectPivotMatrix(){
    const out=[];
    for(const rec of state.sections.pivots){
      const data={token:rec.token};let changed=false;
      const fields=['cycle_low','cl_date','cl_status',...WAVE_NAMES.flatMap(w=>[w,w+'_date',w+'_status'])];
      for(const field of fields){
        const input=document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${field}"]`);
        if(!input)throw Error('Campo de pivote no disponible: '+rec.token+' '+field);
        const raw=input.value.trim();
        let value=null;
        if(field.endsWith('_status'))value=raw;
        else if(field.endsWith('_date'))value=raw||null;
        else if(raw){value=Number(raw);if(!Number.isFinite(value)||value<=0)throw Error(rec.token+' '+field+': precio inválido');}
        const orig=field==='cl_status'?(rec.cl_status||'PROPUESTO'):(rec[field]??null);
        if(value!==orig && (typeof value!=='number'||Math.abs(value-Number(orig))>1e-11))changed=true;
        if(value!==null)data[field]=value;
      }
      if(changed){
        if(data.cl_status==='VALIDADO'&&(rec.cl_status!=='VALIDADO'||data.cycle_low!==rec.cycle_low||data.cl_date!==rec.cl_date)){
          const proof=clReviewProofs[rec.token];
          if(!proof||proof.price!==data.cycle_low||proof.date!==data.cl_date)throw Error(rec.token+' CL: pulsa «Actualizar candidatos desde MCP» para verificar 1W');
          data.cl_review_proof=proof.proof;
        }
        for(const w of WAVE_NAMES){
          const v=data[w+'_status'];
          if(v==='VALIDADO'&&(rec[w+'_status']!=='VALIDADO'||data[w]!==rec[w]||data[w+'_date']!==rec[w+'_date'])){
            const proof=waveReviewProofs[rec.token+'|'+w];
            if(!proof||proof.price!==data[w]||proof.date!==data[w+'_date'])
              throw Error(rec.token+' '+w.toUpperCase()+': requiere validación 1W mediante «Actualizar candidatos desde MCP»');
            data[w+'_review_proof']=proof.proof;
          }
          if(v==='CONFIRMADO'&&rec[w+'_status']!=='VALIDADO'&&rec[w+'_status']!=='CONFIRMADO')
            throw Error(rec.token+' '+w.toUpperCase()+': publica primero VALIDADO y después CONFIRMADO');
        }
        if(data.cl_status==='CONFIRMADO'&&rec.cl_status!=='VALIDADO'&&rec.cl_status!=='CONFIRMADO')
          throw Error(rec.token+' CL: publica primero VALIDADO TÉCNICAMENTE y luego confirma en otra revisión');
        out.push(data);
      }
    }
    return out;
  }
  function draw(){
    document.getElementById('settings-title').textContent=names[tab];
    document.getElementById('settings-desc').textContent=desc[tab];
    save.textContent=(tab==='pivots'||tab==='portfolio_goals')?'Validar → Publicar':'Guardar cambios';
    document.getElementById('settings-snapshot').textContent=state?`Snapshot: ${state.snapshot_id} · Corte: ${state.fecha_corte} · Cambios auditados`:'';
    body.replaceChildren();totals.replaceChildren();more.hidden=tab!=='pivots';
    const pivotMatrix=document.getElementById('settings-pivot-matrix');pivotMatrix.hidden=tab!=='pivots';if(tab!=='pivots')pivotMatrix.replaceChildren();
    const diag=document.getElementById('settings-mcp-panel');if(diag)diag.hidden=tab!=='mcp';
    document.querySelector('.settings-form').hidden=tab==='mcp';
    save.parentElement.hidden=tab==='mcp';
    if(tab==='mcp'){body.textContent='';return;}
    if(!state){body.textContent='Google Sheets no disponible.';return;}
    if(tab==='pivots'){drawPivotTable();return;}
    if(tab==='portfolio_goals'){drawGoals();return;}
    updatePivotPublicationHint();
    const rows=state.sections[tab]||[];
    const groupSlots={};
    if(tab==='parameters'){
      const jump=el('nav','parameter-jump');jump.setAttribute('aria-label','Grupos de parámetros');
      for(const group of PARAM_GROUPS){
        const section=el('section','parameter-group');section.id='parameter-group-'+group.id;
        section.append(el('h4','parameter-group-title',group.name),el('p','settings-hint',group.description));
        const entries=el('div','parameter-group-entries');section.append(entries);groupSlots[group.id]=entries;
        body.append(section);
        const link=el('a','parameter-jump-link',group.name);link.href='#'+section.id;jump.append(link);
      }
      body.prepend(jump);
    }
    const renderOrder=rows.map((entry,index)=>({entry,index}));
    if(tab==='parameters')renderOrder.sort((a,b)=>parameterVisualRank(a.entry)-parameterVisualRank(b.entry));
    for(const {entry,index} of renderOrder){
      const item=el('div','settings-row '+(tab==='parameters'?'param ':''));
      if(tab==='pivots')item.classList.add('pivots');
      if(tab==='units')item.classList.add('units');
      const primary=el('div','settings-token');
      if(tab==='parameters'){
        primary.append(el('strong','token-name',fmt.labels[entry.key]||entry.key),el('small','settings-key',entry.key));
        if(entry.description)primary.append(el('p','parameter-description',entry.description));
        primary.append(el('small','settings-hint',`Área: ${entry.module_name} · Estado: ${entry.status} · Fuente: ${entry.source||'Master'}`));
      }else if((tab==='units'||tab==='targets')&&entry.token)primary.append(settingsTokenLabel(entry.token));
      else primary.append(el('strong','token-name',tab==='capital_targets'&&entry.segment==='Trading'?'Trading · ReservaTrading':entry[rowKey()]));
      item.append(primary);
      for(const [field,label] of sectionFields[tab])makeField(item,entry,index,field,label);
      if(tab==='capital_targets'){
        const detail=el('div','settings-field computed');
        detail.append(el('span','settings-hint','Importe objetivo sobre capital histórico'));
        const amount=el('strong','computed-value','—');amount.dataset.computed=`capital-target-${index}`;
        detail.append(amount);item.append(detail);
      }
      if(tab==='units'){
        for(const [field,label] of [['total','Total unidades'],['avg','Costo medio (USDT/unidad)']]){
          const cell=el('div','settings-field computed');cell.append(el('span','settings-hint',label));
          const value=el('strong','computed-value','—');value.dataset.computed=field+'-'+index;cell.append(value);item.append(cell);
        }
      }
      if(tab==='pivots'){
        const text=el('p','pivot-candidate-hint');text.dataset.pivotInfo=entry.token;
        text.textContent='Actual: '+(entry.status||'SIN_DATO')+' · solo pivotes O1–O5; referencias históricas omitidas en Configuración';
        item.append(text);
      }
      if(tab==='parameters')groupSlots[parameterGroup(entry).id].append(item);
      else body.append(item);
    }
    updateComputed();
  }
  // Hierarchical targets: deliberately distinct from balances and operational
  // Balancer liquidity policy. No write occurs until admin preview + publication.
  const GOAL_GROUPS = [
    {id:'portfolio',title:'1. Portafolio global',caption:'Porcentaje del patrimonio objetivo. No representa caja física.',fields:[['crypto','Cripto'],['liquidity','Liquidez total']]},
    {id:'tiers',title:'2. Capas cripto',caption:'Distribución de la manga cripto entre T1, T2 y T3.',fields:[['T1','Tier 1'],['T2','Tier 2'],['T3','Tier 3']]},
    {id:'liquidity_mix',title:'3. Distribución de liquidez objetivo',caption:'Porcentajes dentro de la Liquidez total, no sobre patrimonio ni el saldo Quantfury.',fields:[['usdt','USDT operativos'],['balancer','Reserva Balancer (objetivo)'],['trading','ReservaTrading (objetivo)']]},
  ];
  function goalRead(key){const input=body.querySelector(`[data-goal="${key}"]`);if(!input)throw Error('Falta el campo '+key);
    const text=input.value.trim().replace(',','.');if(!/^(?:\d+)(?:\.\d+)?$/.test(text))throw Error('Porcentaje inválido: '+key);
    const v=Number(text);if(!Number.isFinite(v)||v<0||v>100)throw Error('Porcentaje fuera de 0–100: '+key);return v/100;
  }
  function collectGoals(){
    const p={group:'portfolio',crypto:goalRead('portfolio.crypto'),liquidity:goalRead('portfolio.liquidity')};
    const t={group:'tiers',T1:goalRead('tiers.T1'),T2:goalRead('tiers.T2'),T3:goalRead('tiers.T3')};
    const l={group:'liquidity',usdt:goalRead('liquidity_mix.usdt'),balancer:goalRead('liquidity_mix.balancer'),trading:goalRead('liquidity_mix.trading')};
    const c=['T1','T2','T3'].map(tier=>({group:'custody',tier,hodl:goalRead('custody.'+tier+'.hodl'),core:goalRead('custody.'+tier+'.core'),exchange:goalRead('custody.'+tier+'.exchange')}));
    for(const [name,vals] of [['Cripto/Liquidez',[p.crypto,p.liquidity]],['Tiers',[t.T1,t.T2,t.T3]],['Liquidez/Reservas',[l.usdt,l.balancer,l.trading]],...c.map(x=>['Custodia '+x.tier,[x.hodl,x.core,x.exchange]])]){
      if(Math.abs(vals.reduce((a,b)=>a+b,0)-1)>1e-8)throw Error(name+' debe sumar exactamente 100%.');
    }
    return [p,t,l,...c];
  }
  function goalInput(key,value,label){const holder=el('label','goal-field');holder.append(el('span','',label));
    const inp=el('input');inp.type='number';inp.step='0.01';inp.min='0';inp.max='100';inp.inputMode='decimal';inp.value=cleanFloat(Number(value)*100);inp.dataset.goal=key;
    inp.setAttribute('aria-label',label);inp.addEventListener('input',updateGoalTotals);holder.append(inp);return holder;
  }
  function updateGoalTotals(){totals.replaceChildren();const summaries=[];let valid=true;
    for(const [label,keys] of [['Cripto + Liquidez',['portfolio.crypto','portfolio.liquidity']],['Tiers',['tiers.T1','tiers.T2','tiers.T3']],['Liquidez y reservas',['liquidity_mix.usdt','liquidity_mix.balancer','liquidity_mix.trading']],
      ...['T1','T2','T3'].map(t=>['Custodia '+t,['custody.'+t+'.hodl','custody.'+t+'.core','custody.'+t+'.exchange']])]){
      try{const total=keys.reduce((acc,k)=>acc+goalRead(k),0)*100;const ok=Math.abs(total-100)<1e-6;valid=valid&&ok;summaries.push({label,total,ok});}
      catch(_){valid=false;summaries.push({label,total:NaN,ok:false});}
    }
    const panel=el('div','settings-total-panel goal-sums');summaries.forEach(x=>panel.append(el('span',x.ok?'valid-value':'invalid-value',x.label+': '+(Number.isFinite(x.total)?x.total.toFixed(2)+'%':'N/D')+' / 100%')));totals.append(panel);
    const m=body.querySelector('#goal-preview');
    if(state){
      const total=Number(state.sections.portfolio_goals.usdt_physical_actual);
      const free=Number(state.sections.portfolio_goals.usdt_operating_actual);
      try{
        const fraction=goalRead('liquidity_mix.balancer');
        const amount=Math.round((total*fraction+Number.EPSILON)*100)/100;
        const value=body.querySelector('#balancer-derived-amount');
        if(value)value.textContent=money(amount)+' de base, antes del tope Spot · '+(fraction*100).toFixed(2)+'% × '+money(total);
        if(amount>free+1e-6){valid=false;totals.append(el('p','invalid-value','Reserva Balancer objetivo supera USDT fuera de QF; revisar porcentajes publicados.'));}
      }catch(_){valid=false;}
    }
    if(m&&valid&&state){
      const entries=collectGoals(),g=entries[0],t=entries[1],liq=entries[2],cus=entries.slice(3);
      const base=state.sections.portfolio_goals.token_targets;
      const old=Object.fromEntries(['T1','T2','T3'].map(tier=>[tier,base.filter(r=>r.tier===tier).reduce((a,r)=>a+Number(r.target),0)]));
      const targets=base.map(r=>({token:r.token,percent:old[r.tier]?100*t[r.tier]*r.target/old[r.tier]:0}));
      const h=Object.fromEntries(cus.map(r=>[r.tier,r]));const protectedShare=['T1','T2','T3'].reduce((sum,tier)=>sum+t[tier]*(h[tier].hodl+h[tier].core),0);
      const totals=[g.crypto*protectedShare,g.crypto*(1-protectedShare),g.liquidity*(liq.usdt+liq.balancer),g.liquidity*liq.trading];
      m.replaceChildren(el('strong','',`Vista previa: HODL/Core ${(totals[0]*100).toFixed(2)}%, Exchange ${(totals[1]*100).toFixed(2)}%, Liquidez/Reserva Balancer ${(totals[2]*100).toFixed(2)}%, ReservaTrading ${(totals[3]*100).toFixed(2)}% del patrimonio objetivo.`),
      el('p','settings-hint','Objetivos por token derivados (manga cripto): '+targets.map(x=>x.token+' '+x.percent.toFixed(2)+'%').join(' · ')));
    }else if(m)m.textContent='Completa las seis validaciones al 100% para generar la vista previa.';
    save.disabled=!state?.is_admin||!state?.write_configured||!valid;
  }
  function drawGoals(){
    const g=state.sections.portfolio_goals;
    for(const group of GOAL_GROUPS){
      const card=el('section','goal-card');card.append(el('h4','',group.title),el('p','settings-hint',group.caption));
      const row=el('div','goal-grid');const values=group.id==='portfolio'?g.portfolio:group.id==='tiers'?g.tiers:g.liquidity_mix;
      group.fields.forEach(([key,label])=>row.append(goalInput(group.id+'.'+key,values[key],label+' (%)')));
      card.append(row);body.append(card);
    }
    const assignment=el('section','goal-card');assignment.append(el('h4','','Reservas y topes del portafolio'),
      el('p','settings-hint','Balancer = menor entre su porcentaje de liquidez y su tope del portafolio. Trading = menor entre su porcentaje de liquidez y su tope del portafolio. Los topes se editan en Parámetros y se calculan con Spot vigente en Balancer. QF real permanece protegido.'));
    const value=el('strong','goal-derived-amount');value.id='balancer-derived-amount';
    assignment.append(value,el('p','settings-hint',`USDT físico: ${money(g.usdt_physical_actual)} · USDT fuera de QF: ${money(g.usdt_operating_actual)} · ${g.liquidity_mix_published?'Porcentaje publicado en MASTER':'Porcentaje en borrador; pendiente de publicación'}`));body.append(assignment);
    if(g.reserve_caps){assignment.append(el('p','settings-hint',`Topes publicados: Balancer ${Number(g.reserve_caps.balancer*100).toFixed(2)}% · Trading ${Number(g.reserve_caps.trading*100).toFixed(2)}% del portafolio Spot. Editables en Parámetros.`));}
    const cust=el('section','goal-card');cust.append(el('h4','','4. Custodia por Tier'),el('p','settings-hint','Cada Tier suma 100% entre HODL, Core y Exchange. Son metas, no transferencias.'));
    ['T1','T2','T3'].forEach(t=>{
      const row=el('div','goal-grid');row.append(el('strong','goal-tier',t));
      ['hodl','core','exchange'].forEach(k=>row.append(goalInput('custody.'+t+'.'+k,g.custody[t][k],k==='hodl'?'HODL (%)':k==='core'?'Core (%)':'Exchange (%)')));
      cust.append(row);
    });body.append(cust);
    const preview=el('section','goal-preview');preview.id='goal-preview';body.append(preview);
    body.append(el('p','settings-hint',g.liquidity_mix_published?
      'Reparto de liquidez publicado en 12_PARAMETROS_KAIROS. Reserva Balancer calculada automáticamente desde el porcentaje publicado y el USDT físico. ReservaTrading no altera el saldo físico de Quantfury.':
      'Borrador inicial de reservas 70/20/10 tomado de tu distribución propuesta: AÚN NO PUBLICADO. Requiere autorización administrativa y publicación para ser operativo como objetivo.'));
    updateGoalTotals();
  }
  function fromInput(field,value,entry){
    if(field==='tier')return value;
    if(tab==='parameters'&&field==='value')return fmt.fromDisplay(value,entry);
    if(tab==='units'&&field==='investment_total'&&!/^(?:\d+)(?:[.,]\d{1,2})?$/.test(value.trim()))throw Error('La inversión debe utilizar como máximo 2 decimales');
    if(value.trim()===''&&tab==='pivots')return null;
    const n=Number(value.replace(',','.'));
    if(!value.trim()||!Number.isFinite(n)||n<0)throw Error(`Valor inválido: ${entry.token||entry.key||entry.venue||entry.tier} · ${field}`);
    if(((tab==='targets'||tab==='capital_targets')&&field==='target')||tab==='tier_custody'){
      if(n>100)throw Error('El porcentaje no puede superar 100%');
      return n/100;
    }
    return n;
  }
  function collect(){if(tab==='portfolio_goals')return collectGoals();if(tab==='pivots')return collectPivotMatrix();const originals=state.sections[tab]||[];const out=[];
    originals.forEach((entry,index)=>{const data={[rowKey()]:entry[rowKey()]};let dirty=false;
      for(const [field] of sectionFields[tab]){
        const input=body.querySelector(`[data-index="${index}"][data-field="${field}"]`);
        if(!input)throw Error('Falta un campo');
        let value=fromInput(field,input.value,entry);
        if(tab==='units'&&field==='investment_total'&&input.dataset.userEdited!=='true')value=Number(entry.investment_total);
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
      if(res.status===403&&data.status==='ADMIN_AUTH_REQUIRED'){
        window.location.replace('/admin/login?tab='+encodeURIComponent(tab));
        return;
      }
      if(!res.ok||data.status!=='OK')throw Error(data.message||'Master no disponible');
      state=data;draw();
      hint.replaceChildren();
      if(!data.is_admin){
        // Session expired while Configuration was open: one login gate,
        // never create per-tab administrative links.
        window.location.replace('/admin/login?tab='+encodeURIComponent(tab));
        return;
      }else{
        hint.append(el('span','valid-value','Sesión administrativa activa · cambios auditados'));
        const out=el('button','tiny-control','Cerrar sesión');out.type='button';out.addEventListener('click',async()=>{
          try{await api('/admin/logout',{},state.csrf_token);window.location.assign('/admin/login');}catch(e){message('Error: '+e.message);}});hint.append(out);
      }
      save.disabled=!data.is_admin||!data.write_configured;
      message(!data.write_configured?'Sin permisos de escritura configurados. Solo consulta.':data.is_admin?'Listo. Modifica los valores y pulsa Guardar cambios.':'Consulta activa; inicia sesión administrativa para guardar.');
    }catch(e){state=null;draw();message('DATA ERROR: '+e.message);}
  }
  const initialTab=new URLSearchParams(location.search).get('tab');
  if(initialTab&&Array.from(nav.querySelectorAll('[data-tab]')).some(b=>b.dataset.tab===initialTab)){tab=initialTab;nav.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('selected',x.dataset.tab===tab));}
  nav.addEventListener('click',e=>{const b=e.target.closest('[data-tab]');if(!b)return;tab=b.dataset.tab;
    nav.querySelectorAll('button').forEach(x=>x.classList.toggle('selected',x===b));draw();message('Edición local; aún no se ha publicado ningún cambio.');
    if(tab==='mcp')document.dispatchEvent(new CustomEvent('kairos-mcp-check'));
    if(tab==='pivots'){if(!archiveLoaded)loadArchivedPivots();else applyCachedPivots();}
  });
  save.addEventListener('click',async()=>{
    if(!state||!state.is_admin)return;
    const evidence=document.getElementById('settings-evidence').value.trim();
    let entries;try{entries=collect();if(!entries.length)throw Error('No hay cambios para guardar.');
      if(evidence.length<8)throw Error('Indica justificación o evidencia (mínimo 8 caracteres).');
      if(tab==='targets'&&Math.abs(state.sections.targets.reduce((s,_,i)=>s+rowNum(i,'target'),0)-100)>.000001)throw Error('Los objetivos deben sumar 100%.');
      if(tab==='capital_targets'&&Math.abs(state.sections.capital_targets.reduce((s,_,i)=>s+rowNum(i,'target'),0)-100)>.000001)throw Error('HODL + Core, Exchange, Liquidez y Trading deben sumar 100%; no se reasignan automáticamente.');
      if(tab==='tier_custody')for(let i=0;i<state.sections.tier_custody.length;i++)if(Math.abs(['hodl','core','exchange'].reduce((s,f)=>s+rowNum(i,f),0)-100)>.000001)throw Error('Custodia de cada Tier debe sumar 100%.');
      if(tab==='parameters')for(const stage of ['O2','O3','O4','O5']){
        const group=state.sections.parameters.map((r,i)=>({r,i})).filter(x=>x.r.key.startsWith(`FORECAST_${stage}_FIB_`)&&x.r.key.endsWith('_PCT'));
        if(group.length!==4 || Math.abs(group.reduce((s,x)=>s+rowNum(x.i,'value'),0)-100)>1e-6)
          throw Error(`${stage}: las cuatro asignaciones deben sumar 100%`);
      }
    }catch(e){message('NO VALIDADO: '+e.message);return;}
    const accepted=window.confirm(tab==='pivots'
      ? '¿Validar propuesta de pivotes por onda? Las confirmaciones publicadas serán inmutables y aplicarán a todos los modos.'
      : tab==='portfolio_goals'?'Se validarán seis sumas al 100%, los 12 targets y la custodia de los Tiers. No cambiarán unidades ni USDT físicos. ¿Revisar propuesta?': 'Se validará y publicará una nueva revisión auditada de Google Sheets. ¿Continuar?');if(!accepted)return;
    save.disabled=true;message('Validando integridad, publicando y recargando el Master…');
    try{
      const req={expected_snapshot_id:state.snapshot_id,section:tab,entries,evidence};
      let res;
      if(tab==='pivots'||tab==='portfolio_goals'){
        const response=await fetch('/api/settings/preview',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Kairos-Csrf':state.csrf_token||''},body:JSON.stringify(req)});
        const preview=await response.json();
        if(!response.ok||preview.status!=='VALIDATED_DRAFT')throw Error(preview.reason||preview.status||'Preview inválido');
        if(!window.confirm(`Revisión validada (${preview.changed_fields} campos). ¿PUBLICAR ahora estos objetivos en una nueva versión del Master?`)){message('Validado, NO publicado.');return;}
        res=await api('/api/settings/publish',{...req,preview_token:preview.preview_token,confirm:'PUBLICAR'},state.csrf_token);
      }else res=await api('/api/settings/save',req,state.csrf_token);
      message(`PUBLICADO: ${res.snapshot_id}. ${res.written_fields} campos auditados. Recargando…`);
      await load();message(`Guardado confirmado en Google Sheets: ${res.snapshot_id}. KairosGPT leerá esta revisión en la siguiente ejecución.`);
    }catch(e){message('NO PUBLICADO / VERIFICAR: '+e.message);}finally{save.disabled=!state?.is_admin||!state?.write_configured;}
  });
  function applyPivotCandidate(rec){
    if(!rec||!state||!Array.isArray(state.sections?.pivots))return;
    if(!['CANDIDATO_ARCHIVADO_NO_CERTIFICADO','CANDIDATO_MCP_NO_CERTIFICADO','DATA_ERROR'].includes(rec.status))return;
    if(rec.status!=='DATA_ERROR'){
      const previous=pivots[rec.token];
      // A partial MCP refresh must not wipe an already observed, unconfirmed
      // O1 from this session. User-edited fields remain even more protected.
      if(previous?.o1>0 && !(rec.o1>0))rec={...rec,o1:previous.o1,o1_date:previous.o1_date,
        o1_preliminary_method:previous.o1_preliminary_method,
        warning:(rec.warning||'')+'; O1 preliminar anterior conservado por respuesta MCP parcial'};
      pivots[rec.token]=rec;
    }
    if(tab!=='pivots')return;
    const ix=state.sections.pivots.findIndex(x=>x.token===rec.token);
    if(ix<0)return;
    const current=state.sections.pivots[ix];
    for(const field of ['cycle_low','o1','o2','o3','o4','o5']){
      const input=tab==='pivots'
        ? document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${field}"]`)
        : body.querySelector(`[data-index="${ix}"][data-field="${field}"]`);
      if(!input || input.dataset.userEdited==='true')continue;
      // Historical/approved values from the official table always have priority.
      // MCP only modifies officially PROPUESTO pivots. VALIDADO and
      // CONFIRMADO retain their published anchors unless the admin explicitly edits.
      if(field==='cycle_low'&&current.cl_status!=='PROPUESTO')continue;
      if(field!=='cycle_low'&&current[field+'_status']!=='PROPUESTO')continue;
      const statusField=field==='cycle_low'?'cl_status':field+'_status';
      const statusInput=document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${statusField}"]`);
      // Protect also VALIDADO selected in an unpublished/admin draft.
      if(statusInput?.value!=='PROPUESTO')continue;
      const val=rec[field];
      if(val!==null&&val!==undefined&&rec.status!=='DATA_ERROR'){
        input.value=String(val);
        input.dataset.preloadOrigin=rec.record_origin||rec.source||'MCP_EXPLORATORIO';
      }
    }
    // Suggest dates as well as prices; never replace confirmed or manually edited fields.
    for(const field of ['cl_date',...WAVE_NAMES.map(w=>w+'_date')]){
      const input=document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${field}"]`);
      if(!input||input.disabled||input.dataset.userEdited==='true')continue;
      if(field==='cl_date'&&current.cl_status!=='PROPUESTO')continue;
      if(field!=='cl_date'&&current[field.replace('_date','')+'_status']!=='PROPUESTO')continue;
      const statusField=field==='cl_date'?'cl_status':field.replace('_date','')+'_status';
      const statusInput=document.querySelector(`[data-pivot-token="${rec.token}"][data-pivot-field="${statusField}"]`);
      if(statusInput?.value!=='PROPUESTO')continue;
      const val=rec[field];if(val&&rec.status!=='DATA_ERROR')input.value=val;
    }
    const info=body.querySelector(`[data-pivot-info="${rec.token}"]`);
    if(info){
      const detail=rec.status==='DATA_ERROR'?'MCP no disponible; sin sustitución de campos oficiales':
        `CH: ${rec.cycle_high??'N/D'} (${rec.ch_date||'fecha pendiente'}) · CL: ${rec.cycle_low??'N/D'} (${rec.cl_date||'fecha por verificar'}) · `+
        `O1: ${rec.o1??'N/D'} (${rec.o1_date||'fecha pendiente'}; PRELIMINAR, NO CERTIFICADO) · O2: ${rec.o2??'N/D'} · O3: ${rec.o3??(rec.o3_unconfirmed_high!=null?String(rec.o3_unconfirmed_high)+' (máx. observado sin 5R)':'N/D')}`;
      info.textContent=`${rec.status} · ${rec.record_origin||rec.source||'MCP'} · ${detail} · ${rec.warning||'No certificado, sin órdenes'}`;
    }
  }
  function applyCachedPivots(){Object.values(pivots).forEach(applyPivotCandidate);}
  async function getPivotPayload(url){
    const response=await fetch(url,{cache:'no-store',credentials:'same-origin'});
    const json=await response.json().catch(()=>({status:'DATA_ERROR'}));
    if(!response.ok||!['OK','PARTIAL'].includes(json.status))throw Error(json.reason||json.status||'Error MCP');
    return json;
  }
  async function loadArchivedPivots(){
    const progress=document.getElementById('settings-preliminary-progress');
    progress.textContent='Cargando archivo exploratorio MCP desde Google Sheets…';
    try{
      const response=await getPivotPayload('/api/settings/pivots/preliminary');
      let usable=0;
      for(const rec of response.records||[]){applyPivotCandidate(rec);if(rec.status!=='DATA_ERROR')usable++;}
      archiveLoaded=true;
      progress.textContent=`${usable}/12 activos con información histórica MCP archivada. Para actualizar precios extremos, pulsa «Actualizar candidatos desde MCP».`;
      message('Datos MCP históricos preliminares cargados. No se han modificado ni certificado los pivotes del Master.');
      // Enrich missing O1 in the background, per token, without blocking Settings.
      // Existing official fields and user edits always take priority.
      if(tab==='pivots'&&!autoO1Started&&!refreshingPivots)enrichMissingO1();
    }catch(e){archiveLoaded=false;progress.textContent='No se pudo consultar el archivo de candidatos: '+e.message+'; puedes intentar actualización MCP.';}
  }
  async function enrichMissingO1(){
    if(autoO1Started||!state||tab!=='pivots')return;
    autoO1Started=true;
    const all=(state.sections.pivots||[]).filter(x=>(x.o1===null||x.o1===undefined) && pivots[x.token] && pivots[x.token].cycle_low>0 && pivots[x.token].o1==null);
    const candidates=all.filter(x=>pivots[x.token].cl_date);
    for(const missing of all.filter(x=>!pivots[x.token].cl_date)){
      const info=body.querySelector(`[data-pivot-info="${missing.token}"]`);
      if(info)info.textContent+=' · O1 pendiente: fecha del CL seleccionado sin confirmar; no usar mínimo bruto excluido';
    }
    if(!candidates.length)return;
    const progress=document.getElementById('settings-preliminary-progress');let next=0,done=0,ok=0;
    progress.textContent+=` · Buscando automáticamente máximos O1 preliminares: 0/${candidates.length}`;
    async function worker(){while(next<candidates.length){const rec=candidates[next++];try{
      const response=await getPivotPayload('/api/settings/pivots/preliminary?o1_only=1&token='+encodeURIComponent(rec.token));
      const result=(response.records||[]).find(x=>x.token===rec.token);
      if(result&&result.status!=='DATA_ERROR'&&result.o1>0){applyPivotCandidate(result);ok++;}
    }catch(e){const info=body.querySelector(`[data-pivot-info="${rec.token}"]`);if(info)info.textContent+=' · O1 MCP pendiente: '+e.message;}
    done++;progress.textContent=`Archivo MCP 12/12 · O1 preliminares recalculadas ${done}/${candidates.length} · ${ok} propuestas · no certificadas`;
    }}
    await Promise.all([worker(),worker()]);
  }
  async function reviewUnconfirmedToken(token){
    const rec=(state?.sections?.pivots||[]).find(x=>x.token===token);if(!rec)return;
    for(const wave of ['cl',...WAVE_NAMES]){
      const isCl=wave==='cl';const base=isCl?'cycle_low':wave;const field=isCl?'cl_status':wave+'_status';
      // Technical MCP reevaluation is restricted to PROPUESTO;
      // never silently revalidate or downgrade an already published VAL/CONF.
      if(rec[field]!=='PROPUESTO')continue;
      const priceEl=document.querySelector(`[data-pivot-token="${token}"][data-pivot-field="${base}"]`);
      const dateEl=document.querySelector(`[data-pivot-token="${token}"][data-pivot-field="${isCl?'cl_date':wave+'_date'}"]`);
      const select=document.querySelector(`[data-pivot-token="${token}"][data-pivot-field="${field}"]`);
      const price=Number(priceEl?.value),day=dateEl?.value;
      if(!priceEl||!dateEl||!select||select.value!=='PROPUESTO'||!(price>0)||!day)continue;
      const prevPrice=priceEl.value,prevDate=dateEl.value;
      try{
        const u='/api/settings/pivots/technical-review?'+new URLSearchParams({token,wave,price:String(price),date:day});
        const resp=await fetch(u,{cache:'no-store',credentials:'same-origin'});
        const result=await resp.json();if(!resp.ok)throw Error(result.reason||result.status||'DATA ERROR');
        if(priceEl.value!==prevPrice||dateEl.value!==prevDate)continue;
        if(result.validated&&result.review_proof){
          const proof={price,date:day,proof:result.review_proof};
          if(isCl)clReviewProofs[token]=proof;else waveReviewProofs[token+'|'+wave]=proof;
          select.value='VALIDADO';select.dataset.userEdited='true';updatePivotPublicationHint();
        }else{
          if(isCl)delete clReviewProofs[token];else delete waveReviewProofs[token+'|'+wave];
          // A completed, negative 1W assessment retains PROPUESTO in the
          // draft. Only pivots that were PROPUESTO enter this path.
          // Network errors fall into catch() and preserve prior status instead.
          select.value='PROPUESTO';select.dataset.userEdited='true';updatePivotPublicationHint();
        }
      }catch(e){
        const info=document.getElementById('settings-preliminary-progress');
        if(info)info.textContent+=' · '+token+' '+wave.toUpperCase()+': revisión pendiente';
      }
    }
  }
  async function refreshLivePivots(){
    if(refreshingPivots||!state)return;
    refreshingPivots=true;
    const button=document.getElementById('settings-preliminary');
    const progress=document.getElementById('settings-preliminary-progress');
    button.disabled=true;
    await loadArchivedPivots();
    const tokens=(state.sections.pivots||[]).map(r=>r.token);
    let next=0,ok=0,failed=0;
    progress.textContent=`Actualizando MCP por token: 0/${tokens.length}… Los candidatos archivados permanecen visibles.`;
    async function worker(){
      while(next<tokens.length){
        const token=tokens[next++];
        try{
          const data=await getPivotPayload('/api/settings/pivots/preliminary?token='+encodeURIComponent(token));
          const r=(data.records||[]).find(x=>x.token===token);
          if(!r||r.status==='DATA_ERROR'){
            failed++;
            // Preserve archive evidence, indicate the live failure without overwriting inputs.
            const ix=state.sections.pivots.findIndex(x=>x.token===token);
            const hint=body.querySelector(`[data-pivot-info="${token}"]`);
            if(hint)hint.textContent+=(hint.textContent?' · ':'')+`Actualización MCP falló: ${r?.warning||'sin respuesta'}`;
          }else{
            applyPivotCandidate(r);ok++;
            // One button refreshes/reviews only the PROPUESTO pivots.
            if(state.is_admin)await reviewUnconfirmedToken(token);
            if(token!=='HYPE'&&!(r.o1>0)&&pivots[token]?.cl_date){
              try{
                const fast=await getPivotPayload('/api/settings/pivots/preliminary?o1_only=1&token='+encodeURIComponent(token));
                const proposed=(fast.records||[]).find(x=>x.token===token);
                if(proposed?.o1>0){applyPivotCandidate(proposed);if(state.is_admin)await reviewUnconfirmedToken(token);}
              }catch(e){const hint=body.querySelector(`[data-pivot-info="${token}"]`);
                if(hint)hint.textContent+=' · O1 pendiente por MCP: '+e.message;}
            }
          }
        }catch(e){failed++;const hint=body.querySelector(`[data-pivot-info="${token}"]`);if(hint)hint.textContent+=' · MCP no disponible para actualizar';}
        progress.textContent=`Candidatos MCP: ${ok+failed}/${tokens.length} consultados · ${ok} respuestas recibidas · ${failed} pendientes. La recepción NO equivale a VALIDADO. ${state.is_admin?'Revisión técnica 1W realizada únicamente en pivotes PROPUESTO fechados.':'Inicia sesión como administrador para ejecutar revisión técnica 1W.'} No se ha publicado nada.`;
      }
    }
    try{await Promise.all([worker(),worker()]);
      archiveLoaded=true;
      message(state.is_admin
        ? `MCP: ${ok} tokens consultados, ${failed} pendientes. Verificación 1W solo en PROPUESTO con precio/fecha: VALIDADO requiere prueba técnica; revisa el resultado y usa «Validar → Publicar».`
        : `MCP: ${ok} tokens consultados, ${failed} pendientes. Solo candidatos PROPUESTO: para realizar la validación 1W y obtener estado VALIDADO, inicia sesión de administrador y vuelve a pulsar «Actualizar candidatos desde MCP». No se ha publicado nada.`);
    }finally{refreshingPivots=false;button.disabled=false;}
  }
  document.getElementById('settings-go-publish').addEventListener('click',()=>{
    document.getElementById('settings-evidence').focus();
    document.getElementById('settings-save').scrollIntoView({behavior:'smooth',block:'center'});
  });
  document.getElementById('settings-preliminary').addEventListener('click',refreshLivePivots);
  load();
})();
