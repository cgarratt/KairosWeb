from datetime import datetime,timezone
import google_sheets_master as gs
TARGETS = {'BTC': 0.2, 'ETH': 0.15, 'SOL': 0.15, 'LINK': 0.1, 'HYPE': 0.1, 'HBAR': 0.05, 'SUI': 0.05, 'ONDO': 0.05, 'PUMPFUN': 0.05, 'PLUME': 0.05, 'VIRTUAL': 0.025, 'PEPE': 0.025}

def fake_master():
    ctrl = [['Campo', 'Valor', 'Instrucción']]
    values = {'snapshot_id': 'TEST-001', 'fecha_corte': '2026-10-16', 'estado_publicacion': 'PUBLICADO', 'publicado_utc': datetime.now(timezone.utc).isoformat(), 'schema_version': '5.0.0', 'Liquidez física': 50, 'Costo abierto cripto': 12, 'ordenes_activas_declaradas': '0', 'fills_pendientes_registro_declarados': '0'}
    ctrl += [[k, v] for k, v in values.items()]
    params = [['Módulo', 'Clave estable', 'Valor', 'Tipo', 'Unidad', 'Estado', 'Ámbito', 'Fuente', 'Nota']]
    setting = {'SNAPSHOT_PROVIDER': 'GOOGLE_SHEETS', 'BTC_NEVER_SELL': True, 'FRESH_DATA_FAIL_CLOSED': True, 'DRIFT_BAND_PP': 1, 'STRUCTURAL_USDT_TARGET': 0.4, 'C1_BAG_FRACTION_P': 0.15, 'C2_BAG_FRACTION_P': 0.1, 'QF_MARGIN_CAP_PER_POSITION': 0.25, 'QF_ACCOUNT_RISK_PER_TRADE': 0.025, 'QF_ACCOUNT_RISK_TOTAL': 0.1, 'RISK_REWARD_MIN': 2, 'MAX_OPEN_POSITIONS': 4, 'MAX_LEVERAGE': 5, 'O5_BTC_PROCEEDS_FRACTION': 0.3, 'O5_USDT_PROCEEDS_FRACTION': 0.7, 'BSI_PROVIDER': 'BINANCE_SPOT_MCP_4H_SYNC', 'HYPE_MACRO_PROVIDER': 'HYPERLIQUID_SPOT_HYPE_USDC_MCP', 'BALANCER_RESERVE_FORMULA': 'MAX(0,USDT_TOTAL-0.25*P-QF_REAL)', 'BALANCER_NOMINAL_REFERENCE_P': 0.05, 'SLIDER_MAX_SIMULATED_USDT_TARGET': 0.7}
    params += [['TEST', k, v, 'bool' if isinstance(v, bool) else 'number' if isinstance(v, (float, int)) else 'string', '', 'REFERENCIA_NO_TOPE' if k == 'BALANCER_NOMINAL_REFERENCE_P' else 'APROBADO_SIMULACION' if k == 'SLIDER_MAX_SIMULATED_USDT_TARGET' else 'APROBADO', 'OPERATIVO', 'TEST'] for k, v in setting.items()]
    pos = [['Token Kairos', 'Mercado MCP', 'Tier', 'Target cripto %', 'HODL unidades', 'Core unidades', 'Exchange unidades', 'Total unidades (calc)', 'Costo prom. USDT', 'Costo abierto USDT (calc)', 'Corte', 'Fuente declarada', 'Validación total', 'Unidades totales declaradas']]
    for s, t in TARGETS.items():
        pos.append([s, 'PUMP' if s == 'PUMPFUN' else s, 'T1' if t >= 0.1 else 'T2' if t == 0.05 else 'T3', t, 0, 0, 1, 1, 1, 1, '2026-10-16', 'TEST', 'OK', 1])
    liq = [['Venue', 'USDT físico', 'Clasificación', 'Corte', 'Fuente'], ['Binance', 40, 'OPERATIVO'], ['Quantfury', 10, 'TRADING_QF'], ['TOTAL LIQUIDEZ', 50], ['RESERVA TRADING QF', 10], ['USDT OPERATIVO', 40], ['Total informado por usuario', 50], ['Diferencia de conciliación', 0]]
    custody = [['Tier', 'HODL %', 'Core %', 'Exchange %', 'Validación'], ['T1', 0.4, 0.3, 0.3, 'OK'], ['T2', 0, 0.3, 0.7, 'OK'], ['T3', 0, 0, 1, 'OK']]
    pivots = [['Token', 'Cycle Low USDT', 'Fecha CL', 'O1 USDT', 'Fecha O1', 'O2 USDT', 'Fecha O2', 'O3 USDT', 'O4 USDT', 'O5 USDT', 'Fib38.2', 'C1', 'C2', 'Fib78.2', 'Estado del pivote', 'Fuente', 'Certificado']]
    pivots += [[s, None, None, None, None, None, None, None, None, None, None, 0.5, 0.4, None, 'REFERENCIA_HISTORICA', 'TEST'] for s in TARGETS]
    bsi = [['Token', 'Ancla hist', 'Quote', 'Venue', 'Fecha', 'Baseline', 'Fecha baseline', 'HWM', 'SELL pendiente', 'Estado', 'Fuente', 'MCP Open', 'MCP Close', 'UTC', 'MCP BSI', 'Estado MCP']]
    bsi += [[s, 1, 'USDT', 'Binance', '2026-10-05', None, None, None, None, 'HISTORICO_NO_ACCIONABLE', 'TEST', 1, 0.9, '2026-10-17T00:00:00Z', 0, 'INFORMATIVE_ONLY'] for s in TARGETS]
    integral = [['Segmento', 'Objetivo USDT', 'Registrado histórico USDT'], ['Capital inicial histórico', 150], ['Pérdidas realizadas acumuladas', 20], ['Capital vivo declarado', 130], ['HODL + Core', 60, 40], ['Exchange', 30, 35], ['Liquidez', 45, 30], ['Trading', 15, 5], ['Lost · realizado', 0, 20]]
    validations = [['Control', 'Resultado']] + [[k, 'OK'] for k in ('12 tokens Kairos presentes', 'Targets cripto suman 100%', 'Custodia suma unidades', 'Total USDT conciliado', 'Reserva QF sin duplicar')] + [['Estado publicación', 'PUBLICADO']]
    raw = {'control': ctrl, 'positions': pos, 'liquidity': liq, 'custody': custody, 'orders': [['header']], 'fills': [['header']], 'pivots': pivots, 'integral': integral, 'bsi': bsi, 'validation': validations, 'parameters': params}
    return {a1: raw[name] for name, a1 in gs.SHEETS.items()}
from google_sheets_master import SHEETS
def demo_master():
    raw = fake_master()
    ctrl = raw[SHEETS['control']]
    ctrl.extend([['Reserva QF', 10], ['USDT operativo', 40], ['Capital contable estimado', 62], ['aprobado_por', 'TEST'], ['reemplaza_snapshot', 'TEST-000'], ['origen', 'TEST'], ['comentario', 'TEST']])
    p = raw[SHEETS['parameters']]
    p.extend([['CICLO', 'O3_BTC_PROCEEDS_FRACTION', 0.3, 'number', 'fraction', 'APROBADO', 'OPERATIVO', 'test'], ['CICLO', 'O3_USDT_PROCEEDS_FRACTION', 0.7, 'number', 'fraction', 'APROBADO', 'OPERATIVO', 'test']])
    return raw
