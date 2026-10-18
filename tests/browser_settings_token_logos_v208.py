"""Offline Chromium smoke test: Settings token logos are present in all token sections."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
TOKENS=['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE']
STATE={
 'status':'OK','is_admin':False,'write_configured':False,'csrf_token':'TEST',
 'snapshot_id':'TEST-SNAPSHOT','fecha_corte':'2026-10-18',
 'sections':{
  'units':[{'token':t,'hodl':0,'core':0,'exchange':10,'investment_total':100} for t in TOKENS],
  'targets':[{'token':t,'tier':'T1','target':.1} for t in TOKENS],
  'pivots':[{'token':t,'cycle_low':1,'cl_date':'2026-01-01','cl_status':'PROPUESTO',
             **{f'o{i}':None for i in range(1,6)},
             **{f'o{i}_date':None for i in range(1,6)},
             **{f'o{i}_status':'PROPUESTO' for i in range(1,6)}} for t in TOKENS],
  'liquidity':[], 'parameters':[], 'tier_custody':[],
 }
}
PAGE='''<div id="settings-nav"><button data-tab="units">Unidades</button><button data-tab="targets">Targets</button><button data-tab="pivots">Pivotes</button></div>
<h2 id="settings-title"></h2><div id="settings-desc"></div><div id="settings-snapshot"></div>
<div id="settings-admin-state"></div><div id="settings-pivots-tools" hidden><button id="settings-preliminary"></button><div id="settings-cl-review-progress"></div><div id="settings-preliminary-progress"></div></div>
<section id="settings-mcp-panel" hidden></section><div class="settings-form"><input id="settings-evidence"></div>
<div id="settings-data"></div><div id="settings-pivot-matrix" hidden></div><div id="settings-totals"></div>
<div><button id="settings-save">Guardar cambios</button></div><div id="settings-msg"></div>
<script>window.KairosFormatting={labels:{},scale:()=>'',toDisplay:v=>v};
window.fetch=async()=>({ok:true,status:200,json:async()=>window.__state});</script>'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page()
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('https://cryptologos.cc/**',lambda route:route.fulfill(status=404,body=''))
 page.set_content(PAGE+'<script>window.__state='+json.dumps(STATE)+'</script>'+ 
                  '<script>'+(ROOT/'static/settings_master.js').read_text()+'</script>')
 for tab,select in [('units','#settings-data .settings-token-identity'),('targets','#settings-data .settings-token-identity'),('pivots','.pivot-wave-table .settings-token-identity')]:
  page.locator(f'[data-tab="{tab}"]').click()
  page.wait_for_selector(select)
  assert page.locator(select).count()==12,(tab,page.locator(select).count())
  assert page.locator(select+' .settings-coin-icon').count()==12
  assert page.locator(select+' strong.token-name').all_text_contents()==TOKENS
  assert page.locator(select+' .coin-fallback').count()==12
 assert not errors,errors
 print('PASS Chromium: logos para 12 tokens en Unidades, Objetivos y Pivotes (fallback sin red)')
 browser.close()
