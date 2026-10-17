/* Accessible, nonintrusive descriptions for buttons, menu, tables and live charts.
   Native title supports mouse and keyboard. Tap produces a brief on-screen hint.
   Never manufactures market values: only uses rendered text or authored metadata. */
(() => {
 'use strict';
 const descriptions={
  'bell-open':'Abrir Alertas Kairos accionables sin leer.',
  'alerts-read-all':'Marcar como leídas las alertas accionables visibles; conservar el historial.',
  'alerts-refresh':'Volver a leer las alertas de Google Sheets.',
  'settings-save':'Validar, guardar y sincronizar los cambios autorizados del Master.',
  'settings-preliminary':'Actualizar candidatos no certificados desde Binance o Hyperliquid MCP.',
  'settings-tab':'Abrir la sección de configuración correspondiente.',
  'settings-snapshot':'Identificador del último snapshot publicado del Master.'
 };
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
 function describe(){
   document.querySelectorAll('button,a,[role="button"],th,.bar-row,.tier-track,.settings-field input,.settings-field select').forEach(node=>{
      const message=info(node);if(message)node.setAttribute('title',message);
   });
   document.querySelectorAll('svg circle[aria-label]').forEach(circle=>{
      if(!circle.querySelector('title')){
        const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=circle.getAttribute('aria-label');circle.append(title);
      }
   });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',describe);else describe();
 let task=false;const observer=new MutationObserver(()=>{
   if(task)return;task=true;requestAnimationFrame(()=>{task=false;describe();});
 });
 observer.observe(document.documentElement,{childList:true,subtree:true});
 const tip=document.createElement('div');tip.className='kairos-tap-tooltip';tip.hidden=true;
 (document.body||document.documentElement).appendChild(tip);
 function hide(){tip.hidden=true;}
 document.addEventListener('pointerdown',event=>{
   if(event.pointerType!=='touch')return;
   const node=event.target.closest('button,a,[role="button"],.bar-row,th,[data-tooltip]');
   if(!node){hide();return;}
   const label=node.getAttribute('title')||info(node);if(!label)return;
   tip.textContent=label;tip.hidden=false;
   const rect=node.getBoundingClientRect();
   tip.style.left=Math.max(10,Math.min(innerWidth-270,rect.left))+'px';
   tip.style.top=Math.max(12,rect.top-50)+'px';
 },{passive:true});
 document.addEventListener('keydown',event=>{if(event.key==='Escape')hide()});
})();
