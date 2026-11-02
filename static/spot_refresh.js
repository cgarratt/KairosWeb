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
/* No Binance request on page load; only the explicit refresh button loads data. */
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
 function show(data){const raw=data?.retry_at_utc;
   retryAt=0;
   if(raw){const parsed=Date.parse(raw);if(Number.isFinite(parsed))retryAt=parsed;}
   updatePause();
   const at=data?.last_valid_observed_at||data?.observed_at;
   const formatted=globalThis.KairosSpotTime.formatSpotTime(at);
   label.textContent=(formatted?formatted.label:'Spot: sin observación')+(data?.source?' · '+data.source+(data?.fallback_active?' (respaldo)':' (primario)'):'');
   label.title=formatted?formatted.title:'Fecha de observación no disponible o sin zona horaria.';
   if(retryAt>Date.now())label.textContent='Proveedor en pausa hasta '+new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',dateStyle:'short',timeStyle:'medium'}).format(new Date(retryAt))+' · Lima';
 }
 fetch('/api/market-status',{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(show).catch(()=>{label.textContent='Spot: estado N/D'});
 updatePause();setInterval(updatePause,1000);
 btn.addEventListener('click',async()=>{if(busy||retryAt>Date.now())return;busy=true;btn.disabled=true;btn.textContent='Actualizando…';
   try{const r=await fetch('/api/spot/refresh',{method:'POST',credentials:'same-origin',headers:{'X-Kairos-Csrf':btn.dataset.csrf,'Content-Type':'application/json'},body:'{}'});
     const data=await r.json();show(data);if(!r.ok||data.status!=='OK'){if(retryAt<=Date.now())label.textContent='Actualización fallida · '+(data.diagnostic?.code||data.status);return;}
     window.location.reload();
   }catch(_){label.textContent='Actualización fallida · red';}
   finally{busy=false;updatePause();}
 });
})();

/* Configuration owns historical maintenance; independent of the global Spot button. */
(()=>{'use strict';
 if(typeof document==='undefined')return;
 const button=document.getElementById('history-refresh'),status=document.getElementById('history-observed');
 if(!button||!status)return;
 const format=new Intl.DateTimeFormat('es-PE',{timeZone:'America/Lima',dateStyle:'short',timeStyle:'short'});
 function show(data){
   const day=data.history_day_utc;
   status.textContent=(data.history_current?'Al último cierre UTC':'Pendiente de actualización')+
     (day?' · Cierre: '+format.format(new Date(day+'T00:00:00Z'))+' (Lima)':' · Sin carga histórica')+
     (data.history_source?' · '+data.history_source:'');
 }
 async function load(){const r=await fetch('/api/market-status',{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('Estado no disponible');show(await r.json());}
 load().catch(()=>{status.textContent='Estado de históricos N/D';});
 button.addEventListener('click',async()=>{
   button.disabled=true;status.textContent='Actualizando históricos…';
   try{
     const response=await fetch('/api/history/refresh',{method:'POST',credentials:'same-origin',headers:{'X-Kairos-Csrf':button.dataset.csrf,'Content-Type':'application/json'},body:'{}'});
     const data=await response.json();
     if(!response.ok||data.status!=='OK')throw Error(data.diagnostic?.code||data.status);
     await load();
   }catch(error){status.textContent='Históricos no actualizados · '+error.message;}
   finally{button.disabled=false;}
 });
})();
