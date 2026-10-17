/* KairosWeb v1.8.0 display-only banking privacy. Values never sent to a server.
   This prevents on-screen exposure, NOT API/DOM/network access or screenshots taken before loading. */
(() => {
  'use strict';
  const root=document.documentElement;
  const button=document.getElementById('privacy-toggle');
  let visible=false;
  try{visible=sessionStorage.getItem('kairos-privacy-visible')==='yes';}catch(_e){}
  const originalText=new WeakMap();
  const originalTitle=new WeakMap();
  const passwordTypes=new WeakMap();
  const moneyRe=/(?:US\s?\$|\$)\s*-?(?:<)?\s*\d[\d,.]*/g;
  const btcRe=/\b\d[\d,.]*\s*(?:BTC|USDT)(?=\b)/g;
  const unitRe=/\b\d[\d,.]*\s*u\.(?=\s|$)/g;
  const excluded='script,style,noscript,textarea,select,option,code,pre,[data-public-price],.privacy-icon';
  const amountInput='input[data-field="hodl"],input[data-field="core"],input[data-field="exchange"],input[data-field="investment_total"],input[data-field="usdt"]';
  function withinSensitive(el){
    if(el.closest('[data-private], [data-sensitive]'))return true;
    const cell=el.closest('td');if(!cell)return false;
    const table=cell.closest('table');if(!table || !table.tHead)return false;
    const header=table.tHead.rows[0]?.cells[cell.cellIndex];
    return !!header && /^(?:HODL(?:\s|$)|Core(?:\s|$)|Exchange(?:\s|$)|Total unidades|Unidades(?:\s|$)|Unidades SELL|Valor BTC|Costo medio|Precio medio|Inversi[oó]n)/i.test(header.textContent.trim());
  }
  function isExcluded(el){return !!el.closest(excluded);}
  function redact(s,whole){return whole?'*****':String(s).replace(moneyRe,'*****').replace(btcRe,'*****').replace(unitRe,'*****');}
  function processText(node){
    const owner=node.parentElement;
    if(!owner || isExcluded(owner))return;
    const old=originalText.get(node);
    if(!visible){
      const source=old&&node.nodeValue===old.mask?old.source:node.nodeValue;
      const next=redact(source,withinSensitive(owner));
      if(next!==source){originalText.set(node,{source,mask:next});if(node.nodeValue!==next)node.nodeValue=next;}
    }else if(old){
      if(node.nodeValue===old.mask)node.nodeValue=old.source;
      originalText.delete(node);
    }
  }
  function processTitle(el){
    if(!el.hasAttribute('title')||isExcluded(el))return;
    const old=originalTitle.get(el);
    if(!visible){
      const current=el.getAttribute('title');
      const source=old&&current===old.mask?old.source:current;
      const next=redact(source,withinSensitive(el));
      if(next!==source){originalTitle.set(el,{source,mask:next});if(current!==next)el.setAttribute('title',next);}
    }else if(old){
      if(el.getAttribute('title')===old.mask)el.setAttribute('title',old.source);
      originalTitle.delete(el);
    }
  }
  function processInput(el){
    if(!el.matches(amountInput))return;
    if(!visible){if(!passwordTypes.has(el))passwordTypes.set(el,el.type);if(el.type!=='password')el.type='password';}
    else if(passwordTypes.has(el)){el.type=passwordTypes.get(el);passwordTypes.delete(el);}
  }
  function visit(container){
    if(container.nodeType===Node.TEXT_NODE){processText(container);return;}
    if(container.nodeType!==Node.ELEMENT_NODE && container.nodeType!==Node.DOCUMENT_NODE)return;
    if(container.nodeType===Node.ELEMENT_NODE){if(isExcluded(container))return;processTitle(container);if(container.matches('input'))processInput(container);}
    const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    while(walker.nextNode()){
      const child=walker.currentNode;
      if(child.nodeType===Node.TEXT_NODE)processText(child);
      else {processTitle(child);if(child.matches('input'))processInput(child);}
    }
  }
  let queued=false;
  function schedule(){if(queued)return;queued=true;queueMicrotask(()=>{queued=false;observer.disconnect();visit(document.body);observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title']});});}
  const observer=new MutationObserver(schedule);
  function setVisible(next){visible=!!next;root.dataset.balances=visible?'visible':'hidden';button?.setAttribute('aria-pressed',String(visible));button?.setAttribute('aria-label',visible?'Ocultar saldos':'Mostrar saldos');button?.setAttribute('title',visible?'Ocultar saldos':'Mostrar saldos');if(button){const s=button.querySelector('.privacy-label');if(s)s.textContent=visible?'Ocultar':'Mostrar';}
    try{sessionStorage.setItem('kairos-privacy-visible',visible?'yes':'no');}catch(_e){}
    schedule();
  }
  button?.addEventListener('click',()=>setVisible(!visible));
  root.dataset.balances=visible?'visible':'hidden';
  setVisible(visible);
  // Shield from first paint until the first sweep completes.
  queueMicrotask(()=>{root.dataset.privacyReady='yes';root.dataset.privacyBoot='ready';});
  window.KairosPrivacy={isVisible:()=>visible};
})();
