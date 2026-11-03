/* BTC daily/weekly display only. No API calls or financial writes. */
(()=>{'use strict';const root=document.getElementById('balancer-daily');if(!root)return;
const ns='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const node=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,v));parent.appendChild(node);return node;}
function draw(svg){const width=Math.max(64,svg.clientWidth),cx=width/2,r=cx-6,cy=r+6;svg.setAttribute('viewBox',`0 0 ${width} ${cy+24}`);svg.replaceChildren();const point=(v,len)=>{const a=Math.PI*(1-v/100);return[cx+len*Math.cos(a),cy-len*Math.sin(a)];};
const valid=svg.dataset.first!==''&&svg.dataset.second!==''&&[+svg.dataset.first,+svg.dataset.second].every(x=>Number.isFinite(x)&&x>=0&&x<=100);
const arc=(a,b,color)=>{const p=point(a,r),q=point(b,r);el('path',{d:`M ${p[0]} ${p[1]} A ${r} ${r} 0 0 1 ${q[0]} ${q[1]}`,fill:'none',stroke:color,'stroke-width':6},svg);};
const low=+svg.dataset.low,high=+svg.dataset.high;
if(valid&&svg.dataset.kind==='adx'){arc(0,23,'var(--line)');arc(23,100,'var(--green)');}else if(valid){arc(0,low,'var(--green)');arc(low,high,'var(--line)');arc(high,100,'var(--red)');}else arc(0,100,'var(--line)');
for(const v of[0,low,high,100]){const p=point(v,r-10),q=point(v,r-15);el('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'var(--muted)','stroke-width':1},svg);}

if(!valid){el('text',{x:cx,y:cy-14,'text-anchor':'middle'},svg).textContent='N/D';return;}
for(const[v,len,color,dash]of[[+svg.dataset.second,r-8,'var(--bd-gold)','4 3'],[+svg.dataset.first,r-2,'var(--bd-blue)','none']]){const p=point(v,len);el('line',{x1:cx,y1:cy,x2:p[0],y2:p[1],stroke:color,'stroke-width':3,'stroke-dasharray':dash,'stroke-linecap':'round'},svg);}
el('circle',{cx,cy,r:5,fill:'var(--panel)',stroke:'var(--bd-blue)','stroke-width':2},svg);}
const button=root.querySelector('#btc-sth-refresh'),status=root.querySelector('#btc-sth-status');
if(button&&status)button.addEventListener('click',async()=>{
 button.disabled=true;status.textContent='Consultando Glassnode…';
 try{
  const response=await fetch('/api/btc-references/refresh',{method:'POST',credentials:'same-origin',headers:{'X-Kairos-Csrf':button.dataset.csrf,'Content-Type':'application/json'},body:'{}'});
  const data=await response.json();
  if(response.ok&&data.status==='OK'){window.location.reload();return;}
  status.textContent=data.reason||'STH o conversión no disponibles. Revisar valores y fuentes; se conservará N/D donde corresponda.';
  if(response.ok&&data.status==='PARTIAL'){window.location.reload();return;}
 }catch(_){status.textContent='No se pudo consultar Glassnode. Puedes reintentar manualmente.';}
 finally{button.disabled=false;}
});
const redraw=()=>root.querySelectorAll('.bd-dial').forEach(draw);redraw();if(typeof ResizeObserver!=='undefined')new ResizeObserver(redraw).observe(root);
})();
