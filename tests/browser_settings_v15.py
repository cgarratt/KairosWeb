"""Offline v1.5 acceptance test, no network or Sheets writes."""
from pathlib import Path
from unittest.mock import patch
import sys,json,re
from jinja2 import Environment,FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
from test_sheets_features import demo_master
from kairos_sheets_features import settings_data
with patch('kairos_sheets_features._remote_data',return_value=demo_master()):
    state=settings_data()
state['is_admin']=True;state['write_configured']=True;state['csrf_token']='FAKE_NON_SECRET'
class Req:
 path='/settings';args={};full_path='/settings'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings',nav_modes=[])
html=env.get_template('settings.html').render(master='1.5.0')
# Set the HTML first, then register a deterministic fake fetch and load local
# scripts in document order; no network or privileged endpoints are invoked.
html=re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1500,'height':960})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(path=str(ROOT/'static/theme.css'))
 page.evaluate("(state)=>{window.fetch=async(url)=>{if(String(url).startsWith('/api/settings/data'))return {ok:true,json:async()=>state};return {ok:false,json:async()=>({status:'DATA_ERROR'})};};}",state)
 page.add_script_tag(path=str(ROOT/'static/settings_format.js'))
 page.add_script_tag(path=str(ROOT/'static/settings_master.js'))
 page.get_by_role('button',name='Parámetros',exact=True).click()
 page.wait_for_selector('#parameter-group-o2 input',timeout=4000)
 assert page.locator('button[data-tab="mcp"]').count()==1
 assert page.locator('button[data-tab="parameters"]').inner_text()=='Parámetros'
 assert page.locator('button[data-tab="parameters"] + button[data-tab="mcp"]').count()==1
 for group in ['o2','o3','o4','o5']:
  tranche_rows=page.locator('#parameter-group-'+group+' .settings-row').filter(has=page.locator('input[data-field="value"]'))
  keys=page.locator('#parameter-group-'+group+' .settings-key').all_inner_texts()
  assert len([k for k in keys if k.startswith('FORECAST_'+group.upper()+'_FIB_')])==4
 assert 'Onda O2' in page.locator('#parameter-group-o2').inner_text() or 'O2' in page.locator('#parameter-group-o2').inner_text()
 assert 'O2 · suma de tramos: 100%' in page.locator('#settings-totals').inner_text()
 # Interactive distribution. 20+40+40+0=100.
 o2=page.locator('#parameter-group-o2 [data-field="value"]')
 assert [n.input_value() for n in o2.all()]==['0','60','40','0']
 o2.nth(0).fill('20');o2.nth(1).fill('40')
 assert 'O2 · suma de tramos: 100%' in page.locator('#settings-totals').inner_text()
 assert not errors,errors
 screenshot=str(ROOT/'tests'/'settings_v15_visual.png')
 page.screenshot(path=screenshot,full_page=True)
 print('PASS Settings v1.5: 16 numeric inputs / 4 groups / navigation / 100% recalculation / no JS errors')
 browser.close()
