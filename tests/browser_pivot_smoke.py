"""Offline Chromium browser smoke test. No Google Sheets writes or real MCP calls."""
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
page_html='''<!doctype html><html lang="es" data-theme="dark"><body>
<div id="settings-nav"><button data-tab="units">Unidades</button><button data-tab="pivots">Pivotes</button></div>
<div id="settings-title"></div><div id="settings-desc"></div><div id="settings-snapshot"></div>
<div id="settings-admin-state"></div><div id="settings-pivots-tools" hidden><button id="settings-preliminary">Actualizar MCP</button><span id="settings-preliminary-progress"></span></div>
<section id="settings-mcp-panel" hidden></section><div id="settings-data"></div><div id="settings-totals"></div>
<div class="settings-form"><input id="settings-evidence"></div><div><button id="settings-save">Guardar cambios</button></div><div id="settings-msg"></div>
</body></html>'''
mock_js='''
window._calls=[];
window.fetch=async (url,options={})=>{
  window._calls.push(url);
  const archive=[{token:'BTC',cycle_high:126199.63,cycle_low:57800.19,o1:null,o2:null,o3:null,o4:null,o5:null,status:'CANDIDATO_ARCHIVADO_NO_CERTIFICADO',source:'HISTORICO_MCP_EN_GOOGLE_SHEETS',warning:'No certificado'},
    {token:'HYPE',cycle_high:59.406,cycle_low:20.5,o1:76.9,o2:51.11,o3:97.885,status:'CANDIDATO_ARCHIVADO_NO_CERTIFICADO',source:'HISTORICO_MCP_EN_GOOGLE_SHEETS',warning:'O3 sin 5R'}];
  const record={token:'BTC',cycle_high:126199.63,cycle_low:57800.19,o1:87402.35,status:'CANDIDATO_MCP_NO_CERTIFICADO',record_origin:'LIVE_MCP',source:'Binance Spot MCP',warning:'No certificado'};
  const state={status:'OK',snapshot_id:'KAIROS-2026-10-17-001',fecha_corte:'2026-10-17',is_admin:false,write_configured:true,
    sections:{units:[],targets:[],tier_custody:[],liquidity:[],parameters:[],pivots:[{token:'BTC',cycle_low:null,o1:null,o2:null,o3:null,o4:null,o5:null,c1_reference:72575.57,c2_reference:69076.45,status:'REFERENCIA_HISTORICA'},
      {token:'HYPE',cycle_low:null,o1:null,o2:null,o3:null,o4:null,o5:null,c1_reference:59.2425,c2_reference:50.1005,status:'REFERENCIA_HISTORICA'}]}};
  const data=url==='/api/settings/data'?state:url==='/api/settings/pivots/preliminary'?{status:'OK',records:archive}:
    url.includes('token=BTC')?{status:'OK',records:[record]}:{status:'PARTIAL',records:[{token:'HYPE',status:'DATA_ERROR',warning:'MCP no disponible'}]};
  return {ok:true,status:200,json:async()=>data};
};'''
with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=b.new_page()
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(page_html)
  page.add_script_tag(content=mock_js)
  page.add_script_tag(path=str(root/'static/settings_format.js'))
  page.add_script_tag(path=str(root/'static/settings_master.js'))
  page.wait_for_function("document.querySelector('#settings-title').textContent==='Maestro de unidades'")
  page.locator('[data-tab=pivots]').click()
  page.wait_for_function("document.querySelector('[data-index=\"0\"][data-field=\"cycle_low\"]').value==='57800.19'")
  assert page.locator('[data-index="1"][data-field="o3"]').input_value()=='97.885'
  assert 'No certificado' in page.locator('[data-pivot-info="BTC"]').inner_text()
  page.locator('#settings-preliminary').click()
  page.wait_for_function("document.querySelector('#settings-preliminary-progress').textContent.includes('2/2 consultados')")
  assert page.locator('[data-index="0"][data-field="o1"]').input_value()=='87402.35'
  assert page.locator('[data-index="1"][data-field="o3"]').input_value()=='97.885'
  assert page.locator('[data-pivot-info="HYPE"]').inner_text().find('Actualización MCP falló')!=-1
  assert not errors,errors
  print('PASS: pivots archived initial fill; live per-token refresh; partial failure preserved; no saves')
  b.close()
