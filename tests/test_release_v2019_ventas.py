from pathlib import Path
R=Path(__file__).resolve().parents[1]

def test_release_v2019_identity_and_preserved_functions():
    source=(R/'app.py').read_text()
    assert "APP_VERSION = '2.0.35'" in source
    assert "'portfolio_unrealized_chart':" in source
    assert "'sales_optimizer_engine':" in source
    assert "'sales_optimizer_ui':" in source
    assert "'buy_postweight_color_ui':" in source
    assert "'SELL_REST_MINIMIZE_SQUARED_PP_DRIFT'" in source
    assert "request.args.get('usdt_pct')" in source
    assert (R/'static/sales_optimizer.js').exists()


def test_sales_proposal_without_redundant_weight_table():
    view=(R/'templates/trade_sim.html').read_text()
    assert 'Pesos antes / objetivo / después (12 tokens)' not in view
    assert 'sell-weight-body' not in view
    assert 'id="sim-body"' in view and 'sell-plan-status' in view
    assert 'p.after_pct.toFixed(2)' in view
    from jinja2 import Environment
    Environment().parse(view)
