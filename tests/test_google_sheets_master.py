import pytest
"""Contract tests for Google Sheets. All data below are SYNTHETIC, not balances."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import google_sheets_master as gs

TARGETS={'BTC':.2,'ETH':.15,'SOL':.15,'LINK':.1,'HYPE':.1,'HBAR':.05,
         'SUI':.05,'ONDO':.05,'PUMPFUN':.05,'PLUME':.05,'VIRTUAL':.025,'PEPE':.025}

def fake_master():
    ctrl=[['Campo','Valor','Instrucción']]
    values={'snapshot_id':'TEST-001','fecha_corte':'2026-10-16','estado_publicacion':'PUBLICADO',
            'publicado_utc':datetime.now(timezone.utc).isoformat(),'schema_version':'5.0.0',
            'Liquidez física':50, 'Costo abierto cripto':12,
            'ordenes_activas_declaradas':'0','fills_pendientes_registro_declarados':'0'}
    ctrl += [[k,v] for k,v in values.items()]
    params=[['Módulo','Clave estable','Valor','Tipo','Unidad','Estado','Ámbito','Fuente','Nota']]
    setting={'SNAPSHOT_PROVIDER':'GOOGLE_SHEETS','BTC_NEVER_SELL':True,'FRESH_DATA_FAIL_CLOSED':True,
             'DRIFT_BAND_PP':1,'STRUCTURAL_USDT_TARGET':.4,'C1_BAG_FRACTION_P':.15,'C2_BAG_FRACTION_P':.1,
             'QF_MARGIN_CAP_PER_POSITION':.25,'QF_ACCOUNT_RISK_PER_TRADE':.025,'QF_ACCOUNT_RISK_TOTAL':.1,
             'RISK_REWARD_MIN':2,'MAX_OPEN_POSITIONS':4,'MAX_LEVERAGE':5,
             'O5_BTC_PROCEEDS_FRACTION':.3,'O5_USDT_PROCEEDS_FRACTION':.7,
             'BSI_PROVIDER':'BINANCE_SPOT_MCP_4H_SYNC',
             'HYPE_MACRO_PROVIDER':'HYPERLIQUID_SPOT_HYPE_USDC_MCP',
             'BALANCER_RESERVE_FORMULA':'MAX(0,USDT_TOTAL-0.25*P-QF_REAL)',
             'BALANCER_NOMINAL_REFERENCE_P':.05,'SLIDER_MAX_SIMULATED_USDT_TARGET':.7}
    params+=[['TEST',k,v,'bool' if isinstance(v,bool) else 'number' if isinstance(v,(float,int)) else 'string','',
              'REFERENCIA_NO_TOPE' if k=='BALANCER_NOMINAL_REFERENCE_P' else 'APROBADO_SIMULACION' if k=='SLIDER_MAX_SIMULATED_USDT_TARGET' else 'APROBADO',
              'OPERATIVO','TEST'] for k,v in setting.items()]
    pos=[['Token Kairos','Mercado MCP','Tier','Target cripto %','HODL unidades','Core unidades','Exchange unidades','Total unidades (calc)','Costo prom. USDT','Costo abierto USDT (calc)','Corte','Fuente declarada','Validación total','Unidades totales declaradas']]
    for s,t in TARGETS.items():pos.append([s,'PUMP' if s=='PUMPFUN' else s,'T1' if t>=.1 else 'T2' if t==.05 else 'T3',t,0,0,1,1,1,1,'2026-10-16','TEST','OK',1])
    liq=[['Venue','USDT físico','Clasificación','Corte','Fuente'],['Binance',40,'OPERATIVO'],['Quantfury',10,'TRADING_QF'],['TOTAL LIQUIDEZ',50],['RESERVA TRADING QF',10],['USDT OPERATIVO',40],['Total informado por usuario',50],['Diferencia de conciliación',0]]
    custody=[['Tier','HODL %','Core %','Exchange %','Validación'],['T1',.4,.3,.3,'OK'],['T2',0,.3,.7,'OK'],['T3',0,0,1,'OK']]
    pivots=[['Token','Cycle Low USDT','Fecha CL','O1 USDT','Fecha O1','O2 USDT','Fecha O2','O3 USDT','O4 USDT','O5 USDT','Fib38.2','C1','C2','Fib78.2','Estado del pivote','Fuente','Certificado']]
    pivots += [[s,None,None,None,None,None,None,None,None,None,None,.5,.4,None,'REFERENCIA_HISTORICA','TEST'] for s in TARGETS]
    bsi=[['Token','Ancla hist','Quote','Venue','Fecha','Baseline','Fecha baseline','HWM','SELL pendiente','Estado','Fuente','MCP Open','MCP Close','UTC','MCP BSI','Estado MCP']]
    bsi += [[s,1,'USDT','Binance','2026-10-05',None,None,None,None,'HISTORICO_NO_ACCIONABLE','TEST',1,.9,'2026-10-17T00:00:00Z',0,'INFORMATIVE_ONLY'] for s in TARGETS]
    integral=[['Segmento','Objetivo USDT','Registrado histórico USDT'],['Capital inicial histórico',150],['Pérdidas realizadas acumuladas',20],['Capital vivo declarado',130],
              ['HODL + Core',60,40],['Exchange',30,35],['Liquidez',45,30],['Trading',15,5],['Lost · realizado',0,20]]
    validations=[['Control','Resultado']]+[[k,'OK'] for k in ('12 tokens Kairos presentes','Targets cripto suman 100%','Custodia suma unidades','Total USDT conciliado','Reserva QF sin duplicar')]+[['Estado publicación','PUBLICADO']]
    raw={'control':ctrl,'positions':pos,'liquidity':liq,'custody':custody,'orders':[['header']], 'fills':[['header']],
         'pivots':pivots,'integral':integral,'bsi':bsi,'validation':validations,'parameters':params}
    return {a1:raw[name] for name,a1 in gs.SHEETS.items()}

class SheetsContract(unittest.TestCase):
    def test_approved_snapshot_and_no_fallback(self):
        state=gs.parse_master(fake_master())
        self.assertEqual(state['control']['snapshot_id'],'TEST-001')
        self.assertEqual(len(state['tokens']),12)
        self.assertEqual(state['snapshot']['physical_total_USDT'],50)
        self.assertEqual(state['snapshot']['trading_real_fixed_USDT'],10)
        self.assertEqual(state['parameters']['O5_BTC_PROCEEDS_FRACTION']['value'],.3)
        self.assertEqual(state['o2_levels']['status'],'REFERENCE_NOT_ACTIONABLE')
    def test_unpublished_rejected(self):
        raw=fake_master();raw[gs.SHEETS['control']][3][1]='BORRADOR'
        with self.assertRaisesRegex(gs.SheetDataError,'PUBLICADO'):gs.parse_master(raw)
    def test_negative_custody_rejected(self):
        raw=fake_master();raw[gs.SHEETS['positions']][2][6]=-2
        with self.assertRaises(gs.SheetDataError):gs.parse_master(raw)
    def test_unreconciled_cash_rejected(self):
        raw=fake_master();raw[gs.SHEETS['liquidity']][1][1]=80
        with self.assertRaises(gs.SheetDataError):gs.parse_master(raw)
    def test_targets_rejected(self):
        raw=fake_master();raw[gs.SHEETS['positions']][2][3]=.7
        with self.assertRaisesRegex(gs.SheetDataError,'100%'):gs.parse_master(raw)
    def test_wrong_o5_ratio_rejected(self):
        raw=fake_master()
        p=raw[gs.SHEETS['parameters']]
        for r in p:
            if len(r)>2 and r[1]=='O5_BTC_PROCEEDS_FRACTION':r[2]=.7
        with self.assertRaisesRegex(gs.SheetDataError,'sum to 100%'):gs.parse_master(raw)
    def test_orders_not_silently_ignored(self):
        raw=fake_master();raw[gs.SHEETS['orders']].append(['Binance','order-id'])
        with self.assertRaisesRegex(gs.SheetDataError,'reconcile'):gs.parse_master(raw)
    def test_real_master_editorial_footnotes_are_not_orders(self):
        raw=fake_master()
        # Actual Google Sheet uses a caption in cell A58 of each operational tab.
        for section,caption in (
            ('orders','Al poblar órdenes: identificador único (Venue, Order ID), separar órdenes abiertas de fills, y reservar USDT antes de cualquier propuesta BUY.'),
            ('fills','Jamás derivar fills de niveles tocados, simulaciones o LIMIT colocadas. Propuestas no son ejecución.'),
        ):
            rows=raw[gs.SHEETS[section]]
            rows.extend([[] for _ in range(53)])
            rows.append([caption])
        state=gs.parse_master(raw)
        self.assertEqual(state['control']['snapshot_id'],'TEST-001')

    def test_footnote_with_operational_data_still_rejected(self):
        raw=fake_master()
        raw[gs.SHEETS['orders']].append([
            'Al poblar órdenes: identificador único (Venue, Order ID), separar órdenes abiertas de fills, y reservar USDT antes de cualquier propuesta BUY.',
            'order-123'])
        with self.assertRaisesRegex(gs.SheetDataError,'reconcile'):
            gs.parse_master(raw)

    def test_closed_reconciled_historical_orders_and_fills_are_not_pending(self):
        raw=fake_master()
        raw[gs.SHEETS['orders']].append([
            'Binance','ord-001','ETH','BUY','LIMIT','O2',100,1,1,100,0,'FILLED',
            '2026-10-15T12:00:00Z','2026-10-15T12:01:00Z','EXCHANGE','CONCILIADO'])
        raw[gs.SHEETS['fills']].append([
            'Binance','ord-001','trade-001','ETH','BUY','2026-10-15T12:01:00Z',
            1,0,'ETH',1,100,0,'Exchange',True,'EXCHANGE','Binance|ord-001|trade-001'])
        result=gs.parse_master(raw)
        self.assertEqual(result['historical_ledger_counts'],{'orders':1,'fills':1})
        self.assertEqual(result['snapshot']['holdings_total']['ETH'],1) # no double count

    def test_unsettled_or_duplicate_ledger_rejected(self):
        raw=fake_master()
        row=['Binance','ord-001','ETH','BUY','LIMIT','O2',100,1,0,100,0,
             'OPEN','2026-10-15T12:00:00Z','','EXCHANGE','CONCILIADO']
        raw[gs.SHEETS['orders']].append(row)
        with self.assertRaisesRegex(gs.SheetDataError,'reconcile'):
            gs.parse_master(raw)
        raw[gs.SHEETS['orders']][-1][11]='FILLED'
        raw[gs.SHEETS['orders']].append(list(raw[gs.SHEETS['orders']][-1]))
        with self.assertRaisesRegex(gs.SheetDataError,'duplicate'):
            gs.parse_master(raw)

    def test_unrecognized_single_cell_is_not_silently_ignored(self):
        raw=fake_master()
        raw[gs.SHEETS['fills']].append(['A new, unrecognized instruction that must not hide a real fill'])
        with self.assertRaisesRegex(gs.SheetDataError,'reconcile'):
            gs.parse_master(raw)

    def test_safe_diagnostic_codes_do_not_disclose_secrets(self):
        code=gs.public_failure_code(gs.SheetDataError('Google service account JSON invalid'))
        self.assertEqual(code,'GOOGLE_CREDENTIALS_INVALID_JSON')
        self.assertEqual(gs.public_failure_code(gs.SheetDataError('Google Sheets HTTP 403')),'GOOGLE_SHEETS_HTTP_403')

    def test_missing_credential_data_error_no_cached_state(self):
        with patch.dict(gs.os.environ,{},clear=True):
            with self.assertRaises(gs.SheetDataError):gs._remote_data()
    def test_configuration_status_gate(self):
        raw=fake_master()
        for r in raw[gs.SHEETS['parameters']]:
            if len(r)>5 and r[1]=='RISK_REWARD_MIN':r[5]='PENDIENTE'
        with self.assertRaisesRegex(gs.SheetDataError,'not approved'):gs.parse_master(raw)
    def test_bad_bsi_sync_archive(self):
        raw=fake_master();raw[gs.SHEETS['bsi']][1][13]='2026-10-16T00:00:00Z'
        with self.assertRaisesRegex(gs.SheetDataError,'synchronized'):gs.parse_master(raw)

if __name__=='__main__':unittest.main()

# B07/B08: verification is tied to current publication and does not rewrite inventories.
def test_homologation_marks_previous_snapshot_and_cash_stale():
    raw=fake_master()
    raw[gs.HOMOLOGATION_RANGE]=[
        ['Control','Resultado','Fuente primaria / brecha'],
        ['01_CONTROL PUBLICADO','PASS','KAIROS-OLD-SNAPSHOT'],
        ['03_LIQUIDEZ QF UNA VEZ','PASS','USDT físico 28130 / QF 7225'],
    ]
    result=gs.parse_master(raw)
    review=result['homologation']
    assert review['status']=='STALE'
    assert review['checked_against_snapshot']=='TEST-001'
    assert {i['code'] for i in review['issues']}=={'SNAPSHOT_REFERENCE_STALE','LIQUIDITY_REFERENCE_STALE'}
    assert result['snapshot']['physical_total_USDT']==50


def test_homologation_current_control_is_not_stale():
    raw=fake_master()
    raw[gs.HOMOLOGATION_RANGE]=[
        ['Control','Resultado','Fuente primaria / brecha'],
        ['01_CONTROL PUBLICADO','PASS','TEST-001'],
        ['03_LIQUIDEZ QF UNA VEZ','PASS','USDT físico 50 / QF 10'],
    ]
    review=gs.parse_master(raw)['homologation']
    assert review['status']=='CURRENT'
    assert review['issues']==[]


def test_homologation_missing_is_unverified_and_not_certified():
    raw=fake_master()
    review=gs.parse_master(raw)['homologation']
    assert review['status']=='NOT_VERIFIED'
    assert review['issues'][0]['code']=='HOMOLOGATION_UNAVAILABLE'


def test_historical_reference_keeps_provenance_without_inventing_year():
    raw=fake_master()
    rows=raw[gs.SHEETS['integral']]
    rows[-1].extend([None]*(6-len(rows[-1])))
    rows[-1][5]='Referencia integral del 16/10; actualizar tras reconciliar'
    result=gs.parse_master(raw)
    assert result['integral']['reference_date_label']=='16/10 (año no indicado en la hoja)'
    assert result['integral']['source_note'].startswith('Google Sheets 08_INTEGRAL')

# v2.0.31 — append-only homologation by published snapshot (synthetic figures only).
def _certified_master():
    raw=fake_master()
    state=gs.parse_master(raw)
    ctrl=state['control']
    cert=gs.homologation_certificate(state,ctrl['snapshot_id'],ctrl['publicado_utc'],
                                    '2026-10-22T20:00:00Z')
    raw[gs.HOMOLOGATION_HISTORY_RANGE]=[gs.HOMOLOGATION_HEADERS,cert]
    return raw


def test_current_ledger_supersedes_old_control_without_rewriting_it():
    raw=_certified_master()
    raw[gs.HOMOLOGATION_RANGE]=[
        ['Control','Resultado','Fuente primaria / brecha'],
        ['01_CONTROL PUBLICADO','PASS','KAIROS-OLD-SNAPSHOT'],
        ['03_LIQUIDEZ QF UNA VEZ','PASS','USDT físico 28130 / QF 7225'],
    ]
    state=gs.parse_master(raw)
    h=state['homologation']
    assert h['status']=='CURRENT'
    assert h['source']=='25_HOMOLOGACION_HISTORIAL'
    assert h['certification_scope']=='BASE_CONTABLE'
    assert 'BSI_SELL_BASELINE_HWM' in h['pending_controls']
    assert state['snapshot']['physical_total_USDT']==50


def test_homologation_ledger_snapshot_change_must_revalidate():
    raw=_certified_master()
    for row in raw[gs.SHEETS['control']]:
        if row and row[0]=='snapshot_id':row[1]='TEST-002'
    result=gs.parse_master(raw)['homologation']
    assert result['status']=='STALE'
    assert 'SNAPSHOT_REFERENCE_STALE' in {item['code'] for item in result['issues']}


def test_homologation_ledger_qf_imbalance_invalidates_certificate():
    raw=_certified_master()
    raw[gs.HOMOLOGATION_HISTORY_RANGE][-1][10]=0
    result=gs.parse_master(raw)['homologation']
    assert result['status']=='STALE'
    assert 'LIQUIDITY_REFERENCE_STALE' in {item['code'] for item in result['issues']}


def test_homologation_latest_entry_wins_not_old_matching_snapshot():
    raw=_certified_master()
    old=list(raw[gs.HOMOLOGATION_HISTORY_RANGE][-1])
    old[0]='TEST-OLD'
    raw[gs.HOMOLOGATION_HISTORY_RANGE].append(old)
    result=gs.parse_master(raw)['homologation']
    assert result['status']=='STALE'


def test_certificate_fails_if_critical_validation_not_pass():
    state=gs.parse_master(fake_master())
    state['validation']['Reserva QF sin duplicar']='PENDIENTE'
    with __import__('pytest').raises(gs.SheetDataError):
        gs.homologation_certificate(state,'TEST-001',state['control']['publicado_utc'],
                                   '2026-10-22T20:00:00Z')


def test_manual_homologation_is_append_only_and_idempotent():
    import kairos_sheets_features as sf
    raw=fake_master()
    state=gs.parse_master(raw)
    proof={'status':'CURRENT','source':'25_HOMOLOGACION_HISTORIAL',
           'pending_controls':['PIVOTES_CERTIFICACION']}
    seen=[]
    def check_api(method,suffix,**kwargs):
        seen.append(kwargs.get('payload'))
        return {'spreadsheetId':'test'}
    with patch.object(sf,'_remote_data',return_value=raw),\
         patch.object(sf,'_sheet_ids',return_value={'01_CONTROL':1355071856}),\
         patch.object(sf,'_api',side_effect=check_api),\
         patch.object(gs,'get_state',return_value={**state,'homologation':proof}):
        result=sf.homologate_current_snapshot('TEST-001')
    assert result['status']=='OK'
    assert result['already_homologated'] is False
    requests=seen[0]['requests']
    assert {'addSheet','updateCells','appendCells'}=={next(iter(r)) for r in requests}
    assert requests[-1]['appendCells']['sheetId']==2005002501
    assert all('02_POSICIONES' not in str(req) and '03_LIQUIDEZ' not in str(req) for req in requests)

    state['homologation']=proof
    with patch.object(sf,'_remote_data',return_value=raw),\
         patch.object(sf,'_api',side_effect=AssertionError('unexpected write')):
        # Patch parser output to represent a previously homologated read.
        with patch.object(sf,'parse_master',return_value=state):
            again=sf.homologate_current_snapshot('TEST-001')
    assert again['already_homologated'] is True

# v2.0.33 — Fresh homologation must be read, identity-bound and diagnosable.
def test_v2033_readiness_reports_missing_ledger_without_writing():
    import kairos_sheets_features as sf
    raw=fake_master()
    state=gs.parse_master(raw)
    with patch.object(gs,'get_state',return_value=state), \
         patch.object(sf,'_sheet_ids',return_value={'01_CONTROL':123}), \
         patch.object(sf,'_api',side_effect=AssertionError('GET-only readiness must not write')):
        status=sf.homologation_readiness()
    assert status['status']=='PENDING'
    assert status['snapshot_id']=='TEST-001'
    assert status['ledger_present'] is False
    assert status['ledger_tab']=='25_HOMOLOGACION_HISTORIAL'
    assert status['recommended_action']=='HOMOLOGATE_CURRENT_SNAPSHOT'


def test_v2033_readiness_uses_current_ledger_no_write():
    import kairos_sheets_features as sf
    state=gs.parse_master(_certified_master())
    assert state['homologation']['status']=='CURRENT'
    with patch.object(gs,'get_state',return_value=state), \
         patch.object(sf,'_sheet_ids',return_value={'25_HOMOLOGACION_HISTORIAL':300}), \
         patch.object(sf,'_api',side_effect=AssertionError('readiness cannot mutate Sheets')):
        status=sf.homologation_readiness()
    assert status['status']=='CURRENT'
    assert status['recommended_action']=='NONE'
    assert status['ledger_present'] is True


def test_v2033_reader_snapshot_conflict_blocks_homologation_write():
    import kairos_sheets_features as sf
    raw=fake_master()
    with patch.object(sf,'_remote_data',return_value=raw), \
         patch.object(sf,'_api',side_effect=AssertionError('must not write after mismatch')):
        with pytest.raises(sf.HomologationWorkflowError) as failure:
            sf.homologate_current_snapshot('OTHER-SNAPSHOT')
    assert failure.value.code=='HOM_SNAPSHOT_CHANGED'
    assert failure.value.phase=='VALIDATION'


def test_v2033_writer_403_reports_actionable_safe_code():
    import kairos_sheets_features as sf
    raw=fake_master()
    with patch.object(sf,'_remote_data',return_value=raw), \
         patch.object(sf,'_sheet_ids',return_value={'01_CONTROL':1}), \
         patch.object(sf,'_api',side_effect=sf.SettingsError('Google Sheets HTTP 403')):
        with pytest.raises(sf.HomologationWorkflowError) as failure:
            sf.homologate_current_snapshot('TEST-001')
    assert failure.value.code=='HOM_WRITER_FORBIDDEN'
    assert failure.value.phase=='WRITE'
    assert failure.value.write_may_have_committed is False
    assert 'Editor' in str(failure.value)


def test_v2033_post_write_read_fails_closed_and_requires_manual_check():
    import kairos_sheets_features as sf
    raw=fake_master()
    with patch.object(sf,'_remote_data',return_value=raw), \
         patch.object(sf,'_sheet_ids',return_value={'01_CONTROL':1}), \
         patch.object(sf,'_api',return_value={'replies':[{}, {}, {}]}), \
         patch.object(gs,'get_state',side_effect=gs.SheetDataError('Google Sheets HTTP 503')):
        with pytest.raises(sf.HomologationWorkflowError) as failure:
            sf.homologate_current_snapshot('TEST-001')
    assert failure.value.code=='HOM_WRITE_UNVERIFIED'
    assert failure.value.phase=='POST_WRITE_READ'
    assert failure.value.write_may_have_committed
    assert 'antes de reintentar' in str(failure.value)


def test_v2033_homologation_diagnostics_and_units_contract_in_release():
    from pathlib import Path
    from jinja2 import Environment
    root=Path(__file__).resolve().parents[1]
    app=(root/'app.py').read_text()
    mcp=(root/'static/mcp_settings.js').read_text()
    html=(root/'templates/balancer.html').read_text()
    assert "APP_VERSION = '2.0.34'" in app
    assert "/api/settings/homologation-status" in app
    assert 'HOM_WRITER_MISSING' in app
    assert 'write_may_have_committed' in app
    assert 'HOM_WRITE_UNVERIFIED' in (root/'kairos_sheets_features.py').read_text()
    assert 'HOM_WRITER_FORBIDDEN' in (root/'kairos_sheets_features.py').read_text()
    assert 'master-homologation-readiness' in (root/'templates/settings.html').read_text()
    assert 'master-homologation-check' in (root/'templates/settings.html').read_text()
    assert 'getHomologationReadiness()' in mcp
    start=html.index('<section class="panel span-6"><h2>4. Candidatos de venta')
    end=html.index('</section>',start)+len('</section>')
    payload=type('Payload',(),{'sells':[{'token':'HBAR','value':100,'weight':.07,'target':.05,'units':17857.38754194}]})()
    out=Environment().from_string(html[start:end]).render(payload=payload)
    assert '<th>Unidades</th>' in out
    assert '17,857.39' in out
    assert '17,857.38754194' not in out
    assert 'TOTAL VENTAS USDT' in out
