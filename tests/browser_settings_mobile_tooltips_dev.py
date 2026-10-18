"""Chromium: no button/menu title/tap tooltips on mobile, but desktop titles remain."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
js=(ROOT/'static/tooltips.js').read_text(encoding='utf-8')
html='''<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body><nav><a id="menu" class="global-nav-link" href="/mode/compras" title="Abrir Compras">Compras</a></nav>
<button id="btn" title="Guardar cambios" aria-label="Guardar cambios">Guardar</button>
<button id="nolabel" aria-label="Abrir opciones">Abrir</button>
<script>window.__isTest=true;</script><script>''' + js + '''</script></body></html>'''

with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  desktop=browser.new_page(viewport={'width':1250,'height':800},has_touch=False)
  desktop.set_content(html)
  desktop.wait_for_timeout(350)
  assert desktop.locator('#menu').get_attribute('title')=='Abrir Compras'
  assert desktop.locator('#btn').get_attribute('title')=='Guardar cambios'
  assert desktop.locator('#nolabel').get_attribute('title')=='Abrir opciones'
  desktop.evaluate("document.body.insertAdjacentHTML('beforeend','<button id=dynamic title=\"Nueva acción\">Nuevo</button>')")
  desktop.wait_for_timeout(150)
  assert desktop.locator('#dynamic').get_attribute('title')=='Nueva acción'
  mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  mobile.set_content(html)
  mobile.wait_for_timeout(350)
  for elem in ['#menu','#btn','#nolabel']:
    assert mobile.locator(elem).get_attribute('title') is None,elem
  mobile.evaluate("document.body.insertAdjacentHTML('beforeend','<button id=dynamic title=\"Nueva acción\">Nuevo</button>')")
  mobile.wait_for_timeout(150)
  assert mobile.locator('#dynamic').get_attribute('title') is None
  mobile.locator('#btn').tap()
  assert mobile.locator('.kairos-tap-tooltip').is_hidden()
  assert mobile.locator('#btn').get_attribute('aria-label')=='Guardar cambios'
  # Form factor can change without reload: desktop hints must come back.
  desktop.set_viewport_size({'width':390,'height':844})
  desktop.wait_for_timeout(180)
  assert desktop.locator('#btn').get_attribute('title') is None
  desktop.set_viewport_size({'width':1250,'height':800})
  desktop.wait_for_timeout(180)
  assert desktop.locator('#btn').get_attribute('title')=='Guardar cambios'
  assert desktop.locator('#menu').get_attribute('title')=='Abrir Compras'
  browser.close()
print('CHROMIUM PASS: desktop tooltip retention, mobile removal, dynamic elements and resize.')
