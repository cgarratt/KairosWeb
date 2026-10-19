from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_identity_and_health_markers_in_release():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert "APP_VERSION = '2.0.13'" in app
    assert "'buy_p1p2_anchors':" in app and "'buy_p1p2_policy':" in app
    template=(ROOT/'templates/trade_sim.html').read_text(encoding='utf-8')
    engine=(ROOT/'buy_weekly_policy.py').read_text(encoding='utf-8')
    assert 'P1 · mínimo semanal' in template and 'P2 · máximo semanal' in template
    assert 'pivot-anchor-dot' in template
    assert 'def select_p1_p2_buy_impulse(' in engine
    assert 'P1_ADMITIDO_P2_MAXIMO_SEMANAL_POSTERIOR' in engine

def test_pivot_anchor_status_semaphore_and_no_execution():
    template=(ROOT/'templates/trade_sim.html').read_text(encoding='utf-8')
    assert 'pivot-propuesto{background:#e54357}' in template
    assert 'pivot-validado{background:#f0a92b}' in template
    assert 'pivot-confirmado{background:#20bb73}' in template
    engine=(ROOT/'buy_weekly_policy.py').read_text(encoding='utf-8')
    assert "'simulation_only':True" in engine
    assert "'operational_blocked':True" in engine
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    assert "'/api/orders/place'" not in app and "'/api/orders/cancel'" not in app
