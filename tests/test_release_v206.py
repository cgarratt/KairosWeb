from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from xml.etree import ElementTree
ROOT=Path(__file__).resolve().parents[1]
def test_release_version_and_asset_diagnostics():
    app=(ROOT/'app.py').read_text()
    assert "APP_VERSION = '2.0.16'" in app
    assert 'def _deployed_asset_status():' in app
    assert "'release_assets': assets" in app
    assert '<th>% Peso</th>' in (ROOT/'templates/trade_sim.html').read_text()

def test_donut_ssr_and_accounting():
    env=Environment(loader=FileSystemLoader(ROOT/'templates'))
    src=(ROOT/'templates/portfolio_integral.html').read_text()
    start=src.index('<article class="panel"><h3>Composición del capital histórico')
    template=env.from_string(src[start:src.index('</article>',start)+len('</article>')])
    assert 'integral-stack' not in (ROOT/'templates/portfolio_integral.html').read_text()
    segments=[{'key':k,'name':label,'actual_usdt':n,'target_usdt':n} for k,label,n in [
        ('hodl_core','HODL + Core',45000),('exchange','Exchange',24000),('liquidity','Liquidez',20295),('trading','Trading',7225),('lost','Lost · realizado',40955)]]
    base=150000;rest=base-sum(s['actual_usdt'] for s in segments)
    # This fixture intentionally has a remainder; chart segments should not invent it.
    rendered=template.render(master='2.0.6',segments=segments,base=base,alive=96520,lost=40955,
        gain_to_recover=0,spot=None,source_note='TEST',total_recorded=sum(s['actual_usdt'] for s in segments),total_target=base)
    assert 'data-capital-chart="donut"' in rendered
    assert 'Composición del capital histórico' in rendered
    assert rendered.count('integral-donut-sector')==5  # one SVG sector per segment
    assert 'HODL + Core' in rendered and 'Lost · realizado' in rendered
    assert '$150,000' in rendered
    assert 'integral-donut-center' in rendered
    assert rest > 0
