from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_shared_theme_styles_cover_notes_and_charts():
    css=(ROOT/'static/theme.css').read_text(encoding='utf-8')
    for selector in (
        '.callout.warn', '.sim-warn', '.fc-warning', '.integral-warning',
        '.liq-step', '.liq-labels > div', '.sim-metric', '.fc-kpi',
        '.integral-stat', '.settings-msg', '.token-compare-track',
        '.tier-track', '.fc-tables tfoot td', '.wave-value-row',
    ):
        assert selector in css, selector
    assert '--surface-warn-text:#ffe6b3' in css
    assert ':root[data-theme="dark"]' in css

def test_dark_fix_does_not_change_financial_logic():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert 'APP_VERSION = "1.7.0"' in app
    assert 'snapshot_master_2026' not in app
