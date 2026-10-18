/* Kairos Orders phase 1: local filters only. No order API, no write calls. */
(function(root){
'use strict';
function visible(row,venue,side,state,token,category='Todos'){
  const table=row.closest('table');
  return (venue==='Todos'||table?.dataset.ordersVenue===venue)&&
    (category==='Todos'||row.dataset.category===category)&&
    (side==='Todos'||row.dataset.side===side)&&
    (state==='Todos'||row.dataset.proximity===state)&&
    (!token||(row.dataset.token||'').includes(token));
}
function init(doc){
 const page=doc.getElementById('orders-inbox');if(!page)return;
 let venue='Todos';
 const state=doc.getElementById('orders-status'),side=doc.getElementById('orders-side');
 const token=doc.getElementById('orders-token'),category=doc.getElementById('orders-category');
 const rows=[...doc.querySelectorAll('table[data-orders-venue] tbody tr')];
 const filter=()=>{
  let count=0;
  for(const row of rows){row.hidden=!visible(row,venue,side.value,state.value,token.value.toUpperCase().trim(),category.value);if(!row.hidden)count++;}
  for(const t of doc.querySelectorAll('table[data-orders-venue]'))t.hidden=![...t.tBodies[0].rows].some(r=>!r.hidden);
  for(const section of doc.querySelectorAll('.orders-section[data-orders-category]'))section.hidden=category.value!=='Todos'&&section.dataset.ordersCategory!==category.value;
  const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=count!==0;
 };
 for(const btn of page.querySelectorAll('button[data-venue]'))btn.addEventListener('click',()=>{
  venue=btn.dataset.venue;
  for(const b of page.querySelectorAll('button[data-venue]')){const active=b===btn;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));}filter();
 });
 for(const el of [side,state,token,category])el?.addEventListener(el===token?'input':'change',filter);
 filter();
}
if(typeof module!=='undefined'&&module.exports)module.exports={visible};
if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));
})(typeof window!=='undefined'?window:globalThis);
