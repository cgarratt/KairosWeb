/* Spot snapshot is read once per server worker; manual refresh is opt-in. */
(()=>{'use strict';
 const btn=document.getElementById('spot-refresh');const label=document.getElementById('spot-observed');
 if(!btn||!label)return;
 function show(data){const at=data?.last_valid_observed_at||data?.observed_at;
   label.textContent=at?'Spot observado: '+at.replace('T',' ').replace(/\.\d+(?=Z|\+)/,''):'Spot: sin observación';
   label.title='Precios de la observación indicada. No se actualizan automáticamente.';
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
