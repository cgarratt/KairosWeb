from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_logos_for_all_tokens_and_alias_only():
    js = (ROOT/'static/settings_master.js').read_text()
    for code in ('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMP','PUMPFUN','PLUME','PEPE','VIRTUAL'):
        assert code+':' in js
    assert 'settingsTokenLabel(rec.token)' in js
    assert "(tab==='units'||tab==='targets')&&entry.token" in js
    assert "img.addEventListener('error'" in js
    assert "else primary.append(el('strong','token-name',entry[rowKey()]));" in js

def test_styles_are_shared_with_dark_mode():
    css=(ROOT/'static/theme.css').read_text()
    assert '.settings-token-identity' in css
    assert '.settings-coin-icon' in css
    assert '.settings-pivot-token' in css
