"""Acceptance: O3/O5 splits are sourced from published Master and are distinct."""
from pathlib import Path
from unittest.mock import patch
import pytest
ROOT=Path(__file__).resolve().parents[1]

def test_independent_o3_o5_from_approved_master():
    source=(ROOT/'app.py').read_text()
    assert "approved_numeric('O3_BTC_PROCEEDS_FRACTION')" in source
    assert "approved_numeric('O3_USDT_PROCEEDS_FRACTION')" in source
    assert "approved_numeric('O5_BTC_PROCEEDS_FRACTION')" in source
    assert "approved_numeric('O5_USDT_PROCEEDS_FRACTION')" in source
    assert "raise SheetDataError('12_PARAMETROS_KAIROS: reparto BTC/USDT O3/O5 debe sumar 100%" in source
    tmpl=(ROOT/'templates/forecast.html').read_text()
    assert 'id="btc-share"' not in tmpl
    assert 'btcShareO3' in tmpl and 'btcShareO5' in tmpl
    assert "Portfolio.allocateSales" in tmpl
    assert "Portfolio.allocateBuys" in tmpl
    assert "id=\"o3-master-share\"" in tmpl and "id=\"o5-master-share\"" in tmpl
    assert "data-forecast-stage" in tmpl
    assert "fetch(" not in tmpl


def test_forecast_price_line_uses_spot_not_wave_pivot():
    view=(ROOT/'templates/forecast.html').read_text()
    assert "const position=fc.tokens.find(t=>t.token===choice.token)" in view
    assert "validSpot?[...prices,spot]:prices" in view
    assert "'data-spot-reference':'binance-mcp'" in view
    assert 'fc.generated_at' in view
    assert 'fc-spot-line' in view
    assert 'drawCurve(result)' in view
    from jinja2 import Environment
    Environment().parse(view)
