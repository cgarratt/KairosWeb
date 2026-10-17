"""KairosWeb 1.5.0: numeric Forecast policies and fail-closed O1 preview."""
import unittest
from datetime import date,timedelta
from unittest.mock import patch
from forecast_fibo_policy import TRANCHE_KEYS, DEFAULTS, defaults_from_master, ForecastAllocationError
from test_sheets_features import demo_master
from test_pivot_preload_v12 import archive_rows
from google_sheets_master import SHEETS
from kairos_sheets_features import prepare_changes, settings_data, SettingsError
from pivot_candidates import add_uncertified_daily_extrema
from pivot_preload import archive_candidates
from pathlib import Path

class ForecastTranches(unittest.TestCase):
 def test_sixteen_individual_keys_and_defaults(self):
  self.assertEqual(sum(map(len,TRANCHE_KEYS.values())),16)
  self.assertEqual(DEFAULTS['o2'],(0,60,40,0))
  self.assertEqual(DEFAULTS['o3'],(40,30,20,10))
  self.assertEqual(DEFAULTS['o5'],(20,20,30,30))
  with patch('kairos_sheets_features._remote_data',return_value=demo_master()):
   p=settings_data()['sections']['parameters']
  self.assertEqual(len([x for x in p if x['key'] in {v for keys in TRANCHE_KEYS.values() for v in keys}]),16)
  self.assertFalse(any(x['key']=='O5_STAGED_TRANCHES' for x in p))
 def test_first_save_creates_complete_approved_numeric_stage(self):
  raw=demo_master();old=len(raw[SHEETS['parameters']])
  writes,state=prepare_changes(raw,'parameters',[
   {'key':'FORECAST_O2_FIB_382_PCT','value':20},
   {'key':'FORECAST_O2_FIB_500_PCT','value':40}],evidence='Usuario aprobó reparto O2')
  group=[state['parameters'][k] for k in TRANCHE_KEYS['o2']]
  self.assertEqual([x['value'] for x in group],[20,40,40,0])
  self.assertTrue(all(x['status']=='APROBADO_SIMULACION' and x['type']=='number' for x in group))
  self.assertEqual(len(raw[SHEETS['parameters']]),old)
  self.assertEqual(len({row for name,row,col,_ in writes if name=='parameters' and col==1}),4)
  self.assertNotIn('FORECAST_O2_FIB_382_PCT',[r[1] for r in raw[SHEETS['parameters']] if len(r)>1])
 def test_numeric_priority_prevents_legacy_shadow(self):
  params={'FORECAST_O5_FIB_ALLOCATION':{'value':'25,25,25,25','status':'APROBADO_SIMULACION'}}
  params.update({k:{'value':v,'status':'APROBADO_SIMULACION'} for k,v in zip(TRANCHE_KEYS['o5'],[20,20,30,30])})
  self.assertEqual(defaults_from_master(params)['o5'],[20,20,30,30])
  del params[TRANCHE_KEYS['o5'][2]]
  with self.assertRaises(ForecastAllocationError):defaults_from_master(params)
 def test_reject_invalid_percent_or_partial_edits(self):
  with self.assertRaises(SettingsError):
   prepare_changes(demo_master(),'parameters',[{'key':TRANCHE_KEYS['o3'][0],'value':101}],evidence='Aprobación de porcentaje')
  with self.assertRaises(SettingsError):
   prepare_changes(demo_master(),'parameters',[{'key':TRANCHE_KEYS['o3'][0],'value':35}],evidence='Aprobación de porcentaje')
  with self.assertRaises(SettingsError):
   prepare_changes(demo_master(),'parameters',[{'key':'BTC_NEVER_SELL','value':False}],evidence='Regla no autorizada')

class PivotPreliminary(unittest.TestCase):
 def test_o1_fast_path_uses_utc_weeks_and_is_not_certified(self):
  rows=archive_rows()
  rows[1][5]='2026-07-01';rows[1][6]=None;rows[1][7]=None
  record=archive_candidates(rows)[0]
  days=[]
  for mon,hi in [(date(2026,7,6),72000),(date(2026,9,21),87395.67)]:
   for k in range(7):
    d=mon+timedelta(days=k)
    days.append({'open_utc':d.isoformat()+'T00:00:00Z','high':str(hi if k==0 else hi-1000)})
  result=add_uncertified_daily_extrema(record,{'status':'OK','records':days})
  self.assertEqual(result['o1'],87395.67)
  self.assertEqual(result['o1_date'],'2026-09-21')
  self.assertFalse(result['o1_certified'])
  self.assertIn('NO certificado',result['warning'])
 def test_endpoint_code_fetches_closed_spot_without_cycle_scanner(self):
  src=(Path(__file__).parents[1]/'app.py').read_text()
  section=src.split("if request.args.get('o1_only') == '1':",1)[1].split("        if token=='HYPE':",1)[0]
  self.assertIn('get_kairos_ohlcv',section)
  self.assertNotIn("'get_kairos_cycle_phase'",section)
  self.assertIn('review_result(record)',section)
if __name__=='__main__':unittest.main()
