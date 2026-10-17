"""Verify O3/O5 policy independence, dynamic rebalancing and no browser writes."""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from jinja2 import Environment,FileSystemLoader
ROOT=Path(__file__).resolve().parents[1]
fixture=(ROOT/'tests/browser_forecast_v14.py').read_text().split('class Req:')[0]
ns={'__file__':str(ROOT/'tests/browser_forecast_v14.py')}
exec(compile(fixture,str(ROOT/'tests/browser_forecast_v14.py'),'exec'),ns)
payload=ns['payload']
class Req:
    path='/mode/forecast';args={};full_path='/mode/forecast'
env=Environment(loader=FileSystemLoader(ROOT/'templates'),autoescape=True)
env.globals.update(request=Req(),url_for=lambda endpoint,**kw:'/static/'+kw.get('filename','') if endpoint=='static' else '/mode/forecast',nav_modes=[{'slug':'forecast','name':'Forecast','description':'Simulación'}])
def scenario(o3btc,o5btc):
    x=dict(payload,official_o3_split=o3btc,official_o3_usdt_split=1-o3btc,official_o5_split=o5btc,official_o5_usdt_split=1-o5btc)
    html=env.get_template('forecast.html').render(payload=x,master='1.7.0')
    return re.sub(r'<script src="/static/([\w\-.]+\.js)"></script>',lambda m:'<script>\n'+(ROOT/'static'/m.group(1)).read_text()+'\n</script>',html)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1560,'height':850})
    errors=[]; network=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:network.append(r.url) if '/api/settings/save' in r.url else None)
    page.set_content(scenario(.3,.5))
    assert page.locator('#o3-master-share').inner_text().strip()=='30.0% BTC / 70.0% USDT'
    assert page.locator('#o5-master-share').inner_text().strip()=='50.0% BTC / 50.0% USDT'
    assert page.locator('#wave-custody-snapshots details').count()==4
    headers=page.locator('#wave-custody-snapshots details').nth(2).locator('th').all_text_contents()
    assert headers[-3:]==['Peso actual','Target','Desvío'],headers
    assert page.locator('#cycle-note').inner_text().find('Reparto oficial O3 30% BTC / 70% USDT; O5 50% BTC / 50% USDT.')>=0
    a=page.locator('#cycle-note').inner_text()
    page.evaluate('weights.o3=[10,20,30,40];renderAll();')
    b=page.locator('#cycle-note').inner_text()
    assert a!=b,(a,b)
    assert page.locator('#wave-custody-snapshots details').count()==4
    page2=browser.new_page(viewport={'width':1560,'height':850})
    page2.on('pageerror',lambda e:errors.append(str(e)))
    page2.on('request',lambda r:network.append(r.url) if '/api/settings/save' in r.url else None)
    page2.set_content(scenario(.8,.2))
    c=page2.locator('#cycle-note').inner_text()
    assert 'Reparto oficial O3 80% BTC / 20% USDT; O5 20% BTC / 80% USDT.' in c
    assert page.locator('#cycle-note').inner_text()!=a
    assert not errors, errors
    assert not network,network
    print('PASS Forecast 4 waves; weighted O3 changes cascade; official O3/O5 shares separate; drift tables render; no Sheet writes')
    browser.close()
