"""Standalone Chromium smoke test v2.0.5 (offline fixture, no Google writes)."""
from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Req: path='/mode/compras'
def url(endpoint, **kwargs):
    return '/static/'+kwargs.get('filename','') if endpoint=='static' else '/settings'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),nav_modes=[],url_for=url)
P=1040
max_deploy=35/P*100
payload={
  'kind':'compras',
  'current':{'P':P,'cash':40,'cash_pct':40/P*100,'trading':5,'max_percent':max_deploy,'reference_cap':35},
  'tokens':[
      {'token':'A','price':100,'current_usdt':800,'target':.10,'weight':.80,'tier':'T1'},
      {'token':'B','price':100,'current_usdt':200,'target':.90,'weight':.20,'tier':'T1'},
  ],
  'o2_levels':{'A':{'c1':80,'c2':60},'B':{'c1':99,'c2':98}},
  'o2_histories':{
       'A':{'status':'PROVISIONAL','post_o1_min':20,'estimated_o1_date':'2026-10-01','post_o1_min_date':'2026-10-05'},
       'B':{'status':'PROVISIONAL','post_o1_min':96,'estimated_o1_date':'2026-10-01','post_o1_min_date':'2026-10-05'}
  },
  'forecast_o2_allocation':[20,30,40,10],
  'drift_band_pp':1,'structural_liquidity_target':.4,
}
html=env.get_template('trade_sim.html').render(mode={'slug':'compras','name':'Compras','description':'Simulación O2'},payload=payload,master='2.0.5')
assert 'data-o2-ui-version="2.0.5"' in html
assert 'o2-drift-dot' in html

def inline_script(m):
    path=ROOT/'static'/m.group(1)
    return '<script>'+path.read_text(encoding='utf-8')+'</script>' if path.exists() else ''
html=re.sub(r'<script src="/static/([\w./-]+)(?:\?[^\"]*)?"[^>]*></script>',inline_script,html)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1450,'height':1000})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html)
    page.wait_for_selector('#fib-body tr')
    slider=page.locator('#allocation-slider')
    assert abs(float(slider.input_value())-max_deploy)<.00001
    assert page.locator('#o2-fibonacci-panel .o2-drift-dot').count()==8
    row_a=page.locator('#fib-body tr').first
    assert row_a.locator('.o2-drift-dot.drift-sobre').count()==4
    assert row_a.locator('td').nth(2).get_attribute('class')=='level-hit'
    assert row_a.locator('td').nth(3).get_attribute('class')=='level-hit'
    assert row_a.locator('td').nth(3).inner_text().strip()=='$0.00'
    row_b=page.locator('#fib-body tr').nth(1)
    assert row_b.locator('.o2-drift-dot.drift-infra').count()>=1
    assert float(row_b.locator('td').nth(3).inner_text().replace('$','').replace(',',''))>0
    assert not [e for e in errors if 'Failed to fetch' not in e],errors
    print('PASS Chromium: slider max, visible 8 dots, green USD $0 by history, sequential underweight buy')
    browser.close()
