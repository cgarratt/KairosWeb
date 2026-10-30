/* KairosWeb v3.0.15: confirmación en GPT; ejecución de confirmadas en Web. */
(function(root){'use strict';function visible(row,venue='Todos',tier='Todos',side='Todos',token='Todos',level='Todos',status='Todos'){const rowVenue=row.dataset.ordersVenue||row.closest('table')?.dataset.ordersVenue;const rowTier=row.dataset.ordersTier||row.dataset.tier;const effective=['CONFIRMADA','EJECUTADA','PARCIAL','NO_APLICA'].includes(row.dataset.status)?row.dataset.status:'PROPUESTA';return (venue==='Todos'||rowVenue===venue)&&(tier==='Todos'||rowTier===tier)&&(side==='Todos'||row.dataset.side===side)&&(token==='Todos'||row.dataset.token===token)&&(level==='Todos'||row.dataset.stage===level)&&(status==='Todos'||effective===status);}function init(doc){const page=doc.getElementById('orders-inbox');if(!page)return;const ids=['orders-venue','orders-tier','orders-side','orders-token','orders-level','orders-status'];const controls=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));const rows=[...page.querySelectorAll('#orders-list tbody tr[data-token]')];function filter(){let n=0;for(const row of rows){row.hidden=!visible(row,...ids.map(id=>controls[id]?.value||'Todos'));if(!row.hidden)n++;}const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=n!==0;const count=doc.getElementById('orders-filter-count');if(count)count.textContent=n+' de '+rows.length+' órdenes visibles';}for(const id of ids)controls[id]?.addEventListener('change',filter);doc.getElementById('orders-clear-filters')?.addEventListener('click',()=>{for(const id of ids)if(controls[id])controls[id].value='Todos';filter();});filter();}if(typeof module!=='undefined'&&module.exports)module.exports={visible,init};if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));})(typeof window!=='undefined'?window:globalThis);

/* Administrative journal updates; no exchange order submission. */
(function(){'use strict';if(typeof document==='undefined')return;
document.addEventListener('DOMContentLoaded',()=>{
 const dialog=document.getElementById('order-manager'),form=document.getElementById('order-manager-form'),page=document.getElementById('orders-inbox');if(!dialog||!form)return;let selected=null;
 const field=n=>form.elements.namedItem(n),feedback=document.getElementById('order-manager-feedback');
 function toggle(){const action=field('action').value,fill=['PARCIAL','EJECUTADA'].includes(action),active=action==='EJECUTADA';document.getElementById('order-fill-fields').hidden=!fill;
 for(const n of ['executed_units','executed_usdt']){field(n).required=fill;field(n).disabled=!fill;}
 for(const n of ['exchange_order_id','planned_units','planned_usdt','evidence']){field(n).required=active;field(n).disabled=!active;}}
 document.querySelectorAll('[data-order]').forEach(button=>button.addEventListener('click',()=>{
 selected=JSON.parse(button.dataset.order);if((selected.effective_status||selected.display_status||selected.estado)!=='NO_APLICA' && selected.estado!=='CONFIRMADA')return;form.reset();feedback.textContent='';
 const q=selected.quantity??selected.unidades_previstas??0,a=selected.usdt??selected.importe_previsto??0;
 field('planned_units').value=q;field('planned_usdt').value=a;field('executed_units').value='';field('executed_usdt').value='';field('exchange_order_id').value=selected.exchange_order_id||'';
 for(const option of field('action').options)option.disabled=option.value!==(selected.estado==='CONFIRMADA'?'EJECUTADA':'PROPUESTA');
 field('action').value=selected.estado==='CONFIRMADA'?'EJECUTADA':'PROPUESTA';
 document.getElementById('order-manager-summary').textContent=[selected.token,selected.stage||selected.tramo,selected.venue].join(' · ');toggle();dialog.showModal();}));
 field('action').addEventListener('change',toggle);document.getElementById('order-manager-cancel').addEventListener('click',()=>dialog.close());
 form.addEventListener('submit',async event=>{event.preventDefault();const submit=form.querySelector('[type="submit"]');submit.disabled=true;feedback.textContent='Guardando…';
 try{const auth=await fetch('/api/admin/session',{credentials:'same-origin'}).then(r=>r.json());if(!auth.is_admin)throw Error('Accede primero a Configuración con tu sesión administrativa y vuelve a Órdenes.');
 const body=Object.fromEntries(new FormData(form));const action=body.action;
 Object.assign(body,{side:selected.side||selected.lado,stage:selected.stage||selected.tramo,source:selected.category||selected.origen||'ESTRUCTURA',token:selected.token,venue:selected.venue,expected_snapshot_id:page.dataset.snapshotId});
 body.action=action;body.kairos_order_id=selected.kairos_order_id;body.expected_revision=selected.revision;
 const response=await fetch('/api/orders/manage',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Kairos-Csrf':auth.csrf_token},body:JSON.stringify(body)});const data=await response.json();if(!response.ok)throw Error(data.reason||'No se pudo guardar; consulta el historial antes de reintentar.');
 feedback.textContent=data.notice||'Estado guardado.';window.location.reload();
 }catch(error){feedback.textContent=error.message;}finally{submit.disabled=false;}});
});})();
