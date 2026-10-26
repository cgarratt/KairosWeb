/* Kairos order management. All mutations are admin-gated and append-only in Sheets.
   No exchange API calls and no automatic inventory/accounting changes. */
(function(root){
'use strict';
function visible(row,venue='Todos',tier='Todos',side='Todos',token='Todos',level='Todos',status='Todos'){
 const rowVenue=row.dataset.ordersVenue||row.closest('table')?.dataset.ordersVenue;
 const rowTier=row.dataset.ordersTier||row.dataset.tier;
 return (venue==='Todos'||rowVenue===venue)&&
        (tier==='Todos'||rowTier===tier)&&
        (side==='Todos'||row.dataset.side===side)&&
        (token==='Todos'||row.dataset.token===token)&&
        (level==='Todos'||row.dataset.stage===level)&&
        (status==='Todos'||row.dataset.status===status);
}
function initialFields(btn){
 const d=btn.dataset,action=d.manage;
 return {action, kairos_order_id:d.id||'',expected_revision:d.revision||'',token:d.token||'',
         venue:d.venue||'',side:d.side||'',source:d.source||'',stage:d.stage||'',
         exchange_order_id:d.orderId||'',planned_units:d.units||'0',planned_usdt:d.amount||'0',
         executed_units:'',executed_usdt:'',fee_units:0,fee_quote:0,note:'',evidence:''};
}
function init(doc){
 const page=doc.getElementById('orders-inbox');if(!page)return;
 const ids=['orders-venue','orders-tier','orders-side','orders-token','orders-level','orders-status'];
 const controls=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
 const rows=[...page.querySelectorAll('#orders-list tbody tr[data-token]')];
 function filter(){
  let shown=0;
  for(const row of rows){
   row.hidden=!visible(row,controls['orders-venue']?.value||'Todos',controls['orders-tier']?.value||'Todos',controls['orders-side']?.value||'Todos',controls['orders-token']?.value||'Todos',controls['orders-level']?.value||'Todos',controls['orders-status']?.value||'Todos');
   if(!row.hidden)shown++;
  }
  const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=shown!==0;
  const count=doc.getElementById('orders-filter-count');if(count)count.textContent=shown+' de '+rows.length+' órdenes visibles · propuestas no colocadas automáticamente';
 }
 for(const id of ids)controls[id]?.addEventListener('change',filter);
 doc.getElementById('orders-clear-filters')?.addEventListener('click',()=>{
  for(const id of ids)if(controls[id])controls[id].value='Todos';
  filter();
 });
 filter();
 const dialog=doc.getElementById('orders-management-dialog');
 const form=doc.getElementById('orders-management-form');
 if(!dialog||!form)return;
 const feedback=doc.getElementById('orders-management-feedback');
 const fields={exchange_order_id:'order-exchange-id',planned_units:'order-planned-units',planned_usdt:'order-planned-usdt',
   executed_units:'order-executed-units',executed_usdt:'order-executed-usdt',fee_units:'order-fee-units',fee_quote:'order-fee-quote',
   evidence:'order-evidence',note:'order-note'};
 let current=null;
 function setVisible(action){
  const shown=action==='PROPUESTA'?['planned_units','planned_usdt','note']:
   (action==='CONFIRMADA'||action==='CONFIRMAR_RECOMENDACION')?['exchange_order_id','planned_units','planned_usdt','evidence','note']:
   ['exchange_order_id','executed_units','executed_usdt','fee_units','fee_quote','evidence','note'];
  for(const [key,id] of Object.entries(fields)){
   const el=doc.getElementById(id); const section=el?.closest('label');
   if(section)section.hidden=!shown.includes(key);
   if(el)el.required=shown.includes(key)&&['exchange_order_id','evidence','executed_units','executed_usdt'].includes(key)
     &&!(key==='exchange_order_id'&&current.exchange_order_id);
  }
  // Only positive planned amounts when confirming; provisional proposals may be unsized.
  for(const key of ['planned_units','planned_usdt']){
   const el=doc.getElementById(fields[key]);if(el)el.required=['CONFIRMADA','CONFIRMAR_RECOMENDACION'].includes(action);
  }
 }
 for(const btn of page.querySelectorAll('[data-manage]'))btn.addEventListener('click',()=>{
  if(page.dataset.managementReady==='false'){
   feedback.textContent='No disponible: el historial no pudo leerse. Reintenta más tarde.';return;
  }
  current=initialFields(btn);
  form.reset();
  for(const [key,id] of Object.entries(fields)){
   const el=doc.getElementById(id);if(el&&current[key]!==undefined)el.value=current[key];
  }
  doc.getElementById('order-management-title').textContent=({PROPUESTA:'Registrar propuesta',CONFIRMADA:'Confirmar orden colocada',CONFIRMAR_RECOMENDACION:'Confirmar recomendación colocada',
      PARCIAL:'Registrar ejecución parcial',EJECUTADA:'Registrar orden ejecutada'})[current.action]||current.action;
  doc.getElementById('order-management-details').textContent=[current.token,current.venue,current.side,current.stage,current.moneda_cotizada||btn.dataset.currency||''].filter(Boolean).join(' · ');
  setVisible(current.action);
  dialog.showModal();
 });
 doc.getElementById('order-cancel')?.addEventListener('click',()=>dialog.close());
 form.addEventListener('submit',async ev=>{
  ev.preventDefault();if(!current)return;
  const payload={...current,expected_snapshot_id:page.dataset.snapshotId};
  for(const [key,id] of Object.entries(fields))payload[key]=doc.getElementById(id)?.value||'';
  if(current.action==='PROPUESTA'){delete payload.exchange_order_id;delete payload.evidence;}
  // Explicit local confirmation before writing financial evidence into the MASTER.
  if(!root.confirm('Registrar estado '+current.action+' en el MASTER? No ejecuta órdenes ni altera saldos.'))return;
  const submit=doc.getElementById('order-submit');submit.disabled=true;
  try{
   const auth=await fetch('/api/admin/session',{credentials:'same-origin'}).then(r=>r.json());
   if(!auth.is_admin||!auth.csrf_token)throw new Error('Requiere clave administrativa adicional. Abre Configuración, autentícate y regresa a Órdenes.');
   const resp=await fetch('/api/orders/manage',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Kairos-Csrf':auth.csrf_token},body:JSON.stringify(payload)});
   const result=await resp.json();
   if(!resp.ok||result.status!=='OK')throw new Error((result.error_code?result.error_code+': ':'')+(result.reason||'No se pudo registrar'));
   feedback.textContent='Registro guardado. Recargando historial…';dialog.close();
   root.location.reload();
  }catch(err){
   feedback.textContent=String(err.message||err);dialog.close();
  }finally{submit.disabled=false;}
 });
}
if(typeof module!=='undefined'&&module.exports)module.exports={visible,initialFields,init};
if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));
})(typeof window!=='undefined'?window:globalThis);
