from pathlib import Path

def test_compras_has_distinct_maximum_and_eligible_spend():
    root=Path(__file__).resolve().parents[1]
    html=(root/'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'Máximo disponible para Compras' in html
    assert 'id="max-buy-metric"' in html
    assert 'id="max-buy-slider"' in html
    assert 'Compra simulada elegible' in html
    assert 'maxBuyCash=Math.max(0,Number(source.current.reference_cap ?? (cash-trading)))' in html
    assert "dollar(Math.max(0,referenceCapacity-sum))" in html
    assert "el('allocation-metric').textContent=dollar(sum)" in html
    assert "const referenceCapacity=Math.max(0,Math.min(desired,maxBuyCash));" in html
    assert 'purchase-metrics' in html

def test_backend_maximum_is_cash_less_qf_not_structural_spend():
    root=Path(__file__).resolve().parents[1]
    api=(root/'app.py').read_text(encoding='utf-8')
    assert 'max_percent=(100*max(0.0,cash-trading)/p) if p else 0.0' in api
    assert 'reference_cap=max(0.0,cash-trading)' in api
    assert 'requireEligibility:true' in (root/'templates/trade_sim.html').read_text(encoding='utf-8')
