(() => {
  'use strict';
  const panel=document.getElementById('settings-mcp-panel');
  if(!panel)return;
  const msg=document.getElementById('mcp-message');
  const lang=new Intl.DateTimeFormat('es-PE',{dateStyle:'short',timeStyle:'medium',timeZone:'America/Lima'});
  const providers=['binance','hyperliquid'];
  const deepButton=document.getElementById('health-check-all'),deepOutput=document.getElementById('health-check-output');
  let working=new Set();
  function render(provider,result){
    const card=panel.querySelector(`[data-provider="${provider}"]`);
    if(!card)return;
    const state=card.querySelector('.mcp-health-state'),stamp=card.querySelector('.mcp-health-checked');
    const status=result?.status||'SIN_VERIFICAR';
    const label={OK:'Conectado',DATA_ERROR:'No disponible',NOT_CONFIGURED:'No configurado'}[status]||status;
    state.textContent=label+(provider==='binance'&&result?.records?` · ${result.records}/12 precios`: '');
    state.dataset.status=status;
    const when=result?.last_success_utc;
    stamp.textContent=when?`Última respuesta exitosa: ${lang.format(new Date(when))} (Lima)`:'Sin respuesta exitosa registrada en este proceso';
    if(result?.diagnostic?.category)stamp.textContent+=` · Diagnóstico: ${result.diagnostic.category}`;
  }
  async function check(provider,refresh=false){
    if(working.has(provider))return;
    working.add(provider);
    const card=panel.querySelector(`[data-provider="${provider}"]`);
    for(const button of card.querySelectorAll('button'))button.disabled=true;
    card.querySelector('.mcp-health-state').textContent=refresh?'Refrescando sesión MCP…':'Verificando conectividad…';
    msg.textContent=refresh?'Reintentando con una sesión nueva del MCP. No se reiniciará Render.':'Consultando estado MCP…';
    try{
      let url='/api/mcp-diagnostics?provider='+encodeURIComponent(provider),opts={credentials:'same-origin',cache:'no-store'};
      if(refresh){
        const res=await fetch('/api/admin/session',{credentials:'same-origin',cache:'no-store'});
        const credentials=await res.json();
        if(!res.ok||!credentials.is_admin||!credentials.csrf_token)throw new Error('Inicia sesión administrativa antes de refrescar. Verificación funciona sin sesión.');
        url='/api/mcp-refresh';opts={method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json','X-Kairos-Csrf':credentials.csrf_token},body:JSON.stringify({provider})};
      }
      const response=await fetch(url,opts),data=await response.json();
      const result=refresh?data.result:data.providers?.[provider];
      if(result)render(provider,result);
      else render(provider,{status:'DATA_ERROR'});
      if(!response.ok||!result||result.status!=='OK')throw new Error('No hay conexión válida. Consulta el estado y los logs privados de Render.');
      msg.textContent=`${provider==='binance'?'Binance':'Hyperliquid'} MCP conectado. Consulta de solo lectura validada.`;
    }catch(error){
      if(!card.querySelector('.mcp-health-state').dataset.status)render(provider,{status:'DATA_ERROR'});
      msg.textContent=error.message||'No se pudo completar la consulta MCP.';
    }finally{
      working.delete(provider);for(const button of card.querySelectorAll('button'))button.disabled=false;
    }
  }
  if(deepButton&&deepOutput){
    deepButton.addEventListener('click',async()=>{
      deepButton.disabled=true;
      deepOutput.textContent='Verificando las tres dependencias…';
      try{
        const resp=await fetch('/api/health/diagnostics',{credentials:'same-origin',cache:'no-store'});
        const data=await resp.json();
        const providers=data.operational_providers||{},modules=data.functional_modules||{};
        // textContent only: never interpret provider response as HTML.
        const providerText=['sheets','binance','hyperliquid'].map(p=>p+': '+(providers[p]?.status||'SIN_VERIFICAR')).join(' · ');
        const moduleText=Object.keys(modules).sort().map(m=>m+': '+modules[m].status).join(' · ');
        deepOutput.textContent='Servidor: '+(data.server?.status||'N/D')+' | Proveedores: '+providerText+' | Módulos (solo dependencias): '+moduleText+' | UTC: '+(data.checked_utc||'N/D')+(resp.ok?'':' | Requiere revisión');
      }catch(err){
        deepOutput.textContent='DATA_ERROR: no fue posible completar el diagnóstico; revisar conexión y logs privados.';
      }finally{deepButton.disabled=false;}
    });
  }
  const certifyButton=document.getElementById('master-homologate-current');
  const certifyOutput=document.getElementById('master-homologate-output');
  const readinessButton=document.getElementById('master-homologation-check');
  const certifyState=document.getElementById('master-homologation-readiness');
  async function getHomologationReadiness(){
    const response=await fetch('/api/settings/homologation-status',{credentials:'same-origin',cache:'no-store'});
    const payload=await response.json();
    if(!response.ok){throw new Error([payload.error_code||'HOM_READ_ERROR',payload.phase||'READ',payload.reason||'Error de lectura'].join(' · '));}
    return payload;
  }
  async function refreshHomologationReadiness(){
    if(!certifyState)return null;
    try{
      const payload=await getHomologationReadiness();
      certifyState.textContent=(payload.status==='CURRENT'?'CURRENT · Certificación vigente':
        ('PENDIENTE · '+(payload.ledger_present?'Hoja 25 presente, falta certificar snapshot actual':'No existe hoja 25: se creará al homologar')))+
        ' · Snapshot '+payload.snapshot_id;
      return payload;
    }catch(error){certifyState.textContent=error.message||'No fue posible comprobar homologación';return null;}
  }
  if(readinessButton)readinessButton.addEventListener('click',refreshHomologationReadiness);
  if(certifyButton&&certifyOutput){
    certifyButton.addEventListener('click',async()=>{
      certifyButton.disabled=true;
      certifyOutput.textContent='Comprobando estado de homologación del MASTER…';
      try{
        const auth=await fetch('/api/admin/session',{credentials:'same-origin',cache:'no-store'});
        const account=await auth.json();
        if(!auth.ok||!account.is_admin||!account.csrf_token)throw new Error('Inicia sesión administrativa en Configuración.');
        const readiness=await getHomologationReadiness();
        if(readiness.status==='CURRENT'){
          certifyOutput.textContent='Ya homologado: '+readiness.snapshot_id+' · CURRENT';return;
        }
        const snapshot=readiness.snapshot_id;
        if(!window.confirm('¿Homologar contabilidad del snapshot '+snapshot+'? '+
          (readiness.ledger_present?'Se registrará una certificación en hoja 25.':'Se creará hoja 25 y su primera certificación.')+
          ' No cambiará unidades, saldos, pivotes ni órdenes.')){
          certifyOutput.textContent='Sin cambios: homologación cancelada.';return;
        }
        certifyOutput.textContent='Validando y registrando homologación…';
        const response=await fetch('/api/settings/homologate',{
          method:'POST',credentials:'same-origin',cache:'no-store',
          headers:{'Content-Type':'application/json','X-Kairos-Csrf':account.csrf_token},
          body:JSON.stringify({expected_snapshot_id:snapshot,confirm:'HOMOLOGAR'})});
        const result=await response.json();
        if(!response.ok||result.status!=='OK'){
          const code=result.error_code||result.status||'HOM_UNKNOWN';
          const phase=result.phase||'UNKNOWN';
          const incident=result.error_id?' · Incidente '+result.error_id:'';
          const retry=result.write_may_have_committed?' · Verifica hoja 25 antes de repetir la acción.':'';
          throw new Error(code+' · '+phase+' · '+(result.reason||'No se pudo verificar la homologación.')+incident+retry);
        }
        certifyOutput.textContent=(result.already_homologated?'Ya homologado: ':'Homologación registrada: ')+
          result.snapshot_id+' · '+result.verification+' · '+result.ledger_tab+
          ' · Contabilidad base validada; pivotes y BSI siguen pendientes.';
        await refreshHomologationReadiness();
      }catch(error){certifyOutput.textContent=error.message||'DATA_ERROR de homologación';}
      finally{certifyButton.disabled=false;}
    });
    if(new URLSearchParams(location.search).get('tab')==='mcp')refreshHomologationReadiness();
  }
  panel.addEventListener('click',event=>{
    const button=event.target.closest('button[data-provider]');if(!button)return;
    check(button.dataset.provider,button.classList.contains('mcp-refresh'));
  });
  document.addEventListener('kairos-mcp-check',()=>{if(!panel.hidden)providers.forEach(p=>check(p));});
  if(new URLSearchParams(location.search).get('tab')==='mcp')providers.forEach(p=>check(p));
})();
