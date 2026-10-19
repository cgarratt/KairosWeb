from pathlib import Path


def test_compras_single_maximum_and_slider_budget_independent_of_eligibility():
    root = Path(__file__).resolve().parents[1]
    html = (root / 'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'Máximo disponible para Compras' in html
    assert 'id="max-buy-metric"' in html
    assert 'id="max-buy-slider"' in html
    assert 'Compra simulada elegible' not in html
    assert "◇ Compra simulada' if mode.slug=='compras'" in html
    assert "el('allocation-metric').textContent=dollar(referenceCapacity)" in html
    assert 'id="selected-buy-budget"' in html
    assert 'id="actual-buy-spend"' in html
    assert 'id="unallocated-buy-budget"' in html
    assert 'maxBuyCash=Math.max(0,Number(source.current.reference_cap ?? (cash-trading)))' in html
    assert 'const referenceCapacity=Math.max(0,Math.min(desired,maxBuyCash));' in html
    assert "el('selected-buy-budget').textContent=dollar(referenceCapacity)" in html
    assert 'sim.stageBudgets.forEach' in html
    assert 'sim.unallocated' in html
    assert 'purchase-metrics' in html


def test_backend_maximum_is_cash_less_qf_not_structural_spend():
    root = Path(__file__).resolve().parents[1]
    api = (root / 'app.py').read_text(encoding='utf-8')
    assert 'max_percent=(100*max(0.0,cash-trading)/p) if p else 0.0' in api
    assert 'reference_cap=max(0.0,cash-trading)' in api
    assert 'requireEligibility:true' in (root/'templates/trade_sim.html').read_text(encoding='utf-8')


def test_fibonacci_title_and_all_three_cells_same_historical_color():
    root = Path(__file__).resolve().parents[1]
    html = (root / 'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'Maestro de Precios - Retrocesos Fibo' in html
    assert 'class="${css}" title="Peso cripto post-compra C${j+1}' in html
    assert html.count('<th>% Peso</th>') == 4
    assert '<td class="${css}" title="${historicalTitle}">${fibPrice(level)}</td>' in html
    assert '<td class="${css}" title="${historicalTitle}">${dollar(amount)}</td>' in html


def test_fibo_percentages_editable_and_local_only():
    root = Path(__file__).resolve().parents[1]
    html = (root / 'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'id="fibo-split-{{ loop.index0 }}"' in html
    assert 'id="fibo-split-reset"' in html
    assert 'id="fibo-split-total"' in html
    assert 'window.KairosPurchaseWeights.rebalance(fiboPercentages,i,value)' in html
    assert 'fiboCustom?window.KairosPurchaseWeights.asFractions(fiboPercentages):null' in html
    assert 'weightsByToken:appliedByToken' in html
    assert 'showFiboControls();paint();' in html
    assert "url_for('static', filename='purchase_weights.js')" in html
    assert (root / 'static/purchase_weights.js').is_file()
