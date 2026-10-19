/* Kairos Orders phase 1: display-only filters. No exchange orders or writes. */
(function(root){
'use strict';
function visible(row,venue='Todos',tier='Todos',side='Todos',token='Todos',level='Todos'){
 const rowVenue=row.dataset.ordersVenue||row.closest('table')?.dataset.ordersVenue;
 const rowTier=row.dataset.ordersTier||row.dataset.tier;
 return (venue==='Todos'||rowVenue===venue)&&
        (tier==='Todos'||rowTier===tier)&&
        (side==='Todos'||row.dataset.side===side)&&
        (token==='Todos'||row.dataset.token===token)&&
        (level==='Todos'||row.dataset.stage===level);
}
function init(doc){
 const page=doc.getElementById('orders-inbox');if(!page)return;
 const ids=['orders-venue','orders-tier','orders-side','orders-token','orders-level'];
 const controls=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
 const rows=[...page.querySelectorAll('#orders-list tbody tr[data-token]')];
 function filter(){
  let shown=0;
  for(const row of rows){
   row.hidden=!visible(row,controls['orders-venue']?.value||'Todos',controls['orders-tier']?.value||'Todos',controls['orders-side']?.value||'Todos',controls['orders-token']?.value||'Todos',controls['orders-level']?.value||'Todos');
   if(!row.hidden)shown++;
  }
  const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=shown!==0;
  const count=doc.getElementById('orders-filter-count');if(count)count.textContent=shown+' de '+rows.length+' propuestas visibles · ninguna colocada';
 }
 for(const id of ids)controls[id]?.addEventListener('change',filter);
 doc.getElementById('orders-clear-filters')?.addEventListener('click',()=>{
  for(const id of ids)if(controls[id])controls[id].value='Todos';
  filter();
 });
 filter();
}
if(typeof module!=='undefined'&&module.exports)module.exports={visible,init};
if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));
})(typeof window!=='undefined'?window:globalThis);
