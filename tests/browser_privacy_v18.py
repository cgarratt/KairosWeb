"""Offline banking-style privacy regression: data isn't posted; numeric balances hide dynamically."""
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
html='''<!doctype html><html><head><title>Offline test</title></head><body>
<button id="privacy-toggle" aria-label="Mostrar saldos"><span class="privacy-label">Mostrar</span></button>
<main class="shell"><div id="portfolio">US$ 125,250.37</div>
<span id="bvalue">0.11344000 BTC</span><span id="percent">25.4%</span>
<table><tr><td id="price" data-public-price="true">US$81,629.301</td><td data-private="units" id="units">0.11344</td></tr></table>
<div id="dynamic"></div><div id="tooltip" title="HYPE: $15,190.52">HYPE</div>
<input data-field="hodl" value="100.12345" id="sensitive-input" /></main></body></html>'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page()
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html)
 page.add_script_tag(path=str(root/'static/privacy.js'))
 page.wait_for_function("document.querySelector('#portfolio').innerText==='*****'")
 assert page.locator('#portfolio').inner_text()=='*****'
 assert page.locator('#bvalue').inner_text()=='*****'
 assert page.locator('#percent').inner_text()=='25.4%'
 assert page.locator('#price').inner_text()=='US$81,629.301'
 assert page.locator('#units').inner_text()=='*****'
 assert page.locator('#tooltip').get_attribute('title')=='HYPE: *****'
 assert page.locator('#sensitive-input').get_attribute('type')=='password'
 page.evaluate("document.getElementById('dynamic').innerHTML='<b>US$ 48,750.16</b>'")
 page.wait_for_function("document.querySelector('#dynamic').innerText==='*****'")
 page.locator('#privacy-toggle').click()
 page.wait_for_function("document.querySelector('#portfolio').innerText==='US$ 125,250.37'")
 assert page.locator('#dynamic').inner_text()=='US$ 48,750.16'
 assert page.locator('#bvalue').inner_text()=='0.11344000 BTC'
 assert page.locator('#units').inner_text()=='0.11344'
 assert page.locator('#tooltip').get_attribute('title')=='HYPE: $15,190.52'
 assert page.locator('#sensitive-input').get_attribute('type')=='text'
 page.locator('#privacy-toggle').click()
 page.wait_for_function("document.querySelector('#dynamic').innerText==='*****'")
 assert not errors,errors
 print('PASS v1.8.0 privacy: hidden default, live mutation, public spot, percentage, tooltip, input, show/hide')
 browser.close()
