(() => {
  'use strict';
  const storageKey='kairosweb-theme';
  function getTheme(){try{return localStorage.getItem(storageKey)==='dark'?'dark':'light';}catch(e){return 'light';}}
  function setTheme(value){const dark=value==='dark';document.documentElement.dataset.theme=dark?'dark':'light';
    try{localStorage.setItem(storageKey,dark?'dark':'light');}catch(e){}
    document.querySelectorAll('[data-theme-toggle]').forEach(b=>{b.setAttribute('aria-label',dark?'Activar tema claro':'Activar tema oscuro');b.title=dark?'Activar tema claro':'Activar tema oscuro';b.setAttribute('aria-pressed',String(dark));});
    document.querySelectorAll('input[name="theme-choice"]').forEach(r=>{r.checked=r.value===(dark?'dark':'light');});
  }
  setTheme(getTheme());
  document.addEventListener('click',e=>{if(e.target.closest('[data-theme-toggle]'))setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');});
  document.addEventListener('change',e=>{if(e.target.matches('input[name="theme-choice"]'))setTheme(e.target.value);});
})();
