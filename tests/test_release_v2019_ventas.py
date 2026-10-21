from pathlib import Path
R=Path(__file__).resolve().parents[1]

def test_release_v2019_identity_and_preserved_functions():
    source=(R/'app.py').read_text()
    assert "APP_VERSION = '2.0.27'" in source
    assert "'portfolio_unrealized_chart':" in source
    assert "'sales_optimizer_engine':" in source
    assert "'sales_optimizer_ui':" in source
    assert "'buy_postweight_color_ui':" in source
    assert "'SELL_REST_MINIMIZE_SQUARED_PP_DRIFT'" in source
    assert "request.args.get('usdt_pct')" in source
    assert (R/'static/sales_optimizer.js').exists()
