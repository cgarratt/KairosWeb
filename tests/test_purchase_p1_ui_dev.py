from pathlib import Path

def test_pivot_prices_visible_in_compras_table():
    root=Path(__file__).resolve().parents[1]
    html=(root/'templates/trade_sim.html').read_text()
    assert '<th>P1 · mínimo semanal</th><th>P2 · máximo semanal</th>' in html
    assert 'anchorCell(p1' in html and 'anchorCell(p2' in html
    assert 'Sin P1 con fecha/precio válidos' in (root/'app.py').read_text()

def test_balance_remains_gate_to_spending():
    s=(Path(__file__).resolve().parents[1]/'static/o2_sequential.js').read_text()
    assert "drift[i].status==='INFRA'" in s
    assert 'maxBalancedSpend' in s
    assert 'Math.min(stageBudget' in s


def test_p1_p2_status_dots_separate_from_fibo_background():
    root=Path(__file__).resolve().parents[1]
    text=(root/'templates/trade_sim.html').read_text()
    for label,color in [('propuesto','#e54357'),('validado','#f0a92b'),('confirmado','#20bb73')]:
        assert f'.pivot-anchor-dot.pivot-{label}{{background:{color}}}' in text
    assert 'anchorCell(p1)' in text and 'anchorCell(p2)' in text
    assert 'P1 · mínimo semanal' in text
    assert 'role="img" aria-label="Pivote ${safeState}"' in text
