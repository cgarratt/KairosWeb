(()=>{'use strict';
  const collator=new Intl.Collator('es',{numeric:true,sensitivity:'base'});
  function value(cell){
    if(!cell)return {type:'empty',value:null};
    const raw=(cell.textContent||'').replace(/\u00a0/g,' ').trim();
    if(!raw||/^(?:—|–|-|N\/D|Pendiente)$/i.test(raw))return {type:'empty',value:null};
    let s=raw.replace(/(?:USDT|USD|BTC|\$|%|pp|unidades|ud\.)/gi,'').trim();
    // Only parse strictly numeric strings, with a small optional unit suffix.
    s=s.replace(/^\+/, '').replace(/\s/g,'');
    if (/^[−-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$/.test(s))s=s.replace(/,/g,'');
    else if (/^[−-]?\d+(?:\.\d+)?$/.test(s)){}
    else return {type:'text',value:raw};
    const n=Number(s.replace('−','-'));
    return Number.isFinite(n)?{type:'number',value:n}:{type:'text',value:raw};
  }
  function normalizeGroup(table,body){
    const rows=Array.from(body.rows), groups=[];
    if(body.id==='waves-body'){
      for(let i=0;i<rows.length;i+=2) groups.push(rows.slice(i,i+2));
    }else{
      rows.forEach(r=>groups.push([r]));
    }
    const fixed=[],sortable=[];
    for(const group of groups){
      const label=(group[0]?.cells[0]?.textContent||'').trim();
      if(/^(?:total(?:es)?(?:\s+usdt|\s+patrimonio|\s+ventas)?|resumen|subtotal|liquidez\s+usdt|cripto\s+total|patrimonio\s+total)$/i.test(label))fixed.push(group);
      else sortable.push(group);
    }
    return {fixed,sortable};
  }
  function sortTable(table,col,dir){
    const tbody=table.tBodies[0];if(!tbody)return;
    const {fixed,sortable}=normalizeGroup(table,tbody);
    const indexed=sortable.map((group,index)=>({group,index,key:value(group[0].cells[col])}));
    indexed.sort((a,b)=>{
      if(a.key.type==='empty'&&b.key.type!=='empty')return 1;
      if(b.key.type==='empty'&&a.key.type!=='empty')return -1;
      let cmp=0;
      if(a.key.type==='number'&&b.key.type==='number')cmp=a.key.value-b.key.value;
      else cmp=collator.compare(String(a.key.value??''),String(b.key.value??''));
      return cmp?cmp*dir:a.index-b.index;
    });
    const fragment=document.createDocumentFragment();
    [...indexed.map(x=>x.group),...fixed].forEach(g=>g.forEach(r=>fragment.appendChild(r)));
    tbody.appendChild(fragment); // tfoot never touched
    table.dataset.sortIndex=String(col);table.dataset.sortDirection=String(dir);
    table.querySelectorAll('thead th[data-sort-index]').forEach(th=>{
      const active=Number(th.dataset.sortIndex)===col;
      th.setAttribute('aria-sort',active?(dir===1?'ascending':'descending'):'none');
      const indicator=th.querySelector('.sort-arrow');if(indicator)indicator.textContent=active?(dir===1?'▲':'▼'):'↕';
    });
  }
  function init(table){
    if(table.dataset.sortReady==='1')return;
    const head=table.tHead,body=table.tBodies[0];
    if(!head||!body)return;
    // For tables with grouped headers, use a single unambiguous column row only.
    if(head.rows.length!==1)return;
    const ths=Array.from(head.rows[0].cells);
    if(ths.length<2||ths.some(th=>th.colSpan!==1||th.rowSpan>1))return;
    table.dataset.sortReady='1';
    ths.forEach((th,index)=>{
      if(!th.textContent.trim())return;
      th.dataset.sortIndex=String(index);
      th.setAttribute('aria-sort','none');
      const btn=document.createElement('button');btn.type='button';btn.className='table-sort-button';
      btn.setAttribute('aria-label','Ordenar por '+th.textContent.trim());
      const caption=document.createElement('span');caption.textContent=th.textContent.trim();
      const arrow=document.createElement('span');arrow.className='sort-arrow';arrow.setAttribute('aria-hidden','true');arrow.textContent='↕';
      btn.append(caption,arrow);th.replaceChildren(btn);
      btn.addEventListener('click',()=>{
        const same=Number(table.dataset.sortIndex)===index;
        const nextDir=same?-Number(table.dataset.sortDirection||'-1'):1;
        sortTable(table,index,nextDir);
      });
    });
  }
  function scan(){document.querySelectorAll('table').forEach(init);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
  // Covers dynamic tables that are inserted after MCP reads.
  const watcher=new MutationObserver(records=>{
    if(records.some(r=>Array.from(r.addedNodes).some(n=>n.nodeType===1&&(n.matches?.('table')||n.querySelector?.('table')))))scan();
  });
  watcher.observe(document.documentElement,{childList:true,subtree:true});
})();