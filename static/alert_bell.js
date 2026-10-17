(() => {
  'use strict';
  const bell=document.getElementById('bell-open'),box=document.getElementById('alerts-popover');
  const list=document.getElementById('alerts-list'),count=document.getElementById('bell-count');
  const refresh=document.getElementById('alerts-refresh'),all=document.getElementById('alerts-read-all');
  if(!bell||!box||!list||!count||!all)return;
  const el=(tag,cls,value)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(value!==undefined)x.textContent=value;return x;};
  const formatDate=iso=>{const t=new Date(iso);return isNaN(t.getTime())?iso:new Intl.DateTimeFormat('es-PE',{
    timeZone:'America/Lima',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(t)+' (Lima)';};
  let pending=0;
  async function load(){
    list.textContent='Consultando el histórico de KairosGPT…';
    try{const r=await fetch('/api/alerts/unread',{credentials:'same-origin',cache:'no-store'}),v=await r.json();
      if(!r.ok||v.status!=='OK')throw Error(v.message||'No disponible');
      pending=Number(v.unread_count)||0;count.hidden=!pending;count.textContent=pending>99?'99+':String(pending);
      all.disabled=!pending||!v.can_mark_read;
      all.title=v.can_mark_read?'Marcar todas las alertas 1H sin leer':'Requiere credencial Google editora';
      list.replaceChildren();
      if(!v.records.length){list.append(el('p','settings-hint','No quedan Alertas Kairos sin leer.'));return;}
      for(const item of v.records){const wrap=el('article','alert-record'),heading=el('div','alert-meta');
        heading.append(el('span','alert-token',item.token),el('span','',formatDate(item.created_utc)));
        heading.append(el('span','alert-flag',item.state));
        if(item.certification!=='CERTIFICADA')heading.append(el('span','alert-flag unverified',item.certification));
        wrap.append(heading,el('p','alert-action','Acción: '+item.action));list.append(wrap);
      }
      if(v.limited)list.append(el('p','settings-hint','Se muestran los 150 más recientes; el botón marcará TODOS los históricos 1H sin leer.'));
    }catch(e){count.hidden=true;all.disabled=true;list.textContent='DATA ERROR: '+e.message;}
  }
  all.addEventListener('click',async()=>{
    if(!pending)return;
    if(!confirm(`¿Marcar como leídas las ${pending} alertas 1H pendientes? Se conservará su historial.`))return;
    all.disabled=true;all.textContent='Guardando…';
    try{const r=await fetch('/api/alerts/read-all',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});
      const v=await r.json();if(!r.ok||v.status!=='OK')throw Error(v.reason||v.message||'Error al actualizar');
      await load();
    }catch(e){list.prepend(el('p','invalid-value','No se pudieron marcar las alertas: '+e.message));all.disabled=false;}
    finally{all.textContent='Marcar todas como leídas';}
  });
  bell.addEventListener('click',()=>{const open=box.hidden;box.hidden=!open;bell.setAttribute('aria-expanded',String(open));if(open)load();});
  refresh.addEventListener('click',load);
  document.addEventListener('click',e=>{if(!box.hidden&&!e.target.closest('.alerts-wrap')){box.hidden=true;bell.setAttribute('aria-expanded','false');}});
  load();setInterval(()=>{if(!document.hidden)load();},60000);
})();
