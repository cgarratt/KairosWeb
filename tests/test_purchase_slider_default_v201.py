from pathlib import Path

def test_compras_slider_defaults_to_eligible_maximum():
    html = (Path(__file__).resolve().parents[1] / 'templates' / 'trade_sim.html').read_text()
    assert 'max="{{ payload.current.max_percent }}"' in html
    assert '''value="{{ payload.current.max_percent if mode.slug=='compras' '''.strip() in html
