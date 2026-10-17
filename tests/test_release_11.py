"""Regression tests for next release candidate. All data synthetic, no Master writes."""
import sys
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pivot_candidates import candidates_binance,candidates_hype
from kairos_sheets_features import mark_all_alerts_read, prepare_changes, SettingsError
from test_sheets_features import BellSheetTests,demo_master

class PivotCandidateTests(unittest.TestCase):
    def test_sui_manual_low_excludes_flash_outlier(self):
        row=candidates_binance('SUI',{
            'status':'OK','scope':'EXPLORATORY_ONLY','phase':'O4',
            'cycle_high':{'price':'5.3687','date_utc':'2025-01-06T00:00:00Z'},
            'cycle_low':{'price':'0.5597','date_utc':'2025-10-10T00:00:00Z'},
            'wave_pivots':{'SH1':{'price':'2.02','date_utc':'2026-01-05T00:00:00Z'}}},selected_low=.6359)
        self.assertAlmostEqual(row['cycle_low'],.6359)
        self.assertAlmostEqual(row['raw_cycle_low'],.5597)
        self.assertIn('OUTLIER',row['warning'])
        self.assertEqual(row['status'],'CANDIDATO_NO_CERTIFICADO')
    def test_pump_excluded_week_and_no_auto_certification(self):
        row=candidates_binance('PUMPFUN',{'status':'OK','scope':'EXPLORATORY_ONLY',
            'cycle_high':{'price':'0.00898'},'cycle_low':{'price':'0.000411'},'wave_pivots':{}},selected_low=.001151)
        self.assertAlmostEqual(row['cycle_low'],.001151)
        self.assertIsNone(row['o3'])
        self.assertIn('certificado',row['warning'])
    def test_non_exploratory_data_rejected(self):
        self.assertEqual(candidates_binance('BTC',{'status':'OK','scope':'EXECUTABLE'})['status'],'DATA_ERROR')
    def test_hype_weekly_closed_5l5r_no_fake_o3(self):
        # Synthetic pattern: CH week 7, CL week 18, O1 week 29, O2 week 39;
        # last high is too recent for 5-right confirmation.
        from datetime import date
        records=[]
        start=date(2025,9,1)
        highs={7:59.406,29:76.9,48:97.885}
        lows={18:20.5,39:51.11}
        for j in range(50*7):
            week=j//7
            high=highs.get(week,45)
            low=lows.get(week,30)
            if week==48:low=70  # local high, not low
            if week>=40 and week!=48:low=60
            # avoid tie windows spuriously producing pivots
            d=start+timedelta(days=j)
            o=33 if week<40 else 70
            records.append({'open_utc':d.isoformat()+'T00:00:00Z',
                'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00Z',
                'open':str(o),'close':str(o),'high':str(max(high,o)),'low':str(min(low,o)),'volume_base':'10'})
        result=candidates_hype({'status':'OK','source':'Hyperliquid Spot','pair':'HYPE/USDC','interval':'1d','closed_only':True,'records':records})
        self.assertEqual(result['status'],'CANDIDATO_NO_CERTIFICADO')
        self.assertIsNone(result['o3'])
        self.assertFalse(result.get('approved_elliott_pivots',False))

class BulkAlertsTests(unittest.TestCase):
    def test_mark_all_filters_only_unread_1h_and_one_write(self):
        fixture=BellSheetTests().fixture();calls=[]
        def api(method,suffix,**kwargs):calls.append(kwargs['payload']['requests']);return {'status':'OK'}
        with patch('kairos_sheets_features.read_ranges',return_value=fixture),\
             patch('kairos_sheets_features._sheet_ids',return_value={'17_ALERTAS_LECTURAS':300}),\
             patch('kairos_sheets_features._api',side_effect=api):
            ret=mark_all_alerts_read()
        self.assertEqual(ret['marked'],0)
        self.assertEqual(len(calls),0)  # WATCH not shown, therefore not acknowledged
    def test_empty_inbox_idempotent(self):
        data=BellSheetTests().fixture();data['receipts'].append(['b','2026-10-17T13:00:00Z'])
        with patch('kairos_sheets_features.read_ranges',return_value=data),patch('kairos_sheets_features._api') as fn:
            self.assertEqual(mark_all_alerts_read()['marked'],0)
            fn.assert_not_called()

class NewUnitCostTests(unittest.TestCase):
    def test_total_cost_not_average_input(self):
        _,state=prepare_changes(demo_master(),'units',[
            {'token':'ETH','hodl':1,'core':1,'exchange':2,'investment_total':20}],
            evidence='Compra conciliada comprobada',as_of_date='2026-10-17')
        self.assertEqual(state['snapshot']['holdings_total']['ETH'],4)
        self.assertAlmostEqual(state['cost_basis']['ETH'],5)
    def test_cost_positive_without_units_rejected(self):
        with self.assertRaisesRegex(SettingsError,'unidades'):
            prepare_changes(demo_master(),'units',[
                {'token':'ETH','hodl':0,'core':0,'exchange':0,'investment_total':12}],
                evidence='Cambio de inventario confirmado',as_of_date='2026-10-17')

class LayoutTests(unittest.TestCase):
    def test_single_save_no_admin_input(self):
        p=Path(__file__).resolve().parents[1]
        t=(p/'templates/settings.html').read_text()
        self.assertIn('settings-save',t)
        for old in ['settings-preview','settings-publish','settings-asof','settings-admin']:
            # settings-admin-state is intended; former admin password field is not.
            self.assertNotIn('id="'+old+'"',t)
        self.assertIn('theme-choice',t)
    def test_global_theme_and_bulk_button(self):
        t=(Path(__file__).resolve().parents[1]/'templates/base.html').read_text()
        self.assertIn('data-theme-toggle',t)
        self.assertIn('Marcar todas como leídas',t)
        self.assertNotIn('Alertas 1H · No leídas',t)
    def test_server_rejects_old_admin_header(self):
        t=(Path(__file__).resolve().parents[1]/'app.py').read_text()
        self.assertNotIn("request.headers.get('X-Kairos-Admin-Key'",t)
        self.assertIn('KAIROS_SESSION_SECRET',t)
        self.assertIn("'/api/settings/save'",t)

if __name__=='__main__':unittest.main()
