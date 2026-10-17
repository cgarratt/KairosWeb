"""Standalone browser smoke test for O2 scenario labels; no live provider or orders."""
from pathlib import Path
import json,re
from jinja2 import Environment,FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Req:path='/mode/compras'
url=lambda endpoint,**kw:('/static/'+kw.get('filename','') if endpoint=='static' else '/settings')
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),nav_modes=[],url_for=url)
A={'token':'A','price':100,'current_usdt':600,'target':.5,'weight':.6,'tier':'T1'}
B={'token':'B','price':100,'current_usdt':400,'target':.5,'weight':.4,'tier':'T1'}
payload={'kind':'compras','current':{'P':1040,'cash':40,'cash_pct':40/1040*100,'trading':0,'max_percent':40/1040*100,'reference_cap':40},'tokens':[A,B],'o2_levels':{'A':{'c1':80,'c2':60},'B':{'c1':99,'c2':98}},'forecast_o2_allocation':[25,25,25,25],'drift_band_pp':1,'structural_liquidity_target':.4}
html=env.get_template('trade_sim.html').render(mode={'slug':'compras','name':'Compras','description':'Simulación O2'},payload=payload,master='2.0.3')
def inline_script(match):
 name=match.group(1)
 p=ROOT/'static'/name
 return '<script>'+p.read_text(encoding='utf-8')+'</script>' if p.exists() else ''
html=re.sub(r'<script src="/static/([\w./-]+)"[^>]*></script>',inline_script,html)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1400,'height':1000})
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html)
 page.wait_for_selector('.o2-drift-chip')
 rows=page.locator('#fib-body tr')
 assert rows.count()==2,rows.count()
 a=rows.nth(0)
 assert a.locator('.o2-drift-chip').count()==4
 labels=[x.strip() for x in a.locator('.o2-drift-chip').all_inner_texts()]
 assert labels[0]=='SOBRE' and labels[2]=='INFRA',labels
 assert a.locator('td').nth(6).inner_text().strip().endswith('INFRA')
 assert 'level-blocked' in a.locator('td').nth(2).get_attribute('class')
 assert 'level-blocked' in a.locator('td').nth(3).get_attribute('class')
 assert 'level-blocked' not in (a.locator('td').nth(6).get_attribute('class') or '')
 assert float(a.locator('td').nth(7).inner_text().replace('$','').replace(',',''))>0
 assert a.locator('.o2-drift-chip').first.get_attribute('title').startswith('Precompra O2C1')
 assert 'band' not in ' '.join(labels)
 assert '±1.00 pp' in a.locator('.o2-drift-chip').first.get_attribute('title')
 assert not [e for e in errors if 'Failed to fetch' not in e],errors
 print('PASS browser O2 badges:',labels)
 browser.close()
