"""Offline acceptance: real forecast UI rendered with simulated 12-asset payload.
No exchange, Google Sheets, or network writes.
"""
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
from playwright.sync_api import sync_playwright
import re
ROOT=Path(__file__).resolve().parents[1]
TOK=['BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PLUME','VIRTUAL','PEPE']
TIERS=['T1']*5+['T2']*5+['T3']*2
TARGETS=[.2,.15,.15,.1,.1,.05,.05,.05,.05,.05,.025,.025]
quotes=[80000,2400,100,12,80,.08,1,.45,.004,.02,.6,.000004]
# 10000 USDT sleeve, 30k cash / 5k QF: O3 target 40% begins below target.
pivots=[{'token':t,'c1':p*.9,'c2':p*.83,'ref382':p*.95,'ref786':p*.74,'cycle_low':p*.75,'o1':p*1.05} for t,p in zip(TOK,quotes)]
units=[0.1,3,20,100,120,2000,100,1000,50000,20000,200,10000000]
assets=[{'token':t,'price':px,'units':u,'target':target,'tier':tier,'current_usdt':u*px} for t,px,u,target,tier in zip(TOK,quotes,units,TARGETS,TIERS)]
cs={t:[u*.2,u*.3,u*.5] for t,u in zip(TOK,units)}
payload={'o2_source':'FAKE_MCPS_ARCHIVE','generated_at':'2026-10-17T12:00:00Z','snapshot_note':'SYNTHETIC',
 'current':{'P':100000,'crypto_value':70000,'max_percent':25,'reference_cap':25000},
 'cash_total':30000,'trading_reserve':5000,'tokens':assets,'pivot_rows':pivots,'custody':cs,
 'custody_policy':{'T1':[.4,.3,.3],'T2':[0,.3,.7],'T3':[0,0,1]},
 'forecast_fibo_allocations':{'o2':[0,60,40,0],'o3':[40,30,20,10],'o4':[0,60,40,0],'o5':[20,20,30,30]},
 'official_o3_split':.3,'official_o3_usdt_split':.7,'official_o5_split':.5,'official_o5_usdt_split':.5,'o3_liquidity_target':.4}
class Req:
 path='/mode/forecast';args={};full_path='/mode/forecast'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/mode/forecast',nav_modes=[dict(slug='forecast',name='Forecast',description='Escenario')])
html=env.get_template('forecast.html').render(payload=payload,master='1.7.0')
# Browser has no app server: safely inline local JS assets.
def inject(m):
 name=m.group(1)
 fp=ROOT/'static'/name
 return '<script>\n'+fp.read_text(encoding='utf8')+'\n</script>' if fp.exists() else ''
html=re.sub(r'<script src="/static/([\w\-.]+\.js)"></script>',inject,html)
with sync_playwright() as playwright:
 browser=playwright.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1600,'height':980})
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='domcontentloaded')
 page.add_style_tag(path=str(ROOT/'static/theme.css'))
 # Offline fixture omits the bundled privacy script; bootstrap privacy here.
 page.add_script_tag(path=str(ROOT/'static/privacy.js'))
 page.locator('#privacy-toggle').click()  # synthetic scenario only
 page.evaluate("document.documentElement.dataset.theme='dark'")
 page.wait_for_timeout(100)
 print('PAGE_ERRORS:',errors)
 print('VALIDATION:',page.locator('#weights-validation').inner_text())
 print('ROWS:',page.locator('#fib-body tr').count(),page.locator('#cycle-assets tr').count(),'PANELS:',page.locator('.forecast-custody-snapshot').count())
 print('NOTE:',page.locator('#cycle-note').inner_text()[:450])
 assert not errors,errors
 assert page.locator('#fib-body tr').count()==12
 assert page.locator('#cycle-assets tr').count()==12
 assert page.locator('.forecast-custody-snapshot').count()==4
 assert page.locator('#weights-validation').inner_text().startswith('Todos los tramos')
 assert page.locator('#cycle-note').inner_text().startswith('Presupuestos teóricos O2')
 init=page.locator('#cycle-note').inner_text()
 page.locator('[data-forecast-stage="o2"][data-level="0"]').fill('20')
 assert 'NO VALIDADO' in page.locator('#weights-validation').inner_text()
 page.locator('[data-forecast-stage="o2"][data-level="1"]').fill('40')
 page.locator('[data-forecast-stage="o2"][data-level="2"]').fill('40')
 page.locator('[data-forecast-stage="o2"][data-level="3"]').fill('0')
 assert 'Todos los tramos' in page.locator('#weights-validation').inner_text()
 page.select_option('#o2-choice','0.786')
 updated=page.locator('#cycle-note').inner_text()
 assert init!=updated,(init,updated)
 assert not errors,errors
 # v1.9 semaforo: verde spot bajo referencia, ámbar a 0.8% de distancia.
 page.evaluate("fc.tokens[0].price=fc.pivot_rows[0].c1*0.999;fc.tokens[1].price=fc.pivot_rows[1].ref382*1.008;renderFib()")
 btc=page.locator('#fib-body tr').nth(0)
 eth=page.locator('#fib-body tr').nth(1)
 assert btc.locator('td[data-fibo="1"][data-level-status="hit"]').count()==1
 assert eth.locator('td[data-fibo="0"][data-level-status="near"]').count()==1
 assert 'Verde' in btc.locator('td[data-fibo="1"]').get_attribute('title')
 assert 'Ámbar' in eth.locator('td[data-fibo="0"]').get_attribute('title')
 assert page.locator('#fib-body tr').first.locator('td.fc-level-hit').count()>0
 assert page.locator('#fib-body tr').first.locator('td:nth-child(3).fc-level-hit').count()==0
 assert not errors,errors
 path='/mnt/data/KairosWeb_v1.4.0_FORECAST_SMOKE.png'
 page.screenshot(path=path,full_page=False)
 print('PASS browser forecast v1.4.0; preview',path)
 browser.close()
