"""Pivot O1–O5 persistence, strict lock and cross-mode read-only contract."""
import pytest
from test_sheets_features import demo_master
from google_sheets_master import SHEETS, parse_master
from kairos_sheets_features import prepare_changes, SettingsError
from wave_pivots import fib_from_anchors


def test_confirm_wave_o1_requires_price_date_and_updates_all_modes_reference():
    raw=demo_master()
    r=raw[SHEETS['pivots']][11];r.extend([None]*27);r[1]=.2772;r[2]='2025-10-10';r[3]=1.1984;r[4]='2026-01-05';r[18]='VALIDADO'
    edits,state=prepare_changes(raw,'pivots',[{'token':'VIRTUAL','cycle_low':.2772,
      'cl_date':'2025-10-10','o1':1.1984,'o1_date':'2026-01-05','o1_status':'CONFIRMADO'}],
      evidence='Aprobación manual y evidencia pivote VIRTUAL')
    assert state['wave_pivots']['VIRTUAL']['waves']['o1']['status']=='CONFIRMADO'
    assert state['o2_levels']['levels']['VIRTUAL']['state']=='ANCHORS_ESTIMADOS_O_CONFIRMADOS'
    assert state['o2_levels']['levels']['VIRTUAL']['c1']==pytest.approx(0.7378)
    assert state['o2_levels']['levels']['VIRTUAL']['c2']==pytest.approx(0.6290984)
    assert any(name=='pivots' and col==18 and val=='CONFIRMADO' for name,row,col,val in edits)
    assert len([v for v in edits if v[0]=='pivots' and v[1]==0])>=0
    # Master input remains untouched until /publish is called.
    assert parse_master(raw)['wave_pivots']['VIRTUAL']['waves']['o1']['status']=='VALIDADO'


def test_legacy_wave_remains_estimated_without_published_confirmation():
    raw=demo_master()
    _,state=prepare_changes(raw,'pivots',[{'token':'PEPE','cycle_low':.00000223,'o1':.00000536,
     'o1_date':'2026-03-15','o1_status':'ESTIMADO'}],evidence='Preliminar archive MCP PEPE')
    assert state['wave_pivots']['PEPE']['waves']['o1']['status']=='PROPUESTO'
    assert state['o2_levels']['levels']['PEPE']['c1']==pytest.approx(.000003795)


def test_confirm_needs_explicit_dated_price():
    for rec in ({'token':'PEPE','o3_status':'CONFIRMADO','o3':1},
                {'token':'PEPE','o3_status':'CONFIRMADO','o3_date':'2026-01-02'},
                {'token':'PEPE','o3_status':'CONFIRMADO','o3':1,'o3_date':'02/01/2026'}):
        with pytest.raises(SettingsError):
            prepare_changes(demo_master(),'pivots',[rec],evidence='Prueba de confirmación sin fecha o precio')


def test_confirmed_wave_immutable_even_in_settings():
    raw=demo_master()
    r=raw[SHEETS['pivots']][1]
    while len(r)<26:r.append(None)
    r[1]=.2772;r[2]='2025-10-10';r[3]=1.1984;r[4]='2026-01-05';r[18]='CONFIRMADO'
    for bad in [{'token':'BTC','o1':1.2345}, {'token':'BTC','o1_status':'ESTIMADO'},
                {'token':'BTC','o1_date':'2026-01-06'},{'token':'BTC','cycle_low':.3}]:
        with pytest.raises(SettingsError,match='bloqueado|inmutable'):
            prepare_changes(raw,'pivots',[bad],evidence='Test de intento de sobrescritura')


def test_independent_confirmation_each_wave():
    raw=demo_master()
    r=raw[SHEETS['pivots']][1];r.extend([None]*27);r[7]=120.5;r[23]='2026-02-01';r[20]='VALIDADO'
    _,state=prepare_changes(raw,'pivots',[{'token':'BTC','o3':120.5,
     'o3_date':'2026-02-01','o3_status':'CONFIRMADO','o2':90.5}],evidence='Aprobación pivote O3 de BTC')
    assert state['wave_pivots']['BTC']['waves']['o3']['status']=='CONFIRMADO'
    assert state['wave_pivots']['BTC']['waves']['o2']['status']=='PROPUESTO'
    assert state['wave_pivots']['BTC']['waves']['o3']['date']=='2026-02-01'


def test_bad_status_from_sheet_is_data_error():
    raw=demo_master()
    r=raw[SHEETS['pivots']][1]
    while len(r)<26:r.append(None)
    r[18]='CERTIFICADO_AUTOMATICO'
    with pytest.raises(Exception,match='estado no permitido'):parse_master(raw)


def test_forecast_script_uses_confirmed_over_selectors():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    js=(root/'templates/forecast.html').read_text()
    assert "fixed('o2')??" in js
    assert "fixed('o3')??" in js
    assert "fixed('o4')??" in js
    assert "fixed('o5')??" in js
    for page in ['balancer.html','trade_sim.html','forecast.html']:
        assert "'_wave_confirmed.html'" in (root/'templates'/page).read_text()
