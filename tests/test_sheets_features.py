"""Synthetic regression tests for navigation, 1H inbox, settings and safe publication."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_google_sheets_master import fake_master
from google_sheets_master import SHEETS, parse_master
from kairos_sheets_features import alert_inbox, prepare_changes, SettingsError, save_changes, mark_alert_read

def demo_master():
    raw=fake_master()
    ctrl=raw[SHEETS['control']]
    ctrl.extend([['Reserva QF',10],['USDT operativo',40],['Capital contable estimado',62],['aprobado_por','TEST'],['reemplaza_snapshot','TEST-000'],['origen','TEST'],['comentario','TEST']])
    p=raw[SHEETS['parameters']]
    p.extend([
      ['CICLO','O3_BTC_PROCEEDS_FRACTION',.3,'number','fraction','APROBADO','OPERATIVO','test'],
      ['CICLO','O3_USDT_PROCEEDS_FRACTION',.7,'number','fraction','APROBADO','OPERATIVO','test'],
    ])
    return raw

class CapitalAllocationTargetsTests(unittest.TestCase):
    def test_edit_liquidity_and_trading_percentages_atomically_without_balances(self):
        raw=demo_master()
        prior=deepcopy(raw)
        writes, state=prepare_changes(raw,'capital_targets',[
            {'segment':'Liquidez','target':.25},
            {'segment':'Trading','target':.15},
        ],evidence='Aprobación targets capital histórico 2026')
        changed={(name,row,col):val for name,row,col,val in writes}
        rows=raw[SHEETS['integral']]
        liq_i=next(i for i,r in enumerate(rows) if r[0]=='Liquidez')
        trad_i=next(i for i,r in enumerate(rows) if r[0]=='Trading')
        assert changed['integral',liq_i,1]==37.5
        assert changed['integral',trad_i,1]==22.5
        assert all(name=='integral' and col==1 for name,row,col,v in writes)
        assert raw==prior
        assert state['snapshot']['trading_real_fixed_USDT']==10
        assert state['snapshot']['physical_total_USDT']==50
        assert state['parameters']['STRUCTURAL_USDT_TARGET']['value']==.4
        assert next(x for x in state['integral']['segments'] if x['name']=='Trading')['target_usdt']==22.5

    def test_reject_partial_reallocation_sum_and_unauthorized_segment(self):
        with self.assertRaisesRegex(SettingsError,'sumar 100%'):
            prepare_changes(demo_master(),'capital_targets',[
                {'segment':'Liquidez','target':.50}],evidence='Aprobación targets 2026')
        with self.assertRaisesRegex(SettingsError,'no editable'):
            prepare_changes(demo_master(),'capital_targets',[
                {'segment':'Lost · realizado','target':.15}],evidence='Aprobación targets 2026')
        with self.assertRaisesRegex(SettingsError,'entre 0% y 100%'):
            prepare_changes(demo_master(),'capital_targets',[
                {'segment':'Trading','target':1.1}],evidence='Aprobación targets 2026')

    def test_frontend_and_source_contract(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        js=(root/'static/settings_master.js').read_text()
        html=(root/'templates/settings.html').read_text()
        assert 'portfolio_goals' in js and 'portfolio_goals' in html
        assert 'ReservaTrading (objetivo)' in js
        assert 'deben sumar' in js
        assert "'capital_targets'" in (root/'app.py').read_text()


class PortfolioGoalManagementTests(unittest.TestCase):
    @staticmethod
    def group_set(*,portfolio=(.7,.3),tiers=(.65,.30,.05),liquidity=(.7,.2,.1),t2=(0,.7,.3)):
        return [{'group':'portfolio','crypto':portfolio[0],'liquidity':portfolio[1]},
                {'group':'tiers','T1':tiers[0],'T2':tiers[1],'T3':tiers[2]},
                {'group':'liquidity','usdt':liquidity[0],'balancer':liquidity[1],'trading':liquidity[2]},
                {'group':'custody','tier':'T1','hodl':.4,'core':.3,'exchange':.3},
                {'group':'custody','tier':'T2','hodl':t2[0],'core':t2[1],'exchange':t2[2]},
                {'group':'custody','tier':'T3','hodl':0,'core':0,'exchange':1}]

    def test_one_atomic_target_plan_and_no_real_balances(self):
        from kairos_sheets_features import portfolio_goals_data, GOAL_LIQ_KEYS
        raw=demo_master();previous=deepcopy(raw)
        entries=self.group_set()
        patches,result=prepare_changes(raw,'portfolio_goals',entries,evidence='Nueva politica de gestión del portafolio')
        after={(name,row,col):v for name,row,col,v in patches}
        self.assertEqual(raw,previous)
        self.assertEqual(sum(result['targets'].values()),1.0)
        self.assertAlmostEqual(sum(result['targets'][token] for token,tier in result['tiers'].items() if tier=='T1'),.65)
        self.assertAlmostEqual(sum(result['targets'][token] for token,tier in result['tiers'].items() if tier=='T2'),.30)
        self.assertEqual(result['custody_policy']['T2'],[0,.7,.3])
        self.assertEqual(result['snapshot']['physical_total_USDT'],50)
        self.assertEqual(result['snapshot']['trading_real_fixed_USDT'],10)
        self.assertTrue(any(name=='integral' for name,row,col,value in patches))
        self.assertTrue(all(name!='liquidity' for name,row,col,value in patches))
        for key in GOAL_LIQ_KEYS.values():self.assertIn(key,result['parameters'])
        updated=portfolio_goals_data({**raw, **{}})
        self.assertFalse(updated['liquidity_mix_published'])

    def test_bad_sums_and_missing_rows_fail_closed(self):
        for kwargs in ({'portfolio':(.5,.3)}, {'tiers':(.5,.4,.09)}, {'liquidity':(.7,.2,.2)}, {'t2':(0,.8,.3)}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(SettingsError,'100%'):
                    prepare_changes(demo_master(),'portfolio_goals',self.group_set(**kwargs),evidence='Aprobación explícita de cambios')
        with self.assertRaisesRegex(SettingsError,'6 grupos'):
            prepare_changes(demo_master(),'portfolio_goals',self.group_set()[:-1],evidence='Aprobación explícita de cambios')

    def test_ui_separate_liquidity_and_previous_balance_floors(self):
        root=Path(__file__).resolve().parents[1]
        js=(root/'static/settings_master.js').read_text()
        html=(root/'templates/settings.html').read_text()
        assert 'portfolio_goals' in js and 'Objetivos de gestión' in html
        assert 'collectGoals' in js and 'goalRead' in js
        assert 'liquidity_mix_published' in js
        assert "if body.get('section')=='portfolio_goals'" in (root/'app.py').read_text()
        assert '02_POSICIONES' not in html.split('data-tab="portfolio_goals"')[0]


class BellSheetTests(unittest.TestCase):
    def fixture(self):
        runs=[['corrida_id','ejecutado_utc','ejecutado_lima','marco'],['r1','2026-10-17T12:00:00Z','', '1H'],['r2','2026-10-17T12:00:00Z','','4H']]
        cols=['evento_id','corrida_id','creado_utc','token','mercado','marco','tipo_alerta','estado_evento','spot_usdt','nivel_usdt','distancia_pct','rsi14','rsi_sma14','stoch_k','stoch_d','regla_clave','certificacion','usdt_preparar','balancer_libre','accion_sugerida','clave_senal']
        def event(a,run,token,act,when):
            row=['']*len(cols)
            for k,v in [('evento_id',a),('corrida_id',run),('creado_utc',when),('token',token),('marco','1H'),('estado_evento','WATCH'),('certificacion','NO_CERTIFICADA'),('accion_sugerida',act)]:row[cols.index(k)]=v
            return row
        events=[cols,event('a','r1','ETH','SEGUIMIENTO; NO ORDEN','2026-10-17T12:15:00Z'),
                   event('b','r1','LINK','ESPERAR; NO ORDEN','2026-10-17T12:18:00Z'),
                   event('c','r2','BTC','NO CORRESPONDE 4H','2026-10-17T12:30:00Z')]
        receipts=[['evento_id','leido_utc','origen_lectura','estado','marco'],['a','2026-10-17T13:00:00Z','KairosWeb','LEIDO','1H']]
        return {'runs':runs,'events':events,'receipts':receipts}
    def test_only_unread_1h_events_displayed(self):
        result=alert_inbox(self.fixture())
        assert result['unread_count']==0
        assert result['records']==[]  # WATCH / NO ORDEN must never enter the bell
    def test_all_historical_unread_when_no_receipts(self):
        data=self.fixture();data['receipts']=data['receipts'][:1]
        result=alert_inbox(data)
        assert result['records']==[]  # even unread WATCH records are not actions

class SettingsTests(unittest.TestCase):
    def test_valid_reallocation_of_target(self):
        raw=demo_master()
        rows,validated=prepare_changes(raw,'targets',[
            {'token':'BTC','target':.19,'tier':'T1'},
            {'token':'ETH','target':.16,'tier':'T1'}],evidence='Aprobación de objetivos 2026')
        assert validated['targets']['BTC']==.19
        assert validated['targets']['ETH']==.16
        assert rows
        assert parse_master(raw)['targets']['BTC']==.2  # no mutation
    def test_targets_sum_must_stay_100(self):
        with self.assertRaisesRegex(SettingsError,'100%'):
            prepare_changes(demo_master(),'targets',[{'token':'BTC','target':.1,'tier':'T1'}],evidence='Aprobación 2026')
    def test_units_keep_snapshot_cost_consistency(self):
        _,state=prepare_changes(demo_master(),'units',[
            {'token':'ETH','hodl':0,'core':.5,'exchange':1,'investment_total':3}
        ],evidence='Fill confirmado y conciliado',as_of_date='2026-10-17')
        assert state['snapshot']['holdings_total']['ETH']==1.5
        assert state['cost_basis']['ETH']==2
    def test_units_require_date_and_evidence(self):
        with self.assertRaises(SettingsError):
            prepare_changes(demo_master(),'units',[{'token':'ETH','hodl':0,'core':0,'exchange':1,'investment_total':1}],evidence='Cambio 123')
    def test_liquidity_reconciled_without_qf_double_count(self):
        _,state=prepare_changes(demo_master(),'liquidity',[{'venue':'Binance','usdt':50}],evidence='Ajuste conciliado 2026',as_of_date='2026-10-17')
        assert state['snapshot']['physical_total_USDT']==60
        assert state['snapshot']['trading_real_fixed_USDT']==10
    def test_custody_policy_must_sum_one(self):
        with self.assertRaisesRegex(SettingsError,'100%'):
            prepare_changes(demo_master(),'tier_custody',[{'tier':'T1','hodl':.3,'core':.3,'exchange':.3}],evidence='Política aprobada')
    def test_o5_pair_can_be_updated_with_sum_100(self):
        _,state=prepare_changes(demo_master(),'parameters',[
          {'key':'O5_BTC_PROCEEDS_FRACTION','value':.4},
          {'key':'O5_USDT_PROCEEDS_FRACTION','value':.6}],evidence='Aprobación del usuario 2026')
        assert state['parameters']['O5_BTC_PROCEEDS_FRACTION']['value']==.4
    def test_o5_mismatch_blocked(self):
        with self.assertRaisesRegex(SettingsError,'100%'):
            prepare_changes(demo_master(),'parameters',[{'key':'O5_BTC_PROCEEDS_FRACTION','value':.5}],evidence='Prueba diferencia')
    def test_pivots_never_certified_by_admin_save(self):
        _,state=prepare_changes(demo_master(),'pivots',[{'token':'BTC','o1':110}],evidence='Pivote observado pendiente')
        assert state['wave_pivots']['BTC']['waves']['o1']['status']=='PROPUESTO'
        assert state['o2_levels']['levels']['BTC']['state']=='REFERENCIA_HISTORICA'
    def test_forbidden_key_rejected(self):
        with self.assertRaisesRegex(SettingsError,'protegido'):
            prepare_changes(demo_master(),'parameters',[{'key':'BTC_NEVER_SELL','value':False}],evidence='Prueba de seguridad')
    def test_no_negative(self):
        with self.assertRaises(SettingsError):
            prepare_changes(demo_master(),'liquidity',[{'venue':'Binance','usdt':-20}],evidence='Caja inválida',as_of_date='2026-10-17')

class WriteTransactionTests(unittest.TestCase):
    def test_commit_is_versioned_and_audited_in_one_batch(self):
        master=demo_master();calls=[];newid=[None]
        sheets={'01_CONTROL':100,'02_POSICIONES':101,'10_HISTORIAL':102,'18_SETTINGS_AUDITORIA':103}
        def stub_api(method,suffix,**kwargs):
            assert method=='POST' and suffix==':batchUpdate'
            requests=kwargs['payload']['requests']
            calls.append(requests)
            history=[x for x in requests if 'appendCells' in x and x['appendCells']['sheetId']==102]
            assert len(history)==1
            newid[0]=history[0]['appendCells']['rows'][0]['values'][0]['userEnteredValue']['stringValue']
            return {'spreadsheetId':'TEST'}
        def reread(force=False):
            return {'control':{'snapshot_id':newid[0]},
                    'homologation':{'status':'CURRENT','source':'25_HOMOLOGACION_HISTORIAL'}}
        with patch('kairos_sheets_features._remote_data',return_value=master), \
             patch('kairos_sheets_features._sheet_ids',return_value=sheets), \
             patch('kairos_sheets_features._api',side_effect=stub_api), \
             patch('google_sheets_master.get_state',side_effect=reread):
            result=save_changes({'expected_snapshot_id':'TEST-001','section':'targets',
                     'entries':[{'token':'BTC','tier':'T1','target':.19},
                                {'token':'ETH','tier':'T1','target':.16}],
                     'evidence':'Aprobación de objetivos para auditoría'})
        assert len(calls)==1 and result['status']=='OK'
        sheetids=[r['appendCells']['sheetId'] for r in calls[0] if 'appendCells' in r]
        assert set(sheetids)=={102,103,2005002501}
        assert any('addSheet' in x and x['addSheet']['properties']['title']=='25_HOMOLOGACION_HISTORIAL' for x in calls[0])
        assert result['previous_snapshot_id']=='TEST-001'
        assert result['snapshot_id']==newid[0]

    def test_read_receipt_only_for_1h(self):
        data=BellSheetTests().fixture()
        calls=[]
        def stub_api(method,suffix,**kwargs):
            calls.append(kwargs['payload']['requests'])
            return {}
        with patch('kairos_sheets_features.read_ranges',return_value=data), \
             patch('kairos_sheets_features._sheet_ids',return_value={'17_ALERTAS_LECTURAS':104}), \
             patch('kairos_sheets_features._api',side_effect=stub_api):
            assert mark_alert_read('b')['status']=='OK'
            with self.assertRaisesRegex(SettingsError,'1H'):
                mark_alert_read('c')
        assert len(calls)==1
        assert calls[0][0]['appendCells']['sheetId']==104

class NavTests(unittest.TestCase):
    def test_no_modes_page_and_central_nav(self):
        root=Path(__file__).resolve().parents[1]
        base=(root/'templates/base.html').read_text()
        app=(root/'app.py').read_text()
        assert "'/modes','Modos Kairos'" not in base
        assert "@app.route('/modes')" not in app
        assert not (root/'templates/modes.html').exists()
        assert 'nav_modes' in base and 'ENABLED_MODE_SLUGS' in app
    def test_gear_and_bell_present_in_shared_layout(self):
        base=(Path(__file__).resolve().parents[1]/'templates/base.html').read_text()
        assert 'bell-open' in base and 'settings_page' in base

