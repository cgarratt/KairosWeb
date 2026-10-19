/* Kairos Orders phase 1: client-only quick views. Never submit exchange orders. */
(function(root){
'use strict';
function matchesGroup(row,group){
 if(group==='Todos')return true;
 if(group==='O2')return /^O2C[1-4]$/.test(row.dataset.stage||'');
 if(group==='O3')return /^O3V[1-4]$/.test(row.dataset.stage||'');
 if(group==='O5')return /^O5V[1-4]$/.test(row.dataset.stage||'');
 return group==='EXTENSION_1W' ? row.dataset.wave==='EXTENSION_1W' : row.dataset.stage===group;
}
function matchesDistance(row,status){
 if(status==='Todos')return true;
 if(status==='NIVEL_SUPERADO')return ['NIVEL_SUPERADO','NIVEL_TOCADO'].includes(row.dataset.proximity);
 if(['PRECIO_PENDIENTE','EN_ESPERA'].includes(status))return row.dataset.proximity===status;
 const val=Number(row.dataset.distance);
 if(row.dataset.distance===''||!Number.isFinite(val)||val<0)return false;
 if(status==='0-2')return val<=2;
 if(status==='2-5')return val>2&&val<=5;
 if(status==='5-10')return val>5&&val<=10;
 if(status==='GT10')return val>10;
 return false;
}
function visible(row,venue,side,status,token,category='Todos',quick='Todas',tier='Todos',group='Todos'){
 const rowVenue=row.dataset.ordersVenue||row.closest('table')?.dataset.ordersVenue;
 const rowTier=(row.getAttribute?.('data-orders-tier'))||row.dataset.tier;
 const base=(venue==='Todos'||rowVenue===venue)&&
  (category==='Todos'||row.dataset.category===category||row.dataset.ordersCategory===category)&&
  (side==='Todos'||row.dataset.side===side)&&
  matchesDistance(row,status)&&
  (tier==='Todos'||rowTier===tier)&&
  matchesGroup(row,group)&&
  (!token||(row.dataset.token||'').includes(token));
 if(!base)return false;
 if(quick==='Todas')return true;
 if(quick==='O2')return matchesGroup(row,'O2');
 if(['Binance','KuCoin','Hyperliquid'].includes(quick))return rowVenue===quick;
 if(['T1','T2','T3'].includes(quick))return rowTier===quick;
 if(quick.startsWith('TOKEN:'))return row.dataset.token===quick.slice(6);
 return false;
}
function init(doc){
 const page=doc.getElementById('orders-inbox');if(!page)return;
 const ids=['orders-view','orders-venue','orders-category','orders-group','orders-tier','orders-side','orders-status','orders-token'];
 const controls=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
 const rows=[...page.querySelectorAll('#orders-list tbody tr[data-token]')];
 const get=id=>controls[id]?.value|| (id==='orders-token'?'':id==='orders-view'?'Todas':'Todos');
 function filter(){
  let shown=0;
  for(const row of rows){row.hidden=!visible(row,get('orders-venue'),get('orders-side'),get('orders-status'),get('orders-token').toUpperCase().trim(),get('orders-category'),get('orders-view'),get('orders-tier'),get('orders-group'));if(!row.hidden)shown++;}
  const empty=doc.getElementById('orders-empty-filter');if(empty)empty.hidden=shown!==0;
  const count=doc.getElementById('orders-filter-count');if(count)count.textContent=shown+' de '+rows.length+' propuestas visibles · ninguna colocada';
 }
 for(const id of ids){const el=controls[id];el?.addEventListener(id==='orders-token'?'input':'change',filter)}
 doc.getElementById('orders-clear-filters')?.addEventListener('click',()=>{for(const id of ids){const el=controls[id];if(el)el.value=id==='orders-token'?'':id==='orders-view'?'Todas':'Todos'}filter()});
 filter();
}
if(typeof module!=='undefined'&&module.exports)module.exports={visible,matchesDistance,matchesGroup};
if(root.document)root.document.addEventListener('DOMContentLoaded',()=>init(root.document));
})(typeof window!=='undefined'?window:globalThis);
