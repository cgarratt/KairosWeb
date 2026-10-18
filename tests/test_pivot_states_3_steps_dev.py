"""Client and backend triple statuses must gate Purchases but not ordinary Sales."""
from test_buy_weekly_policy_v207 import make_weeks
from buy_weekly_policy import select_buy_impulse
from cl_validation import review_wave, sign_review
from test_sheets_features import demo_master
from kairos_sheets_features import SettingsError, prepare_changes
from google_sheets_master import SHEETS
from wave_pivots import wave_row
import pytest

def pair():
    weeks=make_weeks()
    draft=select_buy_impulse(weeks)
    assert not draft['eligible'] and draft['reason']=='EXTREMOS_ND_EN_MASTER'
    return weeks,draft['anchors']['low'],draft['anchors']['high']

def registered(low, high, low_state, high_state):
    return {'cycle_low':low['price'],'cl_date':low['date'],'cl_status':low_state,
            'waves':{'o1':{'price':high['price'],'date':high['date'],'status':high_state}}}

def test_published_proposed_and_validated_allowed_in_simulation():
    weeks,low,high=pair()
    for a,b in [('PROPUESTO','VALIDADO'),('VALIDADO','PROPUESTO'),('PROPUESTO','PROPUESTO')]:
        res=select_buy_impulse(weeks,registered(low,high,a,b))
        assert res['eligible'] and res['status']=='PROPUESTO_SIMULACION'
        assert res['operational_blocked'] and res['simulation_only']
    for a,b in [('VALIDADO','VALIDADO'),('VALIDADO','CONFIRMADO'),('CONFIRMADO','VALIDADO'),('CONFIRMADO','CONFIRMADO')]:
        assert select_buy_impulse(weeks,registered(low,high,a,b))['eligible']
    altered=registered(low,high,'CONFIRMADO','VALIDADO')
    altered['waves']['o1']['price']=high['price']+.15
    assert not select_buy_impulse(weeks,altered)['eligible']

def test_wave_high_review_checks_bullish_impulse_not_bearish_followup():
    weeks,low,high=pair()
    report=review_wave(weeks,high['price'],high['date'],'o1')
    assert report['validated'] and report['status']=='VALIDADO'
    assert not review_wave(weeks,high['price'],low['date'],'o1')['validated']

def test_wave_three_step_and_proof_required(monkeypatch):
    monkeypatch.setenv('KAIROS_SESSION_SECRET','a_very_long_32_character_secret_for_test_only')
    raw=demo_master()
    b=raw[SHEETS['pivots']][1]
    b.extend([None]*27)
    b[3]=200.;b[4]='2026-01-05'
    snapshot=next(r[1] for r in raw[SHEETS['control']] if r and r[0]=='snapshot_id')
    with pytest.raises(SettingsError,match='primero publica VALIDADO'):
        prepare_changes(raw,'pivots',[{'token':'BTC','o1_status':'CONFIRMADO'}],evidence='Confirmación no permitida')
    with pytest.raises(SettingsError,match='evidencia MCP'):
        prepare_changes(raw,'pivots',[{'token':'BTC','o1_status':'VALIDADO'}],evidence='Cambio no acreditado')
    proof=sign_review('BTC|o1',200.,'2026-01-05',snapshot)
    edits,updated=prepare_changes(raw,'pivots',[{'token':'BTC','o1_status':'VALIDADO','o1_review_proof':proof}],evidence='Alta validación MCP')
    assert ('pivots',1,18,'VALIDADO') in edits
    b[18]='VALIDADO'
    edits,after=prepare_changes(raw,'pivots',[{'token':'BTC','o1_status':'CONFIRMADO'}],evidence='Certificación humana')
    assert ('pivots',1,18,'CONFIRMADO') in edits
    b[18]='CONFIRMADO'
    with pytest.raises(SettingsError,match='inmutable'):
        prepare_changes(raw,'pivots',[{'token':'BTC','o1_status':'PROPUESTO'}],evidence='Cambio ilegal')

def test_wave_legacy_states_display_as_proposed_and_validated():
    row=['BTC']+[None]*26
    row[3]=150;row[4]='2026-05-05';row[18]='ESTIMADO';row[26]='VALIDADO_TECNICAMENTE';row[1]=50;row[2]='2026-01-01'
    result=wave_row(row)
    assert result['cl_status']=='VALIDADO' and result['waves']['o1']['status']=='PROPUESTO'

def test_one_global_mcp_button_no_per_token_validation_buttons():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    html=(root/'templates/settings.html').read_text()
    js=(root/'static/settings_master.js').read_text()
    assert html.count('id="settings-preliminary"')==1
    assert 'settings-cl-review-all' not in html
    assert 'Verificar CL 1W' not in html
    assert 'Verificar CL 1W' not in js
    assert 'reviewUnconfirmedToken' in js
    assert "'/api/settings/pivots/technical-review?'" in js
    assert "if(rec[field]==='CONFIRMADO')continue" in js
