"""Chromium-only visual smoke test for event-first bell (development)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
rows=[
 {'id':'a','token':'HBAR','created_utc':'2026-10-18T12:19:00Z','kind':'BREAK_ALCISTA','timeframe':'4H','mode':'Alertas','mode_identified':False,'is_trade_ready':False,'action':'Revisar O3 y O5'},
 {'id':'b','token':'PLUME','created_utc':'2026-10-18T08:27:00Z','kind':'BREAK_BAJISTA','timeframe':'4H','mode':'TradingBot','mode_identified':True,'is_trade_ready':False,'action':'Revisar estructura técnica'},
 {'id':'c','token':'BTC','created_utc':'2026-10-18T12:21:00Z','kind':'BALANCER_ACCION','timeframe':'1D','mode':'Balancer','mode_identified':True,'is_trade_ready':False,'action':'Revisar liquidez'}]
markup='''<div class="alerts-wrap"><button id="bell-open"></button><span id="bell-count" hidden></span>
<div class="alerts-popover" id="alerts-popover" hidden><button id="alerts-refresh"></button><button id="alerts-read-all"></button><div id="alerts-list"></div></div></div>
<script>window.__readCalls=[];window.confirm=()=>true;
window.fetch=async (url,opts={})=>{
 const u=String(url);if(u.includes('/api/alerts/read')){window.__readCalls.push(u);return {ok:true,json:async()=>({status:'OK'})};}
 return {ok:true,json:async()=>({status:'OK',can_mark_read:true,unread_count:3,records:window.__records,limited:false})};
};</script>'''
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':900,'height':650})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<style>:root{--text:#dce8f8;--muted:#bed0e3;--line:#56718b;--soft:#1d3957;--viz-border:#456;}body{background:#101a2b;color:#eff;}'+(root/'static/alerts_settings.css').read_text()+'</style>'+markup+
                     '<script>document.documentElement.setAttribute("data-theme","dark");window.__records='+json.dumps(rows)+';</script>'+ 
                     '<script>'+(root/'static/alert_bell.js').read_text()+'</script>')
    page.locator('#bell-open').click()
    page.wait_for_selector('.alert-record')
    assert page.locator('.alert-event-type').count()==3
    assert page.locator('.alert-event-type.event-bull').inner_text()=='BREAK ALCISTA'
    assert page.locator('.alert-event-type.event-bear').inner_text()=='BREAK BAJISTA'
    assert page.locator('.alert-mode').all_inner_texts()==['Alertas','TradingBot','Balancer']
    assert page.get_by_text('INFORMATIVA').count()==0
    bull=page.locator('.alert-event-type.event-bull').evaluate('(e)=>getComputedStyle(e).backgroundColor')
    bear=page.locator('.alert-event-type.event-bear').evaluate('(e)=>getComputedStyle(e).backgroundColor')
    assert bull!=bear and bull!='rgba(0, 0, 0, 0)' and bear!='rgba(0, 0, 0, 0)'
    page.locator('.alert-read-one').first.click()
    page.wait_for_function('window.__readCalls.length>0')
    assert not errors,errors
    print('PASS Chromium: colored BREAK badges, mode source labels, no INFORMATIVA, individual read')
    browser.close()
