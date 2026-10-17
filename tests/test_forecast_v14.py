"""Simulated-only 4 tranche controls; never mutate canonical Sheets."""
from pathlib import Path
from forecast_fibo_policy import DEFAULTS, STAGE_KEYS, TRANCHE_KEYS, parse_weights, stringify_weights, defaults_from_master, ForecastAllocationError
from forecast_math import derive_reference_anchors
from test_sheets_features import demo_master
from google_sheets_master import SHEETS
from kairos_sheets_features import settings_data, prepare_changes, SettingsError
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

class ForecastPolicyTests(unittest.TestCase):
 def test_defaults(self):
  self.assertEqual(DEFAULTS['o2'],(0,60,40,0))
  self.assertEqual(DEFAULTS['o3'],(40,30,20,10))
  self.assertEqual(DEFAULTS['o5'],(20,20,30,30))
  self.assertEqual(defaults_from_master({'O5_STAGED_TRANCHES':{'status':'APROBADO','value':'20,20,30,30'}})['o5'],[20,20,30,30])
 def test_distributions(self):
  self.assertEqual(parse_weights('20,10.5,49.5,20'),(20,10.5,49.5,20))
  self.assertEqual(stringify_weights([0,20,30,50]),'0,20,30,50')
  for bad in ['10,10,10,10','-1,20,40,41','101,0,0,-1','40,30,30','abc,10,20,70']:
   with self.assertRaises(ForecastAllocationError):parse_weights(bad)
 def test_fibonacci_786(self):
  result=derive_reference_anchors(75,63.2)
  self.assertAlmostEqual(result['ref786'],result['o1']-.786*(result['o1']-result['cycle_low']),places=6)
  self.assertIn('ref782',result) # historical evidence preserved
 def test_new_params_are_virtual_until_admin_save(self):
  raw=demo_master();params=raw[SHEETS['parameters']]
  with patch('kairos_sheets_features._remote_data',return_value=raw):
   data=settings_data()
  row=next(x for x in data['sections']['parameters'] if x['key']=='FORECAST_O3_FIB_1618_PCT')
  self.assertEqual(row['value'],40)
  self.assertEqual(row['type'],'number')
  self.assertEqual(row['status'],'APROBADO_SIMULACION')
  self.assertEqual(len([x for x in data['sections']['parameters'] if x['key'] in TRANCHE_KEYS['o3']]),4)
  self.assertFalse(any(x and len(x)>1 and x[1]=='FORECAST_O3_FIB_1618_PCT' for x in params))
 def test_admin_save_provisions_complete_four_numeric_rows(self):
  raw=demo_master();before=len(raw[SHEETS['parameters']])
  changes,state=prepare_changes(raw,'parameters',[
    {'key':'FORECAST_O3_FIB_1618_PCT','value':30},
    {'key':'FORECAST_O3_FIB_2618_PCT','value':40},
    {'key':'FORECAST_O2_FIB_500_PCT','value':40},
    {'key':'FORECAST_O2_FIB_382_PCT','value':20}],evidence='Simulación aprobada por usuario')
  self.assertEqual(defaults_from_master(state['parameters'])['o3'],[30,40,20,10])
  self.assertEqual(defaults_from_master(state['parameters'])['o2'],[20,40,40,0])
  self.assertEqual(len(raw[SHEETS['parameters']]),before)
  self.assertEqual(len([k for k in TRANCHE_KEYS['o3'] if k in state['parameters']]),4)
  self.assertEqual(len([k for k in TRANCHE_KEYS['o2'] if k in state['parameters']]),4)
  self.assertTrue(any(k=='parameters' and row>=before and col==1 for k,row,col,_ in changes))
  with self.assertRaises(SettingsError):
   prepare_changes(raw,'parameters',[{'key':'FORECAST_O5_FIB_1618_PCT','value':45}],evidence='Config inválida')
 def test_partial_legacy_and_individual_parameters_rejected(self):
  with self.assertRaises(ForecastAllocationError):
   defaults_from_master({'FORECAST_O2_FIB_382_PCT':{'value':10,'status':'APROBADO_SIMULACION'}})
  with self.assertRaises(SettingsError):
   prepare_changes(demo_master(),'parameters',[{'key':'O5_STAGED_TRANCHES','value':'25,25,25,25'}],evidence='Reparto obsoleto')
 def test_expected_html_sections(self):
  s=(ROOT/'templates/forecast.html').read_text()
  self.assertIn('forecast-weights',s)
  self.assertIn('O2C4 · Fib 78.6%',s)
  self.assertIn('25% de P',s)
  self.assertNotIn("custodyShots.push(custodyShot('Post-O5'",s)
  self.assertIn('Composición final Post-O5',s)
