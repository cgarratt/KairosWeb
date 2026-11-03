/* BTC daily/weekly display only. No API calls or financial writes. */
(()=>{'use strict';const root=document.getElementById('balancer-daily');if(!root)return;
const ns='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const node=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,v));parent.appendChild(node);return node;}
function draw(svg){const width=Math.max(110,svg.clientWidth),cx=width/2,r=cx-14,cy=r+15;svg.setAttribute('viewBox',`0 0 ${width} ${cy+24}`);svg.replaceChildren();const point=(v,len)=>{const a=Math.PI*(1-v/100);return[cx+len*Math.cos(a),cy-len*Math.sin(a)];};
const valid=svg.dataset.first!==''&&svg.dataset.second!==''&&[+svg.dataset.first,+svg.dataset.second].every(x=>Number.isFinite(x)&&x>=0&&x<=100);
const arc=(a,b,color)=>{const p=point(a,r),q=point(b,r);el('path',{d:`M ${p[0]} ${p[1]} A ${r} ${r} 0 0 1 ${q[0]} ${q[1]}`,fill:'none',stroke:color,'stroke-width':8},svg);};
const low=+svg.dataset.low,high=+svg.dataset.high;
if(valid){arc(0,low,'var(--green)');arc(low,high,'var(--line)');arc(high,100,'var(--red)');}else arc(0,100,'var(--line)');
for(const v of[0,low,high,100]){const p=point(v,r-10),q=point(v,r-15);el('line',{x1:p[0],y1:p[1],x2:q[0],y2:q[1],stroke:'var(--muted)','stroke-width':1},svg);}
for(const[v,x]of[[0,cx-r],[100,cx+r]])el('text',{x,y:cy+17,'text-anchor':'middle'},svg).textContent=v;
if(!valid){el('text',{x:cx,y:cy-14,'text-anchor':'middle'},svg).textContent='N/D';return;}
for(const[v,len,color,dash]of[[+svg.dataset.second,r-22,'var(--bd-gold)','4 3'],[+svg.dataset.first,r-6,'var(--bd-blue)','none']]){const p=point(v,len);el('line',{x1:cx,y1:cy,x2:p[0],y2:p[1],stroke:color,'stroke-width':3,'stroke-dasharray':dash,'stroke-linecap':'round'},svg);}
el('circle',{cx,cy,r:5,fill:'var(--panel)',stroke:'var(--bd-blue)','stroke-width':2},svg);}
const redraw=()=>root.querySelectorAll('.bd-dial').forEach(draw);redraw();if(typeof ResizeObserver!=='undefined')new ResizeObserver(redraw).observe(root);
})();
