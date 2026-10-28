/* Strict UTC-date chronology. Readability is retained for inherited invalid rows. */
(function(root){'use strict';
function issues(p){const names=['cl','o1','o2','o3','o4','o5'];
 const rows={cl:{date:p.cl_date,price:p.cycle_low},...(p.waves||{})};let prior=null;const errors=[];
 for(let i=0;i<names.length;i++){const name=names[i],r=rows[name]||{},d=r.date;if(!d)continue;
  const parsed=new Date(d+'T00:00:00Z');
  if(!/^\d{4}-\d{2}-\d{2}$/.test(d)||!Number.isFinite(+parsed)||parsed.toISOString().slice(0,10)!==d){errors.push(name.toUpperCase()+': fecha UTC inválida');continue;}
  if(r.price==null||r.price==='')errors.push(name.toUpperCase()+': fecha sin precio');
  if(i&&!rows[names[i-1]]?.date)errors.push(name.toUpperCase()+': falta fecha de '+names[i-1].toUpperCase()+' anterior');
  if(prior&&d<=prior.date)errors.push(name.toUpperCase()+' ('+d+') debe ser posterior a '+prior.name.toUpperCase()+' ('+prior.date+')');
  prior={name,date:d};
 }return errors;
}
const api={issues};root.KairosPivotTimeline=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
