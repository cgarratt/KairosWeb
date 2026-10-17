"""Offline visual smoke: settings MCP diagnostics and theme/tooltip. No account access."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
tpl=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
class Request:
    path='/settings';args={'tab':'mcp'}
    @property
    def full_path(self):return '/settings?tab=mcp'

tpl.globals.update(request=Request(),url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings',nav_modes=[dict(slug='portafolio',name='Portafolio',description='Portfolio')])
html=tpl.get_template('settings.html').render(master='1.3.0')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1320,'height':950})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html)
    page.add_style_tag(path=str(ROOT/'static/alerts_settings.css'))
    page.add_style_tag(path=str(ROOT/'static/theme.css'))
    page.evaluate("document.documentElement.dataset.theme='dark'")
    page.add_script_tag(content='''
       window._requests=[];
       window.fetch=async(url,options={})=>{
         _requests.push(url);
         const status=url.includes('mcp-diagnostics')?{status:'OK',providers:{[url.includes('binance')?'binance':'hyperliquid']:{status:'OK',source:'MCP TEST',records:12,last_success_utc:'2026-10-17T12:00:00Z'}}}:
         url.includes('/api/admin/session')?{status:'OK',is_admin:true,csrf_token:'test-csrf'}:
         url.includes('/api/mcp-refresh')?{status:'OK',result:{status:'OK',records:12,last_success_utc:'2026-10-17T13:00:00Z'}}:
         {status:'OK',snapshot_id:'TEST',is_admin:true,write_configured:true,csrf_token:'test-csrf',sections:{mcp:[],units:[],targets:[],tier_custody:[],liquidity:[],parameters:[],pivots:[]}};
         return {ok:true,json:async()=>status};
       };
    ''')
    for name in ['settings_format.js','settings_master.js','mcp_settings.js','tooltips.js']:
        page.add_script_tag(path=str(ROOT/'static'/name))
    page.locator('[data-tab=mcp]').click()
    page.wait_for_function("document.querySelector('#settings-mcp-panel').hidden===false")
    page.wait_for_function("Array.from(document.querySelectorAll('.mcp-health-state')).every(e=>e.textContent.includes('Conectado'))")
    assert page.locator('#settings-mcp-panel').is_visible()
    assert not page.locator('#settings-save').is_visible()
    assert page.locator('#settings-title').inner_text()=='Estado de conexiones MCP'
    assert not page.locator('.hero .badge.info').count()
    page.locator('.mcp-refresh[data-provider=binance]').click()
    page.wait_for_function("_requests.includes('/api/mcp-refresh')")
    assert not errors,errors
    assert page.locator('.global-nav-link').first.get_attribute('title')
    page.screenshot(path='/mnt/data/KairosWeb_v1.3.0_VISUAL_SETTINGS.png',full_page=False)
    print('PASS: settings MCP visible, status and manual refresh, no decorative badge, tooltips, dark theme; no real API/Sheets writes')
    browser.close()
