from pathlib import Path


def test_compras_slider_uses_available_cash_percent_instead_of_patrimony_percent():
    html = (Path(__file__).resolve().parents[1] / 'templates' / 'trade_sim.html').read_text()
    assert "max=\"{{ 100 if mode.slug=='compras' else payload.current.max_percent }}\"" in html
    assert "value=\"{{ 100 if mode.slug=='compras' else payload.current.requested_percent|default(payload.current.default_percent) }}\"" in html
    assert "step=\"{{ 0.1 if mode.slug=='compras' else 'any' }}\"" in html
    assert "Capital para compras (% de USDT disponible)" in html
    assert "100% = Máximo disponible:" in html
    assert "0% · USDT $0" in html
    assert "window.KairosPurchaseWeights.budgetFromAvailablePercent(target,maxBuyCash)" in html
    assert "const desired=P*target/100;" not in html
    assert "window.KairosSalesOptimizer.calculate(source.tokens,cash,target,source.current.band_pp,source.current.trading)" in html # Ventas v1.3.5 optimized
    assert "const forecastPatrimonyPercent=P>0?100*referenceCapacity/P:0;" in html
