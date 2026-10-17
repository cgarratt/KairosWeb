"""v1.9 acceptance: UI labels and no false claims about historical levels."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_header_single_version():
    template=(ROOT/'templates/base.html').read_text()
    assert '<p>v{{ master }}</p>' in template
    assert 'Google Sheets Master · Spot por MCP' not in template
    assert 'APP_VERSION = "1.9.0"' in (ROOT/'app.py').read_text()

def test_balancer_liquidity_short_cards_keep_values():
    template=(ROOT/'templates/balancer.html').read_text()
    for label in ['Presupuesto Compras','Reserva Balancer','Reserva Trading']:
        assert '<span>'+label+'</span>' in template
    assert 'Presupuesto compras O2/O4 · máximo 25% P' not in template
    assert 'Reserva Trading QF' not in template
    assert '100*buy_budget/cash' in template
    assert '100*bal/cash' in template
    assert '100*trading/cash' in template
    assert 'Las bolsas nominales exceden el saldo físico' in template

def test_forecast_sem_signal_only_prices_not_budgets():
    s=(ROOT/'templates/forecast.html').read_text()
    assert 'id="fibo-level-legend"' in s
    assert "const LevelStatus=window.KairosForecastLevelStatus" in s
    assert 'data-level-status="${state.status}"' in s
    assert 'const levelsHtml=levels.map((level,j)=>{' in s
    assert '<td>${money(shares[j]*a)}</td>' in s
    assert 'no certifica toques históricos post-O1' in s
    assert 'postO1Verified===true' in (ROOT/'static/forecast_level_status.js').read_text()
