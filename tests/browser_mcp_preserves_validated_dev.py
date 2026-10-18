"""Visual/browser: live candidate refresh never overwrites saved VALIDADO/CONFIRMADO."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]


def record(token, low, lowday, cl_status, o1, o1day, o1_status):
    r = dict(token=token,cycle_low=low,cl_date=lowday,cl_status=cl_status,
             o1=o1,o1_date=o1day,o1_status=o1_status)
    for w in ('o2','o3','o4','o5'):
        r[w]=None;r[w+'_date']=None;r[w+'_status']='PROPUESTO'
    return r

state={'status':'OK','is_admin':True,'write_configured':True,'csrf_token':'TEST',
       'snapshot_id':'DEMO','fecha_corte':'2026-10-17','sections':{
       'units':[],'targets':[],'liquidity':[],'tier_custody':[],'parameters':[],
       'pivots':[
       record('BTC',57800.19,'2026-07-01','VALIDADO',87395.67,'2026-09-21','VALIDADO'),
       record('ETH',1505.68,'2026-06-06','CONFIRMADO',2807.34,'2026-09-21','CONFIRMADO'),
       record('SOL',60.13,'2026-06-06','PROPUESTO',124.95,'2026-09-27','PROPUESTO')
       ]}}
updated={
 'BTC':dict(token='BTC',status='CANDIDATO_MCP_NO_CERTIFICADO',cycle_low=55555,cl_date='2026-08-01',o1=99000,o1_date='2026-10-01'),
 'ETH':dict(token='ETH',status='CANDIDATO_MCP_NO_CERTIFICADO',cycle_low=1700,cl_date='2026-06-16',o1=3000,o1_date='2026-10-04'),
 'SOL':dict(token='SOL',status='CANDIDATO_MCP_NO_CERTIFICADO',cycle_low=62.2,cl_date='2026-07-01',o1=131,o1_date='2026-10-04')
}
markup='''<div id="settings-nav"><button data-tab="units">Unidades</button><button data-tab="pivots">Pivotes O1–O5</button></div>
<h2 id="settings-title"></h2><div id="settings-desc"></div><div id="settings-snapshot"></div>
<div id="settings-admin-state"></div><div id="settings-pivots-tools" hidden><button id="settings-preliminary"></button><div id="settings-preliminary-progress"></div></div>
<section id="settings-mcp-panel" hidden></section><div class="settings-form"><input id="settings-evidence" value="Justificación revisada manualmente"></div>
<div id="settings-data"></div><div id="settings-pivot-matrix" hidden></div><div id="settings-totals"></div>
<div><button id="settings-save">Guardar cambios</button></div><div id="settings-msg"></div>
<script>window.KairosFormatting={labels:{},scale:()=>'',toDisplay:v=>v};
window.__requests=[];
window.fetch=async (url,opts={})=>{
 const u=String(url); window.__requests.push(u);
 let v=u.startsWith('/api/settings/data')?window.__state:u.includes('/pivots/preliminary')?
  {status:'OK',records:u.includes('token=')?[window.__live[new URL('http://localhost'+u).searchParams.get('token')]]:Object.values(window.__live)}:
  u.includes('/technical-review')?{status:'OK',validated:false,review_proof:null}:
  {status:'OK'};
 return {ok:true,json:async()=>v,status:200};
};</script>'''

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(markup+f'<script>window.__state={json.dumps(state)};window.__live={json.dumps(updated)};</script>'+
                     '<script>'+ (root/'static/settings_master.js').read_text()+'</script>')
    page.locator('[data-tab="pivots"]').click()
    page.wait_for_selector('.pivot-wave-table tr[data-pivot-row="SOL"]')
    page.wait_for_function("document.querySelector('[data-pivot-token=SOL][data-pivot-field=o1]').value==='131'")
    # On archived refresh, saved VALIDADO and CONFIRMADO remain untouched.
    field=lambda tok,key:page.locator(f'[data-pivot-token="{tok}"][data-pivot-field="{key}"]')
    assert field('BTC','cycle_low').input_value()=='57800.19'
    assert field('BTC','o1').input_value()=='87395.67'
    assert field('BTC','cl_status').input_value()=='VALIDADO'
    assert field('ETH','cycle_low').input_value()=='1505.68'
    assert field('ETH','o1_status').input_value()=='CONFIRMADO'
    page.locator('#settings-preliminary').click()
    page.wait_for_function("!document.querySelector('#settings-preliminary').disabled",timeout=30000)
    # No MCP updates/downgrades, even when the proposed values differ and technical review fails.
    for t,expected in [('BTC',('57800.19','2026-07-01','87395.67','2026-09-21','VALIDADO','VALIDADO')),
                        ('ETH',('1505.68','2026-06-06','2807.34','2026-09-21','CONFIRMADO','CONFIRMADO'))]:
        assert tuple(field(t,x).input_value() for x in ('cycle_low','cl_date','o1','o1_date','cl_status','o1_status'))==expected
    assert field('SOL','cycle_low').input_value()=='62.2'
    assert field('SOL','cl_status').input_value()=='PROPUESTO'
    calls=page.evaluate('window.__requests')
    assert not any('/technical-review?' in u and ('token=BTC' in u or 'token=ETH' in u) for u in calls)
    assert not any('/settings/publish' in u or '/settings/preview' in u for u in calls)
    # A status already VALIDADO in an unpublished draft also freezes that wave.
    field('SOL','cl_status').select_option('VALIDADO')
    field('SOL','o1_status').select_option('VALIDADO')
    # Admin can manually correct an already published VALIDADO anchor.
    field('BTC','cycle_low').fill('58000')
    page.locator('#settings-preliminary').click()
    page.wait_for_function("!document.querySelector('#settings-preliminary').disabled",timeout=30000)
    assert field('BTC','cycle_low').input_value()=='58000'
    assert field('BTC','cl_status').input_value()=='VALIDADO'
    assert field('SOL','cycle_low').input_value()=='62.2'
    assert field('SOL','o1').input_value()=='131'
    assert field('SOL','cl_status').input_value()=='VALIDADO'
    assert field('SOL','o1_status').input_value()=='VALIDADO'
    assert not errors, errors
    print('PASS Chromium: MCP only edits PROPUESTO; VALIDADO/CONFIRMADO frozen; manual draft respected')
    browser.close()
