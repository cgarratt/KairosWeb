(() => {
  'use strict';
  const bell=document.getElementById('bell-open'),box=document.getElementById('alerts-popover');
  const list=document.getElementById('alerts-list'),count=document.getElementById('bell-count');
  const refresh=document.getElementById('alerts-refresh'),all=document.getElementById('alerts-read-all');
  if(!bell||!box||!list||!count||!all)return;
  const el=(tag,cls,value)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(value!==undefined)x.textContent=value;return x;};
  const formatDate=iso=>{const t=new Date(iso);return isNaN(t.getTime())?iso:new Intl.DateTimeFormat('es-PE',{
    timeZone:'America/Lima',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(t)+' (Lima)';};
  let pending=0,writer=false,loading=false;
  const frameClass=frame=>({ '1H':'tf-1h','4H':'tf-4h','1D':'tf-1d' })[frame]||'';
  async function acknowledge(id,button){
    button.disabled=true;button.textContent='Guardando…';
    try{
      const r=await fetch('/api/alerts/read',{method:'POST',credentials:'same-origin',
        headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
      const v=await r.json();if(!r.ok||v.status!=='OK')throw Error(v.reason||v.message||'No disponible');
      await load();
    }catch(e){button.disabled=false;button.textContent='Marcar leída';list.prepend(el('p','invalid-value','Error al marcar lectura: '+e.message));}
  }
  async function load(){
    if(loading)return;
    loading=true;
    list.textContent='Consultando alertas Kairos 1H / 4H / 1D…';
    try{
      const r=await fetch('/api/alerts/unread',{credentials:'same-origin',cache:'no-store'}),v=await r.json();
      if(!r.ok||v.status!=='OK')throw Error(v.reason||v.message||'No disponible');
      pending=Number(v.unread_count)||0;
      writer=Boolean(v.can_mark_read);
      count.hidden=!pending;count.textContent=pending>99?'99+':String(pending);
      all.disabled=!pending||!writer;
      all.title=writer?'Marcar todas las alertas 1H / 4H / 1D como leídas':'Requiere credencial Google editora';
      list.replaceChildren();
      if(!v.records.length){list.append(el('p','settings-hint','No hay alertas pendientes en 1H, 4H ni 1D.'));return;}
      for(const item of v.records){
        const wrap=el('article','alert-record'),heading=el('div','alert-meta');
        const tf=['1H','4H','1D'].includes(item.timeframe)?item.timeframe:'N/D';
        heading.append(el('span','alert-timeframe '+frameClass(tf),tf),
                       el('span','alert-token',item.token||'PORTAFOLIO'),
                       el('span','',formatDate(item.created_utc)));
        const kind=String(item.kind||'ALERTA').replaceAll('_',' ');
        heading.append(el('span','alert-event-type',kind));
        if(item.is_trade_ready===true){
          heading.append(el('span','alert-flag','CERTIFICADA'));
        }else{
          heading.append(el('span','alert-flag unverified','INFORMATIVA'));
        }
        wrap.append(heading);
        if(item.action)wrap.append(el('p','alert-action', (item.is_trade_ready?'Acción certificada: ':'Detalle informativo: ')+item.action));
        if(!item.is_trade_ready)wrap.append(el('p','alert-disclaimer','No constituye orden ni fill verificado.'));
        const controls=el('div','alert-record-controls');
        const readButton=el('button','tiny-control alert-read-one','Marcar leída');
        readButton.type='button';readButton.disabled=!writer;
        readButton.addEventListener('click',()=>acknowledge(item.id,readButton));
        controls.append(readButton);wrap.append(controls);list.append(wrap);
      }
      if(v.limited)list.append(el('p','settings-hint','Se muestran las 150 más recientes. Marcar todas incluye también las alertas no visibles.'));
    }catch(e){count.hidden=true;all.disabled=true;list.textContent='DATA ERROR: '+e.message;}
    finally{loading=false;}
  }
  all.addEventListener('click',async()=>{
    if(!pending||!writer)return;
    if(!confirm(`¿Marcar como leídas las ${pending} notificaciones 1H/4H/1D pendientes? Se conservará su historial.`))return;
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
