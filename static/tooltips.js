/* Desktop-only button/menu tooltips. On mobile (coarse pointer or narrow
   viewport), never show tap bubbles or native title tooltips on controls.
   Keep aria-label and visible text for accessibility; leave desktop intact. */
(() => {
 'use strict';
 const descriptions={
  'bell-open':'Abrir Alertas Kairos 1H, 4H y 1D sin leer.',
  'alerts-read-all':'Marcar como leídas las alertas visibles; conservar historial.',
  'alerts-refresh':'Volver a leer las alertas de Google Sheets.',
  'settings-save':'Validar, guardar y sincronizar los cambios autorizados del Master.',
  'settings-preliminary':'Actualizar candidatos PROPUESTO desde MCP; no publica.',
  'settings-tab':'Abrir la sección de configuración correspondiente.',
  'settings-snapshot':'Identificador del último snapshot publicado del Master.'
 };
 const mobilePointer=window.matchMedia?.('(hover: none) and (pointer: coarse)');
 const narrowScreen=window.matchMedia?.('(max-width: 680px)');
 const isMobile=()=>Boolean(mobilePointer?.matches||narrowScreen?.matches);
 const interactive='button,a,[role="button"],.settings-tab,[data-theme-toggle]';
 const described='button,a,[role="button"],th,.bar-row,.tier-track,.settings-field input,.settings-field select';
 const previousTitles=new WeakMap();
 const clean=x=>String(x||'').replace(/\s+/g,' ').trim().slice(0,220);
 function info(node){
   if(node.hasAttribute('title')&&node.getAttribute('title'))return '';
   if(node.dataset.tooltip)return clean(node.dataset.tooltip);
   if(node.id&&descriptions[node.id])return descriptions[node.id];
   if(node.matches('.global-nav-link'))return 'Abrir modo '+clean(node.textContent);
   if(node.matches('th'))return 'Columna: '+clean(node.textContent)+'; puedes ordenar si aparece una flecha.';
   if(node.matches('.bar-row')){
     const label=clean(node.querySelector('.bar-label')?.textContent),value=clean(node.querySelector('.bar-value')?.textContent);
     return label+(value?' · '+value:'')+' · consulta la fuente y fecha del reporte';
   }
   if(node.matches('button,a,[role="button"]'))return clean(node.getAttribute('aria-label')||node.textContent);
   return '';
 }
 const tip=document.createElement('div');tip.className='kairos-tap-tooltip';tip.hidden=true;
 function hide(){tip.hidden=true;}
 function describe(){
   const mobile=isMobile();
   if(mobile)hide();
   document.querySelectorAll(described).forEach(node=>{
     if(mobile){
       if(node.matches(interactive)&&node.hasAttribute('title')){
         previousTitles.set(node,node.getAttribute('title'));
         node.removeAttribute('title');
       }
       return;
     }
     if(node.matches(interactive)&&!node.hasAttribute('title')&&previousTitles.has(node)){
       node.setAttribute('title',previousTitles.get(node));
       previousTitles.delete(node);
     }
     const message=info(node);if(message)node.setAttribute('title',message);
   });
   if(mobile)return;
   document.querySelectorAll('svg circle[aria-label]').forEach(circle=>{
     if(!circle.querySelector('title')){
       const title=document.createElementNS('http://www.w3.org/2000/svg','title');
       title.textContent=circle.getAttribute('aria-label');circle.append(title);
     }
   });
 }
 function start(){
   (document.body||document.documentElement).appendChild(tip);
   describe();
   let queued=false;
   const schedule=()=>{
     if(queued)return;queued=true;
     requestAnimationFrame(()=>{queued=false;describe();});
   };
   // Other UI modules dynamically create buttons and set title attributes.
   // Re-strip those titles on mobile without interfering with desktop hints.
   const observer=new MutationObserver(schedule);
   observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['title']});
   mobilePointer?.addEventListener?.('change',schedule);
   narrowScreen?.addEventListener?.('change',schedule);
   document.addEventListener('pointerdown',event=>{
     if(isMobile()){hide();return;}
     if(event.pointerType!=='touch')return;
     const node=event.target.closest('button,a,[role="button"],.bar-row,th,[data-tooltip]');
     if(!node){hide();return;}
     const label=node.getAttribute('title')||info(node);if(!label)return;
     tip.textContent=label;tip.hidden=false;
     const rect=node.getBoundingClientRect();
     tip.style.left=Math.max(10,Math.min(innerWidth-270,rect.left))+'px';
     tip.style.top=Math.max(12,rect.top-50)+'px';
   },{passive:true});
   document.addEventListener('keydown',event=>{if(event.key==='Escape')hide();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();
