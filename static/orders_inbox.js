/* KairosWeb v3.0.15: confirmación en GPT; ejecución de confirmadas en Web. */
(function(root){'use strict';function visible(row,venue='Todos',tier='Todos',side='Todos',token='Todos',level='Todos',status='Todos'){const rowVenue=row.dataset.ordersVenue||row.closest('table')?.dataset.ordersVenue;const rowTier=row.dataset.ordersTier||row.dataset.tier;const effective=['CONFIRMADA','EJECUTADA','PARCIAL','NO_APLICA'].includes(row.dataset.status)?row.dataset.status:'PROPUESTA';return (venue==='Todos'||rowVenue===venue)&&(tier==='Todos'||rowTier===tier)&&(side==='Todos'||row.dataset.side===side)&&(token==='Todos'||row.dataset.token===token)&&(level==='Todos'||row.dataset.stage===level)&&(status==='Todos'||effective===status);}function init(doc){const page=doc.getElementById('orders-inbox');if(!page)return;const ids=['orders-venue','orders-tier','orders-side','orders-token','orders-level','orders-status'];const controls=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));const rows=[...page.querySelectorAll('#orders-list tbody tr[data-token]')];function filter(){let n=0;for(const row of rows){row.hidden=!visible(row,...ids.map(id=>controls[id]?.value||'Todos'));if(!row.hidden)n++;}const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=n!==0;const count=doc.getElementById('orders-filter-count');if(count)count.textContent=n+' de '+rows.length+' órdenes visibles';}for(const id of ids)controls[id]?.addEventListener('change',filter);doc.getElementById('orders-clear-filters')?.addEventListener('click',()=>{for(const id of ids)if(controls[id])controls[id].value='Todos';filter();});filter();}if(typeof module!=='undefined'&&module.exports)module.exports={visible,init};if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));})(typeof window!=='undefined'?window:globalThis);

/* One global save; each successful order is removed before advancing. */
(function(root){'use strict';
async function saveSequential(entries,send,onSaved){
 let saved=0;
 for(const [key,body] of entries){
  try{const result=await send(body);if(result.status!=='OK')throw Error(result.reason||'Respuesta no verificable');onSaved(key,result);saved++;}
  catch(error){return {saved,error};}
 }
 return {saved,error:null};
}
if(typeof module!=='undefined'&&module.exports)module.exports.saveSequential=saveSequential;
if(!root.document)return;
document.addEventListener('DOMContentLoaded',()=>{
 const dialog=document.getElementById('order-manager'),form=document.getElementById('order-manager-form'),page=document.getElementById('orders-inbox'),save=document.getElementById('orders-save-all');if(!dialog||!form||!save)return;
 const pending=new Map(),controls=[...document.querySelectorAll('.orders-next-state')];let selected=null,busy=false,locked=false,validated=false;
 const field=n=>form.elements.namedItem(n),feedback=document.getElementById('orders-management-feedback');
 function refresh(){document.getElementById('orders-pending-count').textContent=pending.size?pending.size+' cambio(s) pendiente(s), incluidos los ocultos por filtros':'Sin cambios pendientes';save.disabled=busy||locked||!pending.size;}
 function bodyFor(control){const item=JSON.parse(control.dataset.order);return {side:item.side||item.lado,stage:item.stage||item.tramo,source:item.category||item.origen||'ESTRUCTURA',token:item.token,venue:item.venue,action:control.value,kairos_order_id:item.kairos_order_id,expected_revision:item.revision,expected_snapshot_id:page.dataset.snapshotId};}
 for(const control of controls)control.addEventListener('change',()=>{
  if(busy||locked)return;
  pending.delete(control);
  if(!control.value){refresh();return;}
  if(control.value==='PROPUESTA'){pending.set(control,bodyFor(control));refresh();return;}
  selected=control;validated=false;form.reset();field('action').value='EJECUTADA';
  const item=JSON.parse(control.dataset.order);
  field('exchange_order_id').value=item.exchange_order_id||'';field('planned_units').value=item.unidades_previstas||'';field('planned_usdt').value=item.importe_previsto||'';field('evidence').value=item.evidencia||'';
  document.getElementById('order-manager-summary').textContent=[item.token,item.tramo||item.stage,item.venue].join(' · ');
  document.getElementById('order-manager-feedback').textContent='Estos datos quedarán pendientes hasta pulsar Guardar cambios en la tabla.';
  for(const n of ['executed_units','executed_usdt'])field(n).required=true;
  refresh();dialog.showModal();
 });
 function cancel(){if(selected&&!validated){pending.delete(selected);selected.value='';}refresh();}
 document.getElementById('order-manager-cancel').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',cancel);
 form.addEventListener('submit',event=>{event.preventDefault();if(!selected||!form.reportValidity())return;pending.set(selected,{...bodyFor(selected),...Object.fromEntries(new FormData(form))});validated=true;refresh();dialog.close();});
 save.addEventListener('click',async()=>{
  if(busy||locked||!pending.size)return;busy=true;refresh();controls.forEach(c=>c.disabled=true);feedback.textContent='Guardando cambios…';
  let auth;
  try{const response=await fetch('/api/admin/session',{credentials:'same-origin'});auth=await response.json();if(!response.ok||!auth.is_admin)throw Error('Accede primero a Configuración con la sesión administrativa.');}
  catch(error){busy=false;controls.forEach(c=>c.disabled=false);feedback.textContent=error.message;refresh();return;}
  const result=await saveSequential([...pending.entries()],async body=>{
   const response=await fetch('/api/orders/manage',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Kairos-Csrf':auth.csrf_token},body:JSON.stringify(body)});
   const data=await response.json();if(!response.ok)throw Error(data.reason||'No se pudo verificar el guardado');return data;
  },(control)=>{pending.delete(control);control.value='';control.disabled=true;});
  busy=false;
  if(result.error){locked=true;feedback.textContent=result.saved+' cambio(s) guardado(s). Se detuvo el guardado: '+result.error.message+' Recarga y consulta el historial antes de reintentar; el último cambio podría haberse registrado.';refresh();return;}
  feedback.textContent=result.saved+' cambio(s) guardado(s).';refresh();window.location.reload();
 });
 refresh();
});
})(typeof window!=='undefined'?window:globalThis);
