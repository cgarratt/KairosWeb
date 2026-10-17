"""Security, compatibility and UI acceptance for KairosWeb 1.3.0."""
from datetime import timezone
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kairos_sheets_features import alert_inbox, alert_category
from pivot_candidates import candidates_binance, add_uncertified_daily_extrema
ROOT=Path(__file__).resolve().parents[1]
COLS=['evento_id','corrida_id','creado_utc','token','mercado','marco','tipo_alerta','estado_evento','spot_usdt','nivel_usdt','distancia_pct','rsi14','rsi_sma14','stoch_k','stoch_d','regla_clave','certificacion','usdt_preparar','balancer_libre','accion_sugerida','clave_senal']

def event(eid, token='BTC', kind='COMPRA_C1', action='PREPARAR COMPRA LIMIT BTC 100 USDT',state='READY',cert='CERTIFICADA',price=72000,budget=100,run='r1',when='2026-10-17T12:18:00Z'):
    values=dict(evento_id=eid,corrida_id=run,creado_utc=when,token=token,marco='1H',tipo_alerta=kind,
                estado_evento=state,nivel_usdt=price,certificacion=cert,usdt_preparar=budget,accion_sugerida=action,clave_senal=eid)
    return [values.get(x) for x in COLS]
def inbox(events, receipts=None):
    return {'runs':[['corrida_id','marco'],['r1','1H'],['r2','4H']],
            'events':[COLS]+events,'receipts':[['evento_id','leido_utc']]+(receipts or [])}

class ActionFilterTest(unittest.TestCase):
    def test_watch_and_preconfirmed_never_show_even_if_buy_word(self):
        for state,cert in [('WATCH','CERTIFICADA'),('PRECONFIRMADO','CERTIFICADA'),('READY','NO_CERTIFICADA')]:
            self.assertIsNone(alert_category(dict(zip(COLS,event('x',state=state,cert=cert)))))
    def test_buy_certified_budget_and_level(self):
        self.assertEqual(alert_inbox(inbox([event('buy')]))['records'][0]['category'],'COMPRA')
        self.assertEqual(alert_inbox(inbox([event('badbudget',budget=0)]))['unread_count'],0)
        self.assertEqual(alert_inbox(inbox([event('badlevel',price=0)]))['unread_count'],0)
    def test_sell_certified_quantified_and_actionable(self):
        rows=[event('s1',kind='VENTA_O5',action='VENDER 20 LINK a 15 USDT; SELL sujeto a revisión',price=15,budget=0),
              event('s2',kind='VENTA_O5',action='VIGILANCIA: NO ORDEN',price=15,budget=0)]
        x=alert_inbox(inbox(rows));self.assertEqual([r['category'] for r in x['records']],['VENTA'])
    def test_ready_qf_needs_sl_tp_verified(self):
        e=event('tb',kind='TRADINGBOT_LONG_READY',action='LONG BTC 80000 SL 78000 TP 84000',cert='CERTIFICADA_QF')
        self.assertEqual(alert_inbox(inbox([e]))['records'][0]['category'],'TRADINGBOT READY')
        self.assertFalse(alert_inbox(inbox([event('tb2',kind='TRADINGBOT_LONG_READY',action='LONG BTC READY',cert='CERTIFICADA_QF')]))['records'])
        self.assertFalse(alert_inbox(inbox([event('tb3',kind='TRADINGBOT_LONG_READY',action='LONG BTC SL 78000 TP 84000',cert='NO_CERTIFICADA_QF')]))['records'])
    def test_liquidity_only_with_concrete_amount_and_validated_level(self):
        e=event('liq',kind='PREPARAR_LIQUIDEZ',action='RESERVAR USDT 2000 para compra en nivel validado',budget=2000)
        self.assertEqual(alert_inbox(inbox([e]))['unread_count'],1)
        self.assertEqual(alert_inbox(inbox([event('liq2',kind='PREPARAR_LIQUIDEZ',action='RESERVAR 2000',budget=0)]))['unread_count'],0)
    def test_bsi_sell_blocked_until_certified_and_explicit_enabled(self):
        e=event('bsi',kind='BSI_SELL',action='VENDER 50 SOL en 110 USDT',price=110)
        self.assertEqual(alert_inbox(inbox([e]))['unread_count'],0)
        self.assertEqual(alert_inbox(inbox([e]),bsi_enabled=True)['records'][0]['category'],'BSI SELL')
    def test_scope_1h_only(self):
        self.assertEqual(alert_inbox(inbox([event('other',run='r2')]))['unread_count'],0)
    def test_latest_read_prevents_historical_duplicate_reappearing(self):
        a=event('old',when='2026-10-17T12:10:00Z');b=event('new',when='2026-10-17T12:20:00Z')
        self.assertEqual(alert_inbox(inbox([a,b]))['unread_count'],1)
        self.assertEqual(alert_inbox(inbox([a,b],[['new','2026-10-17T12:30:00Z']]))['unread_count'],0)
    def test_material_change_creates_new_alert(self):
        a=event('old',price=80000);b=event('new',price=79000)
        self.assertEqual(alert_inbox(inbox([a,b]))['unread_count'],2)

class PivotO1Tests(unittest.TestCase):
    def sample(self):
        return candidates_binance('BTC',{'status':'OK','scope':'EXPLORATORY_ONLY',
                  'cycle_high':{'price':126199.63,'date_utc':'2025-10-06T00:00:00Z'},
                  'cycle_low':{'price':57800.19,'date_utc':'2026-07-01T00:00:00Z'},'wave_pivots':{}})
    def test_o1_post_cl_max_is_preliminary_with_date(self):
        a=self.sample();d={'status':'OK','records':[
           {'open_utc':'2026-06-29T00:00:00Z','high':'99000'},
           {'open_utc':'2026-07-02T00:00:00Z','high':'71200'},
           {'open_utc':'2026-09-15T00:00:00Z','high':'92200'},
           {'open_utc':'2026-10-15T00:00:00Z','high':'81000'}]}
        r=add_uncertified_daily_extrema(a,d)
        self.assertEqual(r['o1'],92200)
        self.assertEqual(r['o1_date'],'2026-09-15')
        self.assertFalse(r['o1_certified'])
        self.assertIsNone(r['o2'])
    def test_keep_weekly_candidate(self):
        a=self.sample();a['o1']=88888;a['o1_date']='2026-08-01'
        r=add_uncertified_daily_extrema(a,{'status':'OK','records':[{'open_utc':'2026-08-05T00:00:00Z','high':'100000'}]})
        self.assertEqual(r['o1'],88888)
    def test_sui_selected_low_has_no_unverified_date(self):
        s=candidates_binance('SUI',{'status':'OK','scope':'EXPLORATORY_ONLY','cycle_low':{'price':'0.5597','date_utc':'2025-10-10T00:00:00Z'},'wave_pivots':{}},selected_low=.6359)
        self.assertIsNone(s['cl_date'])
        self.assertIsNone(add_uncertified_daily_extrema(s,{'status':'OK','records':[{'open_utc':'2025-10-11','high':100} ]})['o1'])

class UIReleaseTests(unittest.TestCase):
    def test_navigation_tooltips_and_no_fake_badge(self):
        base=(ROOT/'templates/base.html').read_text();settings=(ROOT/'templates/settings.html').read_text()
        self.assertIn('tooltips.js',base)
        self.assertNotIn('<span class="badge info">Validar → Guardar → Sincronizar</span>',settings)
        self.assertIn('data-tab="mcp"',settings)
        self.assertNotIn('Conexiones MCP',(ROOT/'templates/index.html').read_text())
    def test_mcp_refresh_admin_only_and_no_restart(self):
        code=(ROOT/'app.py').read_text()
        self.assertIn("@app.route('/api/mcp-refresh',methods=['POST'])",code)
        self.assertIn('not _admin_authorized() or not _csrf_ok()',code)
        self.assertIn("_MARKET_CACHE.update(stored=0.0,observed=None,prices=None)",code)
        self.assertNotIn('RENDER_API_KEY',code)
    def test_bsi_and_wave_chart_title(self):
        self.assertIn('BTC Strength Index (BSI)',(ROOT/'templates/index.html').read_text())
        chart=(ROOT/'templates/forecast.html').read_text()
        self.assertIn('wave-price-label',chart)
        self.assertIn('document.createElementNS(ns,\'title\')',chart)

if __name__=='__main__':unittest.main()
