"""Local Chromium acceptance: canonical order, original parameter write identities; no production calls."""
import re,sys
from pathlib import Path
from unittest.mock import patch
from jinja2 import Environment,FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from kairos_sheets_features import settings_data
from test_sheets_features import demo_master
with patch('kairos_sheets_features._remote_data',return_value=demo_master()): state=settings_data()
state.update({'is_admin':True,'write_configured':True,'csrf_token':'LOCAL_FAKE_CSRF'})
# Reproduce the historic Master insertion order O2C4 before O2C3.
rows=state['sections']['parameters']
for stage in ['O2','O3','O4','O5']:
    from_index=[i for i,r in enumerate(rows) if r['key'].startswith('FORECAST_'+stage+'_FIB_')]
    rotated=[rows[i] for i in from_index][::-1]
    for i,row in zip(from_index,rotated): rows[i]=row
class Req:
    path='/settings';args={};full_path='/settings'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings',nav_modes=[])
html=env.get_template('settings.html').render(master='1.7.0')
html=re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1600,'height':960})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(path=str(ROOT/'static/theme.css'))
    page.evaluate("""(state)=>{
      window.savePayloads=[];
      window.fetch=async(url,opts)=>{
       if(String(url)==='/api/settings/data')return {ok:true,json:async()=>state};
       if(String(url)==='/api/settings/save'){
         window.savePayloads.push(JSON.parse(opts.body));
         return {ok:true,json:async()=>({status:'OK',snapshot_id:'OFFLINE_SIMULATION',written_fields:2})};
       }
       throw Error('External/unauthorized fetch: '+url);
      };
      window.confirm=()=>true;
    }""",state)
    page.add_script_tag(path=str(ROOT/'static/settings_format.js'))
    page.add_script_tag(path=str(ROOT/'static/settings_master.js'))
    page.get_by_role('button',name='Parámetros',exact=True).click()
    expected={
      'o2':['382','500','618','786'],
      'o3':['1618','2618','3618','4618'],
      'o4':['382','500','618','786'],
      'o5':['1618','2618','3618','4618']}
    for stage,fracs in expected.items():
        keys=page.locator('#parameter-group-'+stage+' .settings-key').all_inner_texts()
        tranche_keys=[k for k in keys if k.startswith('FORECAST_'+stage.upper()+'_FIB_')]
        assert tranche_keys==['FORECAST_'+stage.upper()+'_FIB_'+n+'_PCT' for n in fracs],(stage,tranche_keys)
    c3=page.locator('#parameter-group-o2 .settings-row').filter(has=page.locator('.settings-key',has_text='FORECAST_O2_FIB_618_PCT'))
    c4=page.locator('#parameter-group-o2 .settings-row').filter(has=page.locator('.settings-key',has_text='FORECAST_O2_FIB_786_PCT'))
    assert c3.locator('[data-field="value"]').input_value()=='40'
    assert c4.locator('[data-field="value"]').input_value()=='0'
    c3.locator('[data-field="value"]').fill('35')
    c4.locator('[data-field="value"]').fill('5')
    assert 'O2 · suma de tramos: 100%' in page.locator('#settings-totals').inner_text()
    page.locator('#settings-evidence').fill('PRUEBA LOCAL sin conexión real')
    page.locator('#settings-save').click()
    page.wait_for_function('window.savePayloads.length===1')
    payload=page.evaluate('window.savePayloads[0]')
    assert payload['section']=='parameters'
    edits={r['key']:r['value'] for r in payload['entries']}
    assert edits=={'FORECAST_O2_FIB_618_PCT':35,'FORECAST_O2_FIB_786_PCT':5},edits
    assert not errors,errors
    print('PASS v1.7.0 browser: O2/O3/O4/O5 sequential; data-index preserved; simulated audited payload has EXACT keys; no external calls')
    browser.close()
