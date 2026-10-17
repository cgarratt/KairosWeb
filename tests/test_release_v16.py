"""Acceptance tests for KairosWeb 1.6.0 (offline; no production writes)."""
from pathlib import Path
from unittest.mock import patch
import unittest
from google_sheets_master import SHEETS, parse_master
from kairos_sheets_features import settings_data, prepare_changes, SettingsError
from forecast_fibo_policy import TRANCHE_KEYS, defaults_from_master, ForecastAllocationError
from wave_nomenclature import STAGES, LEGACY_O2, canonical
from test_sheets_features import demo_master

ROOT=Path(__file__).resolve().parents[1]

class Kairos160Tests(unittest.TestCase):
    def test_16_canonical_stage_levels_and_historical_alias(self):
        self.assertEqual([p[0] for p in STAGES['O2']],['O2C1','O2C2','O2C3','O2C4'])
        self.assertEqual([p[0] for p in STAGES['O4']],['O4C1','O4C2','O4C3','O4C4'])
        self.assertEqual([p[0] for p in STAGES['O3']],['O3V1','O3V2','O3V3','O3V4'])
        self.assertEqual([p[0] for p in STAGES['O5']],['O5V1','O5V2','O5V3','O5V4'])
        self.assertEqual(LEGACY_O2['C1_FIB50'],'O2C2')
        self.assertEqual(LEGACY_O2['C2_FIB61_8'],'O2C3')
        self.assertEqual(canonical('O2',0),'O2C1')
        with self.assertRaises(ValueError):canonical('O1',1)
    def test_can_parse_master_without_obsolete_budget_fields(self):
        raw=demo_master()
        rows=raw[SHEETS['parameters']]
        rows[:]=[r for r in rows if len(r)<2 or r[1] not in {'C1_BAG_FRACTION_P','C2_BAG_FRACTION_P','ORDINARY_DEFAULT_USDT_TARGET'}]
        state=parse_master(raw)
        self.assertEqual(len(state['tokens']),12)
        self.assertEqual(state['parameters']['STRUCTURAL_USDT_TARGET']['value'],.4)
    def test_settings_only_single_liquidity_target_and_balancer_pp(self):
        with patch('kairos_sheets_features._remote_data',return_value=demo_master()):
            d=settings_data()
        keys={r['key'] for r in d['sections']['parameters']}
        self.assertIn('STRUCTURAL_USDT_TARGET',keys)
        self.assertIn('DRIFT_BAND_PP',keys)
        self.assertNotIn('C1_BAG_FRACTION_P',keys)
        self.assertNotIn('C2_BAG_FRACTION_P',keys)
        self.assertNotIn('ORDINARY_DEFAULT_USDT_TARGET',keys)
        self.assertEqual(len(keys.intersection(k for ids in TRANCHE_KEYS.values() for k in ids)),16)
        src=(ROOT/'static/settings_master.js').read_text()
        self.assertIn("keys:['STRUCTURAL_USDT_TARGET','DRIFT_BAND_PP']",src)
        self.assertNotIn('Liquidez y Balancer\',description',src)
    def test_obsolete_fields_cannot_be_published(self):
        for key in ('C1_BAG_FRACTION_P','C2_BAG_FRACTION_P','ORDINARY_DEFAULT_USDT_TARGET'):
            with self.subTest(key=key):
                with self.assertRaisesRegex(SettingsError,'Parámetro protegido'):
                    prepare_changes(demo_master(),'parameters',[{'key':key,'value':.1}],evidence='Transición canónica aprobada')
    def test_fibo_numeric_splits(self):
        default=defaults_from_master(parse_master(demo_master())['parameters'])
        self.assertEqual(default['o2'],[0,60,40,0])
        self.assertEqual(default['o3'],[40,30,20,10])
        self.assertEqual(default['o5'],[20,20,30,30])
        with self.assertRaises(ForecastAllocationError):
            defaults_from_master({TRANCHE_KEYS['o2'][0]:{'value':15,'status':'APROBADO_SIMULACION'}})
    def test_templates_global_canonical_labels_and_order(self):
        h=(ROOT/'templates/forecast.html').read_text()
        self.assertLess(h.index('Trayectoria hipotética por token'),h.index('Ondas y precios pivote'))
        self.assertLess(h.index('Ondas y precios pivote'),h.index('Asignación USDT para referencias Fibonacci O2'))
        self.assertIn('O2C1 · Fib 38.2%',h)
        self.assertIn('O2C4 · Fib 78.6%',h)
        self.assertIn('O3V3 · Fib 3.618',h)
        self.assertIn('O4C4 · Fib 78.6%',h)
        self.assertIn('O5V4 · Fib 4.618',h)
        self.assertIn('O2C2 · USDT',h)
        self.assertIn('O2C3 · USDT',h)
        self.assertIn('Total compras O2 · USDT',h)
        self.assertNotIn('C1 · 50% precio',h)
        self.assertNotIn('C2 · 61.8% precio',h)
    def test_deploy_slider_only_percentage_and_usdt(self):
        h=(ROOT/'templates/forecast.html').read_text()
        self.assertIn('id="forecast-deploy"',h)
        self.assertIn('id="deploy-label"',h)
        self.assertIn('id="deploy-total"',h)
        for removed in ('deploy-c1','deploy-c2','deploy-balance'):
            self.assertNotIn('id="'+removed+'"',h)
        self.assertNotIn('<small>USDT simulados</small>',h)
        self.assertIn('25% de P',h)
    def test_purchase_mode_four_tranches_and_one_cash_cap(self):
        h=(ROOT/'templates/trade_sim.html').read_text()
        for i in range(4):self.assertIn('id="buy-tranche-'+str(i)+'"',h)
        self.assertNotIn('id="buy-c1-total"',h)
        self.assertNotIn('id="buy-c2-total"',h)
        a=(ROOT/'app.py').read_text()
        self.assertNotIn("approved_numeric('C1_BAG_FRACTION_P')",a)
        self.assertNotIn("approved_numeric('C2_BAG_FRACTION_P')",a)
        self.assertIn('operational_25=.25*p',a)
        self.assertIn('forecast_o2_allocation',a)
    def test_bsi_sell_and_btc_safety_untouched(self):
        a=(ROOT/'app.py').read_text()
        self.assertIn('BTC NEVER SELL',a)
        s=(ROOT/'static/settings_master.js').read_text()
        self.assertNotIn("keys:['C1_BAG_FRACTION_P'",s)
        assert 'O5_BTC_PROCEEDS_FRACTION' in s
    def test_source_docs_do_not_change_snapshot(self):
        names=list(ROOT.glob('data/*.json'))
        self.assertEqual(names,[])

if __name__=='__main__':unittest.main()
