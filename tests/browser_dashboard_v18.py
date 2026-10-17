"""Offline Dashboard rendering, new columns/price precision and privacy on refreshed Spot data."""
from pathlib import Path
from jinja2 import Environment,FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Req:path='/'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),nav_modes=[],url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/settings')
html=env.get_template('index.html').render(master='1.8.0')
rows=[
 {'token':'BTC','tier':'T1','units':.11344,'hodl_units':.1,'core_units':0,'exchange_units':.01344,'price':81629.301,'value':9260,'weight':.5,'target':.2,'drift_pp':30,'status':'SOBRE','avg_cost':62590.056,'pnl_pct':30.4201},
 {'token':'ETH','tier':'T1','units':3.45,'hodl_units':1.5,'core_units':1.5,'exchange_units':.45,'price':2421.62457,'value':8355,'weight':.5,'target':.15,'drift_pp':35,'status':'SOBRE','avg_cost':1746.377,'pnl_pct':38.66}]
data={'status':'OK','total_value':37615,'crypto_value':17615,'crypto_pct':17615/37615,'usdt_total':20000,'usdt_pct':20000/37615,'trading_reserve':7225,'snapshot_date':'2026-10-17','observed_at':'2026-10-17T20:00:00Z','rows':rows,'bsi_historical':{'rows':[]},'profitability':{'top5':[],'verified_count':2}}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1530,'height':940})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html,wait_until='domcontentloaded')
 page.evaluate('(data)=>{window.fetch=async()=>({ok:true,json:async()=>data})}',data)
 page.add_script_tag(path=str(ROOT/'static/privacy.js'))
 page.evaluate('refreshData()')
 page.wait_for_function("document.querySelector('#positions tr td')!==null")
 assert [x.lower() for x in page.locator('th').all_inner_texts()[-10:]]==[x.lower() for x in ['Token','Estado','Unidades','Peso','Target','Precio Spot','Valor USDT','Valor BTC','Precio Medio','Rentabilidad']]
 assert page.locator('#positions tr').count()==2
 btc=page.locator('#positions tr').nth(0)
 assert btc.locator('td').count()==10
 assert 'US$81,629.301' in btc.locator('td').nth(5).inner_text()
 assert btc.locator('td').nth(6).inner_text()=='*****'
 assert btc.locator('td').nth(2).inner_text()=='*****'
 assert btc.locator('td').nth(8).inner_text()=='*****'
 assert '+30.42%' in btc.locator('td').nth(9).inner_text()
 page.locator('#privacy-toggle').click()
 page.wait_for_function("document.querySelector('#positions tr td[data-private=money]').textContent.includes('$')")
 assert '$9,260.00' in btc.locator('td').nth(6).inner_text()
 assert 'US$62,590.056' in btc.locator('td').nth(8).inner_text()
 assert not errors,errors
 print('PASS dashboard v1.8.0: ten columns, public spot 5 decimals, cost 5 decimals, privacy, rentabilidad')
 browser.close()
