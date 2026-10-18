"""Real Chromium smoke of the rendered historical capital donut (offline fixtures)."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'templates/portfolio_integral.html').read_text()
a=source.index('<article class="panel"><h3>Composición del capital histórico')
b=source.index('</article>',a)+len('</article>')
env=Environment(loader=FileSystemLoader(ROOT/'templates'))
segs=[{'key':k,'name':label,'actual_usdt':n} for k,label,n in [
    ('hodl_core','HODL + Core',45573.2),('exchange','Exchange',32721.8),
    ('liquidity','Liquidez',23525),('trading','Trading',7225),('lost','Lost · realizado',40955)]]
assert abs(sum(s['actual_usdt'] for s in segs)-150000)<1e-6
html=env.from_string(source[a:b]).render(segments=segs,base=150000)
css=source.split('<style>',1)[1].split('</style>',1)[0]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':900,'height':600})
    page.set_content('<style>'+css+'</style><div class="integral-grid">'+html+'</div>')
    assert page.locator('[data-capital-chart=donut] .integral-donut-sector').count()==5
    assert page.locator('.integral-donut-center').text_content()=='$150,000'
    assert page.locator('.integral-breakdown-item').count()==5
    assert page.locator('.integral-stack').count()==0
    strokes=page.locator('.integral-donut-sector').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).stroke)')
    assert len(set(strokes))==5
    page.evaluate("document.documentElement.setAttribute('data-theme','dark')")
    assert page.locator('.integral-donut').is_visible()
    browser.close()
print('PASS Chromium v2.0.6: donut SVG, five categories, historical capital total, dark theme')
