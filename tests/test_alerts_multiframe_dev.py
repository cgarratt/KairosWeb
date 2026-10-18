"""Acceptance of the unified 1H/4H/1D notification bell (development, not release)."""
import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kairos_sheets_features import alert_inbox, mark_alert_read, mark_all_alerts_read, SettingsError

COLS=['evento_id','corrida_id','creado_utc','token','mercado','marco','tipo_alerta','estado_evento',
      'spot_usdt','nivel_usdt','distancia_pct','rsi14','rsi_sma14','stoch_k','stoch_d',
      'regla_clave','certificacion','usdt_preparar','balancer_libre','accion_sugerida','clave_senal']
RUNS=['corrida_id','ejecutado_utc','ejecutado_lima','marco']

def fixture():
    runs=[RUNS,['r1','','','1H'],['r4','','','4H'],['rD','','','1D'],['rBad','','','12H']]
    def ev(eid,run,frame,kind,when,**kw):
        d=dict(evento_id=eid,corrida_id=run,marco=frame,tipo_alerta=kind,token='BTC',
               estado_evento='WATCH',certificacion='NO_CERTIFICADA',
               accion_sugerida='Vigilar, NO ORDEN',creado_utc=when,clave_senal=eid)
        d.update(kw)
        return [d.get(k) for k in COLS]
    t='2026-10-17T21:10:00Z'
    return {'runs':runs,'events':[COLS,
        ev('level','r1','1H','NIVEL_PROXIMO',t),
        ev('touch','r1','1H','NIVEL_TOCADO','2026-10-17T21:11:00Z'),
        ev('fill','r1','1H','FILL_PARCIAL','2026-10-17T21:12:00Z'),
        ev('break','r4','4H','BREAK_BAJISTA','2026-10-17T21:13:00Z'),
        ev('struc','r4','4H','NUEVA_ESTRUCTURA','2026-10-17T21:14:00Z'),
        ev('wave','rD','1D','NUEVA_ONDA','2026-10-17T21:15:00Z',token=''),
        ev('bsi','rD','1D','BSI_ACCION','2026-10-17T21:16:00Z',accion_sugerida='SELL no certificado'),
        ev('liq','rD','1D','LIQUIDEZ_CRITICA','2026-10-17T21:17:00Z'),
        ev('wrong','r4','1H','NIVEL_TOCADO','2026-10-17T21:18:00Z'),
        ev('fake','rBad','12H','NUEVA_ONDA','2026-10-17T21:19:00Z')],
        'receipts':[['evento_id','leido_utc','origen_lectura','estado','marco']]}

class InboxTests(unittest.TestCase):
    def test_all_timeframes_and_types_and_not_trade_ready(self):
        result=alert_inbox(fixture())
        self.assertEqual(result['unread_count'],8)
        self.assertEqual(result['timeframe_counts'],{'1H':3,'4H':2,'1D':3})
        self.assertEqual(result['scope'],'UNREAD_1H_4H_1D')
        self.assertEqual({r['kind'] for r in result['records']},
                         {'NIVEL_PROXIMO','NIVEL_TOCADO','FILL_PARCIAL','BREAK_BAJISTA',
                          'NUEVA_ESTRUCTURA','NUEVA_ONDA','BSI_ACCION','LIQUIDEZ_CRITICA'})
        self.assertFalse(any(r['is_trade_ready'] for r in result['records']))
        self.assertEqual(next(r for r in result['records'] if r['id']=='wave')['token'],'PORTAFOLIO')
    def test_filtered_counts_and_bad_filter(self):
        self.assertEqual(alert_inbox(fixture(),timeframe='4h')['unread_count'],2)
        self.assertEqual(alert_inbox(fixture(),timeframe='1d')['unread_count'],3)
        self.assertEqual(alert_inbox(fixture(),timeframe='1H')['unread_count'],3)
        with self.assertRaises(SettingsError):alert_inbox(fixture(),timeframe='12H')
    def test_read_id_and_dedupe_remain_separate_per_frame(self):
        b=fixture()
        b['events'][2][COLS.index('clave_senal')]='common'
        b['events'][4][COLS.index('clave_senal')]='common'
        # Different events and frames should not suppress each other.
        self.assertEqual(alert_inbox(b)['unread_count'],8)
        b['receipts'].append(['wave','2026-10-17T22:00:00Z','KairosWeb','LEIDO','1D'])
        self.assertEqual(alert_inbox(b)['unread_count'],7)
    def test_fill_dedupes_by_event_id_not_generic_signal(self):
        b=fixture()
        extra=list(b['events'][3]);extra[0]='fill-2';b['events'].append(extra)
        self.assertEqual(alert_inbox(b)['unread_count'],9)

class ReceiptTests(unittest.TestCase):
    def test_individual_4h_and_1d_are_append_only_with_correct_timeframe(self):
        b=fixture();calls=[]
        def api(method,suffix,**kwargs):
            calls.append(kwargs['payload']['requests']);return {}
        with patch('kairos_sheets_features.read_ranges',return_value=b),\
             patch('kairos_sheets_features._sheet_ids',return_value={'17_ALERTAS_LECTURAS':17}),\
             patch('kairos_sheets_features._api',side_effect=api):
            self.assertEqual(mark_alert_read('break')['timeframe'],'4H')
            self.assertEqual(mark_alert_read('wave')['timeframe'],'1D')
            with self.assertRaises(SettingsError):mark_alert_read('wrong')
        self.assertEqual(len(calls),2)
        values=[item['userEnteredValue']['stringValue'] for item in calls[1][0]['appendCells']['rows'][0]['values']]
        self.assertEqual(values[-1],'1D')
    def test_mark_all_is_one_batch_with_all_three_timeframes(self):
        b=fixture();calls=[]
        def api(method,suffix,**kwargs):calls.append(kwargs['payload']['requests']);return {}
        with patch('kairos_sheets_features.read_ranges',return_value=b),\
             patch('kairos_sheets_features._sheet_ids',return_value={'17_ALERTAS_LECTURAS':17}),\
             patch('kairos_sheets_features._api',side_effect=api),\
             patch('kairos_sheets_features._bsi_selling_approved',return_value=False):
            self.assertEqual(mark_all_alerts_read()['marked'],8)
        self.assertEqual(len(calls),1)
        rows=calls[0][0]['appendCells']['rows']
        self.assertEqual(sorted(set(r['values'][-1]['userEnteredValue']['stringValue'] for r in rows)),['1D','1H','4H'])
    def test_mark_all_can_filter_only_one_timeframe(self):
        b=fixture();calls=[]
        def api(method,suffix,**kwargs):calls.append(kwargs['payload']['requests']);return {}
        with patch('kairos_sheets_features.read_ranges',return_value=b),\
             patch('kairos_sheets_features._sheet_ids',return_value={'17_ALERTAS_LECTURAS':17}),\
             patch('kairos_sheets_features._api',side_effect=api),\
             patch('kairos_sheets_features._bsi_selling_approved',return_value=False):
            self.assertEqual(mark_all_alerts_read('4H')['marked'],2)
        self.assertEqual(len(calls[0][0]['appendCells']['rows']),2)

class UiTests(unittest.TestCase):
    def test_single_bell_and_visible_tfs_and_individual_ack(self):
        root=Path(__file__).resolve().parents[1]
        js=(root/'static/alert_bell.js').read_text()
        html=(root/'templates/base.html').read_text()
        self.assertEqual(html.count('id="bell-open"'),1)
        self.assertIn("'/api/alerts/read'",js)
        self.assertIn('alert-timeframe',js)
        self.assertIn('1H, 4H y 1D',html)
        self.assertIn('alert_bell.js',html)

if __name__=='__main__':unittest.main()

@unittest.skipUnless(importlib.util.find_spec('flask'), 'Flask no está instalado en este entorno; validar HTTP en Render')
class HttpContractTests(unittest.TestCase):
    def setUp(self):
        import app as webapp
        self.webapp=webapp
        self._env=patch.dict('os.environ',{'KAIROS_WEB_PASSWORD':'test-pass','KAIROS_WEB_USER':'kairos'})
        self._env.start()
        import base64
        raw=base64.b64encode(b'kairos:test-pass').decode('ascii')
        self.client=webapp.app.test_client()
        self.h={'Authorization':'Basic '+raw,'Origin':'http://localhost'}

    def tearDown(self):
        self._env.stop()

    def test_get_1h_4h_1d_optional_filter(self):
        with patch.object(self.webapp,'unread_alerts',return_value={'status':'OK','unread_count':0,'records':[]}) as stub:
            for tf in ['1H','4H','1D']:
                rsp=self.client.get('/api/alerts/unread?timeframe='+tf,headers=self.h)
                self.assertEqual(rsp.status_code,200)
                stub.assert_called_with(timeframe=tf)
            rsp=self.client.get('/api/alerts/unread',headers=self.h)
            self.assertEqual(rsp.status_code,200)
            stub.assert_called_with(timeframe=None)

    def test_post_readall_optional_scope(self):
        with patch.object(self.webapp,'mark_all_alerts_read',return_value={'status':'OK','marked':3}) as stub:
            for body,expected in [({},None),({'timeframe':'4H'},'4H')]:
                rsp=self.client.post('/api/alerts/read-all',json=body,headers=self.h)
                self.assertEqual(rsp.status_code,200)
                stub.assert_called_with(timeframe=expected)
