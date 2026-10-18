"""Offline Chromium: CL technical review → preview/publish, without auto-confirmation."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
rows=[{'token':name,'cycle_low':None,'cl_date':None,'status':'SIN_DATO',
       **{key:None for key in ['o1','o2','o3','o4','o5','o1_date','o2_date','o3_date','o4_date','o5_date']},
       **{f'o{i}_status':'ESTIMADO' for i in range(1,6)}} for name in ['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE']]
rows[0].update(cycle_low=70000,o1=100000,o1_date='2026-02-01',o1_status='CONFIRMADO')
state={'status':'OK','is_admin':True,'write_configured':True,'csrf_token':'TEST',
       'snapshot_id':'DEMO','fecha_corte':'2026-10-17','sections':{
       'units':[],'targets':[],'liquidity':[],'tier_custody':[],'parameters':[],'pivots':rows}}
candidates={'status':'OK','records':[{'token':'VIRTUAL','status':'CANDIDATO_ARCHIVADO_NO_CERTIFICADO',
    'cycle_low':.2772,'cl_date':'2025-10-10','o1':1.1984,'o1_date':'2026-01-05','certified':False},
    {'token':'PEPE','status':'CANDIDATO_ARCHIVADO_NO_CERTIFICADO',
    'cycle_low':.00000223,'cl_date':'2025-10-10','o1':.00000536,'o1_date':'2026-01-05','certified':False}]}
markup='''<div id="settings-nav"><button data-tab="units">Unidades</button><button data-tab="pivots">Pivotes O1–O5</button></div>
<h2 id="settings-title"></h2><div id="settings-desc"></div><div id="settings-snapshot"></div>
<div id="settings-admin-state"></div><div id="settings-pivots-tools" hidden><button id="settings-preliminary"></button><div id="settings-preliminary-progress"></div></div>
<section id="settings-mcp-panel" hidden></section><div class="settings-form"><input id="settings-evidence" value="Pivote confirmado manualmente con evidencia técnica"></div>
<div id="settings-data"></div><div id="settings-pivot-matrix" hidden></div><div id="settings-totals"></div>
<div><button id="settings-save">Guardar cambios</button></div><div id="settings-msg"></div>
<script>window.KairosFormatting={labels:{},scale:()=>'',toDisplay:v=>v};
window.__requests=[];
window.confirm=()=>true;
window.fetch=async (url,opts={})=>{
  const u=String(url);if(opts.method==='POST')window.__requests.push({url:u,body:JSON.parse(opts.body)});
  let v=u.startsWith('/api/settings/data')?window.__state:u.includes('/pivots/cl-review')?{status:'VALIDADO_TECNICAMENTE',validated:true,review_proof:'1000.'+'a'.repeat(64),reason:'5L/5R + BOS semanal válido'}:u.includes('/pivots/preliminary')?window.__candidate:
    u.includes('/settings/preview')?{status:'VALIDATED_DRAFT',preview_token:'10.signature',changed_fields:5}:
    u.includes('/settings/publish')?{status:'OK',snapshot_id:'DEMO2',written_fields:5}:
    {status:'OK'};
  return {ok:true,json:async()=>v,status:200};
};</script>'''
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page()
    page.on('pageerror',lambda e:print('JS ERROR',e))
    page.set_content(markup+f'<script>window.__state={json.dumps(state)};window.__candidate={json.dumps(candidates)};</script>'+
                     '<script>'+ (root/'static/settings_master.js').read_text()+'</script>')
    page.locator('[data-tab="pivots"]').click()
    page.wait_for_selector('.pivot-wave-table tr[data-pivot-row="PEPE"]')
    assert page.locator('.pivot-wave-table tbody tr').count()==12
    assert page.locator('[data-pivot-token="BTC"][data-pivot-field="o1"]').is_disabled()
    assert page.locator('[data-pivot-token="BTC"][data-pivot-field="o1_status"]').input_value()=='CONFIRMADO'
    page.wait_for_function("document.querySelector('[data-pivot-token=VIRTUAL][data-pivot-field=o1]').value==='1.1984'")
    assert page.locator('[data-pivot-token="VIRTUAL"][data-pivot-field="o1_date"]').input_value()=='2026-01-05'
    assert page.locator('[data-pivot-token="PEPE"][data-pivot-field="o1"]').input_value()=='0.00000536'
    page.locator('[data-cl-review-token="VIRTUAL"]').click()
    page.wait_for_function("document.querySelector('[data-pivot-token=VIRTUAL][data-pivot-field=cl_status]').value==='VALIDADO_TECNICAMENTE'")
    assert page.locator('[data-pivot-token="VIRTUAL"][data-pivot-field="cl_status"]').input_value()=='VALIDADO_TECNICAMENTE' 
    page.locator('#settings-save').click()
    page.wait_for_function('window.__requests.length>=2')
    records=page.evaluate('window.__requests')
    assert records[0]['url']=='/api/settings/preview'
    assert records[1]['url']=='/api/settings/publish'
    assert records[0]['body']['entries'][0]['token']=='VIRTUAL'
    assert records[0]['body']['entries'][0]['cl_status']=='VALIDADO_TECNICAMENTE'
    assert records[0]['body']['entries'][0]['cl_review_proof'].startswith('1000.')
    assert records[1]['body']['confirm']=='PUBLICAR'
    print('PASS Chromium: CL 1W technical review, states, per-token proof, preview then publish')
    browser.close()
