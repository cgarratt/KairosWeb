(() => {
  'use strict';
  const bell = document.getElementById('bell-open');
  const box = document.getElementById('alerts-popover');
  const list = document.getElementById('alerts-list');
  const count = document.getElementById('bell-count');
  const refresh = document.getElementById('alerts-refresh');
  if (!bell || !box || !list || !count) return;
  function el(tag, cls, txt) {
    const node = document.createElement(tag);
    if (cls) node.className=cls;
    if (txt !== undefined) node.textContent=String(txt);
    return node;
  }
  const formatDate = (iso) => {
    const date=new Date(iso);
    return Number.isNaN(date.getTime()) ? iso : new Intl.DateTimeFormat('es-PE', {
      timeZone:'America/Lima',day:'2-digit',month:'2-digit',year:'numeric',
      hour:'2-digit',minute:'2-digit',hour12:false
    }).format(date)+' (Lima)';
  };
  async function load() {
    list.textContent='Consultando Google Sheets…';
    try {
      const response = await fetch('/api/alerts/unread', {credentials:'same-origin',cache:'no-store'});
      const data=await response.json();
      if (!response.ok || data.status!=='OK') throw Error(data.message || 'No se pudo cargar Alertas 1H');
      count.hidden=!data.unread_count;
      count.textContent=data.unread_count>99?'99+':String(data.unread_count);
      list.replaceChildren();
      if (!data.records.length) {list.append(el('p','settings-hint','No hay alertas 1H históricas sin leer.'));return;}
      data.records.forEach(item=> {
        const wrap=el('article','alert-record');
        const top=el('div','alert-meta');
        top.append(el('span','alert-token',item.token), el('span','',formatDate(item.created_utc)));
        top.append(el('span','alert-flag',item.state));
        if (item.certification && item.certification!=='CERTIFICADA') top.append(el('span','alert-flag unverified',item.certification));
        wrap.append(top,el('p','alert-action','Acción: '+item.action));
        const done=el('button','tiny-control','Marcar como leída');
        done.type='button';
        if(!data.can_mark_read){done.disabled=true;done.title='Requiere la cuenta editora de Google Sheets en Render';done.textContent='Lectura pendiente · requiere editor';}
        done.addEventListener('click',async()=>{
          done.disabled=true;done.textContent='Guardando…';
          try {
            const res=await fetch('/api/alerts/read',{
              method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',
              body:JSON.stringify({id:item.id})
            });
            const out=await res.json();
            if (!res.ok || out.status!=='OK') throw Error(out.reason || out.message || 'No se pudo guardar');
            await load();
          }catch(e){done.textContent='Error: '+e.message;done.disabled=false;}
        });
        wrap.append(done);list.append(wrap);
      });
      if(data.limited)list.append(el('p','settings-hint','Vista limitada a 150 eventos. Los demás siguen registrados en el Master.'));
    }catch(e) { count.hidden=true;list.textContent='DATA ERROR: '+e.message; }
  }
  bell.addEventListener('click',()=>{
    const open=box.hidden;box.hidden=!open;bell.setAttribute('aria-expanded',String(open));
    if(open)load();
  });
  refresh.addEventListener('click',load);
  document.addEventListener('click',e=>{if(!box.hidden && !e.target.closest('.alerts-wrap')){box.hidden=true;bell.setAttribute('aria-expanded','false');}});
  load();
  // Gentle refresh, no push claim. Visibility blocks repeated hidden-tab network calls.
  setInterval(()=>{if(!document.hidden)load();},60000);
})();
