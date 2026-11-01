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
 let retryAt=0,busy=false;
 function updatePause(){const paused=retryAt>Date.now();btn.disabled=busy||paused;
   if(paused){const seconds=Math.ceil((retryAt-Date.now())/1000);
     btn.textContent='En pausa · '+Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');
   }else if(!busy){btn.textContent='↻ Actualizar Spot';}
 }
 function show(data){const raw=data?.diagnostic?.retry_at_utc||data?.retry_at_utc;
   if(raw){const parsed=Date.parse(raw);if(Number.isFinite(parsed))retryAt=parsed;}
   updatePause();
   const at=data?.last_valid_observed_at||data?.observed_at;
   const formatted=globalThis.KairosSpotTime.formatSpotTime(at);
   label.textContent=formatted?formatted.label:'Spot: sin observación';
   label.title=formatted?formatted.title:'Fecha de observación no disponible o sin zona horaria.';
   if(retryAt>Date.now())label.textContent='Binance en pausa hasta '+new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',dateStyle:'short',timeStyle:'medium'}).format(new Date(retryAt))+' · Lima';
 }
 fetch('/api/market-status',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(show).catch(()=>{label.textContent='Spot: estado N/D'});
 for(const node of document.querySelectorAll('.spot-retry-at')){
   const date=new Date(node.getAttribute('datetime'));if(Number.isFinite(date.getTime())){
     node.textContent=new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',dateStyle:'short',timeStyle:'medium'}).format(date)+' · Lima';
     retryAt=Math.max(retryAt,date.getTime());
   }
 }
 updatePause();setInterval(updatePause,1000);
 btn.addEventListener('click',async()=>{if(busy||retryAt>Date.now())return;busy=true;btn.disabled=true;btn.textContent='Actualizando…';
   try{const r=await fetch('/api/spot/refresh',{method:'POST',credentials:'same-origin',headers:{'X-Kairos-Csrf':btn.dataset.csrf,'Content-Type':'application/json'},body:'{}'});
     const data=await r.json();show(data);if(!r.ok||data.status!=='OK'){if(retryAt<=Date.now())label.textContent='Actualización fallida · '+(data.diagnostic?.code||data.status);return;}
     window.location.reload();
   }catch(_){label.textContent='Actualización fallida · red';}
   finally{busy=false;updatePause();}
 });
})();
