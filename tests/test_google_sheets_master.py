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
        with self.assertRaisesRegex(gs.SheetDataError,'30/70'):gs.parse_master(raw)
    def test_orders_not_silently_ignored(self):
        raw=fake_master();raw[gs.SHEETS['orders']].append(['Binance','order-id'])
        with self.assertRaisesRegex(gs.SheetDataError,'reconcile'):gs.parse_master(raw)
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
