"""CL status pipeline: no silent certification, server-proven weekly technical gate."""
from datetime import date, timedelta
import os
import pytest
from cl_validation import review_cl, sign_review, verify_review
from test_sheets_features import demo_master
from google_sheets_master import SHEETS,parse_master
from kairos_sheets_features import SettingsError,prepare_changes


def test_weekly_validation_5l5r_plus_close_bos():
    monday=date(2026,1,5)
    weeks=[]
    for i in range(23):
        high=30 if i==6 else (35 if i==18 else 10)
        low=1 if i==12 else (6 if i>12 else 5)
        close=31 if i==18 else 8
        weeks.append({'week_start':(monday+timedelta(weeks=i)).isoformat(),
                      'week_end':(monday+timedelta(weeks=i,days=6)).isoformat(),
                      'low_date':(monday+timedelta(weeks=i,days=2)).isoformat(),
                      'high':high,'low':low,'close':close})
    price_date=weeks[12]['low_date']
    result=review_cl(weeks,1,price_date)
    assert result['validated'] and result['status']=='VALIDADO'
    assert result['protected_high']==30
    assert result['bos_week']==weeks[18]['week_start']
    not_bos=[dict(w,close=9) for w in weeks]
    assert not review_cl(not_bos,1,price_date)['validated']
    assert not review_cl(weeks[:-10],1,price_date)['validated']
    assert not review_cl(weeks,1,weeks[11]['low_date'])['validated']


def test_cl_requires_technical_proof_and_two_published_steps(monkeypatch):
    monkeypatch.setenv('KAIROS_SESSION_SECRET','a_very_secure_test_session_secret_for_kairos')
    raw=demo_master()
    snapshot=next(r[1] for r in raw[SHEETS['control']] if r and r[0]=='snapshot_id')
    candidate={'token':'BTC','cycle_low':.2772,'cl_date':'2026-02-01','cl_status':'VALIDADO'}
    with pytest.raises(SettingsError,match='requiere revisión MCP'):
        prepare_changes(raw,'pivots',[candidate],evidence='Validación técnica pendiente en MCP')
    with pytest.raises(SettingsError,match='primero valida'):
        prepare_changes(raw,'pivots',[{**candidate,'cl_status':'CONFIRMADO'}],evidence='Intento confirmar candidato')
    proof=sign_review('BTC',.2772,'2026-02-01',snapshot,now=1700000000)
    assert not verify_review('BTC',.2772,'2026-02-01',snapshot,proof,now=1700000901)
    proof=sign_review('BTC',.2772,'2026-02-01',snapshot)
    assert not verify_review('BTC',.2773,'2026-02-01',snapshot,proof)
    edits,updated=prepare_changes(raw,'pivots',[{**candidate,'cl_review_proof':proof}],
                                  evidence='CL BTC cumple 5L5R y BOS semanal revisado')
    assert ('pivots',1,26,'VALIDADO') in edits
    assert updated['wave_pivots']['BTC']['cl_status']=='VALIDADO'
    # Step 2 occurs only after the technical status is *published* in the Master.
    raw[SHEETS['pivots']][1].extend([None]*27)
    raw[SHEETS['pivots']][1][1]=.2772;raw[SHEETS['pivots']][1][2]='2026-02-01'
    raw[SHEETS['pivots']][1][26]='VALIDADO'
    edits,confirmed=prepare_changes(raw,'pivots',[{'token':'BTC','cl_status':'CONFIRMADO'}],
            evidence='Usuario confirma formalmente el Cycle Low después de revisar estructura semanal')
    assert ('pivots',1,26,'CONFIRMADO') in edits
    assert confirmed['wave_pivots']['BTC']['cl_status']=='CONFIRMADO'
    raw[SHEETS['pivots']][1][26]='CONFIRMADO'
    for mutation in ({'token':'BTC','cycle_low':.25},{'token':'BTC','cl_status':'PROPUESTO'},
                     {'token':'BTC','cl_date':'2026-02-02'}):
        with pytest.raises(SettingsError,match='inmutable'):
            prepare_changes(raw,'pivots',[mutation],evidence='Intento de modificar CL confirmado')


def test_bad_cl_status_from_sheet_is_data_error():
    raw=demo_master()
    raw[SHEETS['pivots']][1].extend([None]*27)
    raw[SHEETS['pivots']][1][26]='CERTIFICADO_AUTOMATICO'
    with pytest.raises(Exception,match='estado no permitido'):
        parse_master(raw)
