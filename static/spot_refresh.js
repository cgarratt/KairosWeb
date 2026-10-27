/* Display only: compact America/Lima time, full timestamp in tooltip. */
(function(root){
 'use strict';
 function formatSpotTime(value){
   if(!value)return null;
   // Never guess a timezone for a timestamp that does not declare one.
   if(typeof value!=='string'||!/(Z|[+-]\d{2}:\d{2})$/.test(value))return null;
   const date=new Date(value);if(!Number.isFinite(date.getTime()))return null;
   const time=new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(date);
   const full=new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(date);
   return {label:'Spot: '+time,title:'Observado: '+full+' · Lima. No se actualiza automáticamente.'};
 }
 root.KairosSpotTime={formatSpotTime};
 if(typeof module!=='undefined'&&module.exports)module.exports={formatSpotTime};
})(globalThis);
/* Spot snapshot is read once per server worker; manual refresh is opt-in. */
(()=>{'use strict';
 if(typeof document==='undefined')return;
 const btn=document.getElementById('spot-refresh');const label=document.getElementById('spot-observed');
 if(!btn||!label)return;
 function show(data){const at=data?.last_valid_observed_at||data?.observed_at;
   const formatted=globalThis.KairosSpotTime.formatSpotTime(at);
   label.textContent=formatted?formatted.label:'Spot: sin observación';
   label.title=formatted?formatted.title:'Fecha de observación no disponible o sin zona horaria.';
 }
 fetch('/api/market-status',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(show).catch(()=>{label.textContent='Spot: estado N/D'});
 btn.addEventListener('click',async()=>{btn.disabled=true;btn.textContent='Actualizando…';
   try{const r=await fetch('/api/spot/refresh',{method:'POST',credentials:'same-origin',headers:{'X-Kairos-Csrf':btn.dataset.csrf,'Content-Type':'application/json'},body:'{}'});
     const data=await r.json();show(data);if(!r.ok||data.status!=='OK'){label.textContent='Actualización fallida · '+(data.diagnostic?.code||data.status);return;}
     window.location.reload();
   }catch(_){label.textContent='Actualización fallida · red';}
   finally{btn.disabled=false;btn.textContent='↻ Actualizar Spot';}
 });
})();
