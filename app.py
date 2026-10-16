"""Kairos Web v3.2: read-only dashboard and preliminary mode pages backed by approved MCPs."""
import asyncio
import json
import os
import secrets
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, Response, jsonify, render_template, request, abort
from fastmcp import Client

BASE = Path(__file__).parent
app = Flask(__name__)
SNAPSHOT = json.loads((BASE / 'data/snapshot_master_2026-10-15.json').read_text())
CONFIG = json.loads((BASE / 'data/config.json').read_text())
BSI_ANCHORS = json.loads((BASE / 'data/bsi_anchors.json').read_text())
TOKENS = [r['symbol'] for r in CONFIG['universe']]
TARGETS = {r['symbol']: r['target'] for r in CONFIG['universe']}
TIERS = {r['symbol']: r['tier'] for r in CONFIG['universe']}
MODE_DEFS = [
    {'slug':'resumen','name':'Resumen','subtitle':'Auditoría del portafolio','description':'Posiciones, liquidez, custodia y composición general del portafolio.'},
    {'slug':'balancer','name':'Balancer','subtitle':'Rebalanceo y liquidez','description':'Propuestas de rebalanceo, control de piso de liquidez y protección de Core.'},
    {'slug':'compras','name':'Compras','subtitle':'O2 / O4','description':'Candidatos estructurales C1 50% y C2 61.8%, priorizados por déficit.'},
    {'slug':'ventas','name':'Ventas','subtitle':'Objetivo USDT','description':'Propuestas solo SELL para acercarse a la meta de liquidez y reducir sobrepeso.'},
    {'slug':'tradingbot','name':'TradingBot','subtitle':'Táctico 4H','description':'Vista táctica preliminar para la reserva de trading y activos de seguimiento.'},
    {'slug':'alertas','name':'Alertas','subtitle':'Vigilancia 1H · 4H · 1D','description':'Watchlist visual de composición, BSI y liquidez. Motor horario aún pendiente.'},
    {'slug':'forecast','name':'Forecast','subtitle':'Escenarios O2 → O5','description':'Escenarios preliminares y sensibilidad patrimonial, sin predicciones ni órdenes.'},
    {'slug':'benchmark','name':'Benchmark','subtitle':'Comparación estructural','description':'Base visual para comparar estructura actual vs. objetivos Kairos.'},
    {'slug':'rotation','name':'Rotation','subtitle':'Rotación de activos','description':'Fuentes y destinos potenciales de rotación, en modo simulación.'},
    {'slug':'montecarlo','name':'MonteCarlo','subtitle':'Simulación probabilística','description':'Workbench preliminar para simulación de escenarios y dispersión de resultados.'},
]
MODES_BY_SLUG = {m['slug']: m for m in MODE_DEFS}
# Short TTL protects the MCP service from 10 simultaneous page loads, without
# ever labeling cached observations as real-time without their original time.
_MARKET_CACHE = {'stored': 0.0, 'observed': None, 'dashboard': None}
_MARKET_LOCK = threading.Lock()
CACHE_TTL_SECONDS = 30


@app.before_request
def authenticate():
    if request.path == '/health':
        return None
    password = os.getenv('KAIROS_WEB_PASSWORD', '')
    if not password:
        return jsonify({'status': 'CONFIG_REQUIRED', 'message': 'Configure KAIROS_WEB_PASSWORD in Render.'}), 503
    auth = request.authorization
    username = os.getenv('KAIROS_WEB_USER', 'kairos')
    if not auth or not secrets.compare_digest(auth.username or '', username) or not secrets.compare_digest(auth.password or '', password):
        return Response('Autenticación requerida', 401, {'WWW-Authenticate':'Basic realm="Kairos Web"', 'Cache-Control':'no-store'})

@app.after_request
def headers(resp):
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'no-referrer'
    return resp

async def call_mcp(env_name, tool, args=None):
    endpoint = os.getenv(env_name, '').strip()
    if not endpoint:
        raise RuntimeError(f'{env_name} no configurada')
    parsed = urlsplit(endpoint)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1')):
        raise RuntimeError(f'{env_name}: URL debe usar HTTPS')
    token = os.getenv(env_name.replace('_URL', '_TOKEN'), '').strip()
    from fastmcp.client.transports import StreamableHttpTransport
    transport = StreamableHttpTransport(endpoint, headers={'Authorization': f'Bearer {token}'} if token else None)
    async with Client(transport, timeout=80) as client:
        result = await client.call_tool(tool, args or {})
    if result.is_error:
        raise RuntimeError(f'{tool}: error remoto')
    if isinstance(result.data, dict):
        return result.data
    for block in result.content:
        if getattr(block, 'type', None) == 'text':
            value = json.loads(block.text)
            if isinstance(value, dict):
                return value
    raise RuntimeError(f'{tool}: respuesta MCP no reconocida')

def pretty_error(exc):
    if isinstance(exc, RuntimeError) and ('no configurada' in str(exc) or 'debe usar HTTPS' in str(exc)):
        return str(exc)
    return 'MCP sin respuesta válida. Revisar conectividad y logs de Render.'

def fmt_money(v):
    return f"${v:,.0f}" if abs(v) >= 100 else f"${v:,.2f}"

def fmt_price(v):
    if v >= 1000:
        return f"${v:,.2f}"
    if v >= 1:
        return f"${v:,.4f}".rstrip('0').rstrip('.')
    return f"${v:,.6f}".rstrip('0').rstrip('.')

def fmt_pct(v):
    return f"{v:.1f}%"

def tone_from_drift(d):
    return 'danger' if d > 1 else 'warn' if d < -1 else 'ok'

def custody_summary(prices):
    sums={'HODL_bloqueado':0.0,'Core_estrategico':0.0,'Exchange_declarado':0.0}
    for token, units in SNAPSHOT['custody_core_blocked__core_strategic__exchange'].items():
        price=prices.get('PUMP' if token=='PUMPFUN' else token)
        if price is None:
            continue
        for key,qty in zip(sums,units):
            sums[key]+=float(qty)*price
    return sums

def historical_bsi(prices):
    btc=prices['BTC']
    btc_base=float(BSI_ANCHORS['btc_base_price'])
    out=[]
    for symbol in TOKENS:
        ticker='PUMP' if symbol=='PUMPFUN' else symbol
        if symbol=='BTC':
            continue
        anchor=BSI_ANCHORS.get('assets',{}).get(symbol)
        if not anchor or not anchor.get('price'):
            out.append({'token':ticker,'bsi':None,'status':'NO_ANCHOR'})
            continue
        base=float(anchor['price'])
        bsi=100*((prices[ticker]/base)/(btc/btc_base)-1)
        out.append({'token':ticker,'bsi':round(bsi,2),'status':'HISTORICAL_ONLY'})
    return {'status':'INFORMATIVE_ONLY','anchor_date':'2026-10-05',
            'basis':'Spot Binance USDT actual vs anclas históricas TradingView USD/USDT (aproximación de paridad)',
            'signals_enabled':False,'note':'No es una señal de venta. La monetización necesita baseline certificado, HWM y cierres sincronizados.',
            'rows':sorted(out,key=lambda x: (x['bsi'] is None,-(x['bsi'] or 0)))}

def forecast_sensitivity(rows, usdt):
    btc_value=next((r['value'] for r in rows if r['token']=='BTC'),0.0)
    base=sum(r['value'] for r in rows)+usdt
    shocks=[-30,-15,0,15,30]
    return {'status':'ILLUSTRATIVE_ONLY','model':'BTC price shock, altcoins and USDT unchanged, no transactions',
            'base_portfolio':base,'btc_units':SNAPSHOT['holdings_total']['BTC'],
            'scenarios':[{'btc_change_pct':s,'portfolio_value':round(base+btc_value*s/100,2),
                          'portfolio_change_pct':round((btc_value*s/100)/base*100,2) if base else 0} for s in shocks],
            'official_forecast':'NOT_CONNECTED','note':'NO es Forecast O2-O5 ni predicción. Falta motor y precios hipotéticos por onda.'}

def core_dashboard(prices):
    rows=[]
    portfolio_crypto=0.0
    for token in TOKENS:
        key = 'PUMPFUN' if token == 'PUMPFUN' else token
        market_key = 'PUMP' if token == 'PUMPFUN' else token
        price = prices[market_key]
        units = float(SNAPSHOT['holdings_total'].get(key, 0))
        value = units*price
        portfolio_crypto += value
        rows.append({'token':market_key,'tier':TIERS[token], 'target':TARGETS[token],
                     'units':units,'price':price,'value':value})
    for row in rows:
        row['weight']=row['value']/portfolio_crypto if portfolio_crypto else 0
        row['drift_pp']=(row['weight']-row['target'])*100
        row['status']='SOBRE' if row['drift_pp']>1 else 'INFRA' if row['drift_pp']< -1 else 'OK'
    liquidity=SNAPSHOT['physical_total_USDT']
    trading=SNAPSHOT['trading_real_fixed_USDT']
    total_value = portfolio_crypto+liquidity
    return {
        'rows': rows,
        'crypto_value': portfolio_crypto,
        'usdt_total':liquidity,
        'usdt_operating':SNAPSHOT['kairos_operating_USDT_before_commitments'],
        'trading_reserve':trading,
        'total_value':total_value,
        'usdt_pct':liquidity/total_value if total_value else 0,
        'crypto_pct':portfolio_crypto/total_value if total_value else 0,
        'snapshot_date':SNAPSHOT['units_snapshot_as_of'],
        'note':'Unidades y USDT del snapshot Master 15/10/2026. No se leen balances privados de exchanges.',
        'liquidity_venues':SNAPSHOT['liquidity_venues_USDT'],
        'liquidity_floor_usdt':total_value*0.40,
        'liquidity_headroom_usdt':liquidity-total_value*0.40,
        'custody_summary':custody_summary(prices),
        'bsi_historical':historical_bsi(prices),
        'forecast_sensitivity':forecast_sensitivity(rows,liquidity)
    }

def load_live_dashboard():
    with _MARKET_LOCK:
        if _MARKET_CACHE['dashboard'] is not None and (time.monotonic() - _MARKET_CACHE['stored']) < CACHE_TTL_SECONDS:
            return _MARKET_CACHE['observed'], _MARKET_CACHE['dashboard']
    # Retry one time on transient Render cold-start and MCP transport failure.
    last_error = None
    data = None
    for attempt in range(2):
        try:
            data = asyncio.run(call_mcp('BINANCE_MCP_URL', 'get_kairos_spot_prices'))
            if data.get('status') != 'OK':
                raise RuntimeError('Binance MCP DATA_ERROR')
            break
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(1.5)
    if data is None:
        raise last_error or RuntimeError('MCP no disponible')
    if data.get('status') != 'OK':
        raise RuntimeError('Binance MCP DATA_ERROR')
    records = data.get('records')
    if not isinstance(records, list):
        raise RuntimeError('Invalid records')
    prices={}
    for record in records:
        s=record['symbol']
        if not s.endswith('USDT'):
            continue
        value=float(record['price'])
        if not (value > 0 and value < float('inf')):
            raise ValueError('Invalid price')
        prices[s[:-4]]=value
    required = set(('PUMP' if t == 'PUMPFUN' else t) for t in TOKENS)
    if not required.issubset(prices):
        raise RuntimeError('Missing one or more Kairos assets')
    observed = data.get('as_observed_utc')
    timestamp=datetime.fromisoformat(observed.replace('Z','+00:00'))
    age=(datetime.now(timezone.utc)-timestamp.astimezone(timezone.utc)).total_seconds()
    if age < -60 or age > 180:
        raise RuntimeError('Stale MCP data')
    dashboard=core_dashboard(prices)
    with _MARKET_LOCK:
        _MARKET_CACHE.update(stored=time.monotonic(), observed=observed, dashboard=dashboard)
    return observed, dashboard

def top_n(rows, key, n=5, reverse=True, predicate=None):
    items = rows
    if predicate:
        items = [r for r in rows if predicate(r)]
    return sorted(items, key=key, reverse=reverse)[:n]

def as_table(title, columns, rows, subtitle=''):
    return {'title':title, 'subtitle':subtitle, 'columns':columns, 'rows':rows}

def bar_card(title, subtitle, items):
    maxv = max([abs(i.get('value',0)) for i in items] or [1])
    return {'title':title,'subtitle':subtitle,'max':maxv or 1,'items':items}

def build_mode_payload(slug, d, observed):
    rows = sorted(d['rows'], key=lambda x: x['value'], reverse=True)
    under = top_n(rows, key=lambda r: r['drift_pp'], n=6, reverse=False, predicate=lambda r: r['drift_pp'] < -1)
    over = top_n(rows, key=lambda r: r['drift_pp'], n=6, reverse=True, predicate=lambda r: r['drift_pp'] > 1)
    sellable_over = [r for r in over if r['token'] != 'BTC']
    bsi_rows = [r for r in d['bsi_historical']['rows'] if r['bsi'] is not None]
    top_bsi = sorted(bsi_rows, key=lambda x: x['bsi'], reverse=True)[:6]
    top_pos = rows[0]
    top3_conc = sum(r['weight'] for r in rows[:3])
    usdt_gap = d['liquidity_floor_usdt'] - d['usdt_total']
    c1_budget = d['total_value'] * 0.15
    c2_budget = d['total_value'] * 0.10
    deficits = [abs(r['drift_pp']) for r in under]
    deficits_sum = sum(deficits) or 1

    common = {
        'generated_at': observed,
        'read_only': True,
        'status_badge': 'LIVE MCP',
        'snapshot_note': d['note'],
        'callouts': []
    }

    if slug == 'resumen':
        return {
            **common,
            'metrics':[
                {'label':'Patrimonio total','value':fmt_money(d['total_value']),'help':'Cripto + USDT físico consolidado','tone':'primary'},
                {'label':'Liquidez total','value':fmt_money(d['usdt_total']),'help':fmt_pct(d['usdt_pct']*100) if False else f"{fmt_pct(d['usdt_pct']*100)} del patrimonio",'tone':'ok'},
                {'label':'Mayor posición','value':top_pos['token'],'help':f"{fmt_pct(top_pos['weight']*100)} · {fmt_money(top_pos['value'])}",'tone':'primary'},
                {'label':'Snapshot base','value':d['snapshot_date'],'help':'Unidades estáticas; precios en línea por MCP','tone':'neutral'},
            ],
            'highlights':[
                f"{len(over)} activos sobreponderados y {len(under)} infraponderados con la banda de ±1 pp.",
                f"La liquidez consolidada equivale a {fmt_pct(d['usdt_pct']*100)} del patrimonio.",
                f"La concentración Top 3 representa {fmt_pct(top3_conc*100)} de la manga cripto.",
            ],
            'bars':[
                bar_card('Distribución por token','Peso relativo dentro de la manga cripto',[
                    {'label':r['token'], 'value':r['weight']*100, 'display':fmt_pct(r['weight']*100), 'tone':tone_from_drift(r['drift_pp'])}
                    for r in rows[:8]
                ]),
                bar_card('Liquidez por venue','USDT físico confirmado por venue',[
                    {'label':k, 'value':v, 'display':fmt_money(v), 'tone':'ok'}
                    for k,v in sorted(d['liquidity_venues'].items(), key=lambda x:x[1], reverse=True) if v > 0
                ])
            ],
            'tables':[
                as_table('Posiciones actuales',['Token','Precio','Valor','Peso','Target','Estado'],[
                    [r['token'], fmt_price(r['price']), fmt_money(r['value']), fmt_pct(r['weight']*100), fmt_pct(r['target']*100), r['status']] for r in rows
                ], 'Base de unidades del snapshot + valoración Spot Binance'),
                as_table('Custodia estimada',['Segmento','Valor aprox.'],[
                    ['HODL bloqueado', fmt_money(d['custody_summary']['HODL_bloqueado'])],
                    ['Core estratégico', fmt_money(d['custody_summary']['Core_estrategico'])],
                    ['Exchange declarado', fmt_money(d['custody_summary']['Exchange_declarado'])],
                ], 'No consulta balances privados.')
            ],
            'callouts':[{'tone':'info','title':'Lectura del modo','text':'Esta página resume el mismo tipo de información que Kairos Resumen muestra en ChatGPT, pero en formato visual ejecutivo.'}]
        }

    if slug == 'balancer':
        return {
            **common,
            'metrics':[
                {'label':'Holgura sobre piso 40%','value':('+' if d['liquidity_headroom_usdt']>=0 else '-') + fmt_money(abs(d['liquidity_headroom_usdt'])),'help':'Matemática; no descuenta órdenes pendientes','tone':'ok' if d['liquidity_headroom_usdt']>=0 else 'danger'},
                {'label':'Infraponderados','value':str(len(under)),'help':'Candidatos de compra Balancer / Compras','tone':'warn'},
                {'label':'Sobreponderados','value':str(len(sellable_over)),'help':'Candidatos de venta convencionales','tone':'danger'},
                {'label':'Piso USDT objetivo','value':fmt_money(d['liquidity_floor_usdt']),'help':'40% del patrimonio total actual','tone':'neutral'},
            ],
            'highlights':[
                'Balancer solo propone; no envía órdenes ni mueve custodia.',
                'BTC nunca se vende. Core y HODL permanecen protegidos.',
                'Si el BSI relativo supera niveles altos, la captura requiere baseline certificado y reconciliación.',
            ],
            'bars':[
                bar_card('Brechas vs target','Diferencias más relevantes en puntos porcentuales',[
                    {'label':r['token'],'value':abs(r['drift_pp']),'display':('+' if r['drift_pp']>=0 else '')+f"{r['drift_pp']:.1f} pp",'tone':tone_from_drift(r['drift_pp'])}
                    for r in sorted(rows, key=lambda x: abs(x['drift_pp']), reverse=True)[:8]
                ]),
                bar_card('BSI histórico','Información relativa frente a BTC (referencial)',[
                    {'label':r['token'],'value':abs(r['bsi']),'display':('+' if r['bsi']>=0 else '')+f"{r['bsi']:.1f}%",'tone':'warn' if r['bsi']>20 else 'ok' if r['bsi']>=0 else 'danger'}
                    for r in top_bsi
                ])
            ],
            'tables':[
                as_table('Candidatos de compra Balancer',['Token','Peso actual','Target','Déficit','Lectura'],[
                    [r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"{r['drift_pp']:.1f} pp", 'BUY / WATCH'] for r in under
                ], 'Solo activos infraponderados'),
                as_table('Candidatos de venta Balancer',['Token','Peso actual','Target','Exceso','Lectura'],[
                    [r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"+{r['drift_pp']:.1f} pp", 'SELL / HOLD'] for r in sellable_over
                ], 'Excluye BTC, que sigue en NEVER SELL')
            ],
            'callouts':[{'tone':'info','title':'Vista preliminar','text':'Equivale a un Balancer visual: muestra dónde están las desviaciones y qué zonas requerirían atención antes del cálculo final de propuestas.'}]
        }

    if slug == 'compras':
        buy_rows=[]
        for r in under:
            share = abs(r['drift_pp'])/deficits_sum
            buy_rows.append([r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"{r['drift_pp']:.1f} pp", fmt_money(c1_budget*share), fmt_money(c2_budget*share)])
        return {
            **common,
            'metrics':[
                {'label':'USDT operativo','value':fmt_money(d['usdt_operating']),'help':'Antes de compromisos y fees','tone':'ok'},
                {'label':'Bolsa teórica C1','value':fmt_money(c1_budget),'help':'15% del patrimonio actual','tone':'primary'},
                {'label':'Bolsa teórica C2','value':fmt_money(c2_budget),'help':'10% del patrimonio actual','tone':'primary'},
                {'label':'Activos con déficit','value':str(len(under)),'help':'Con banda de -1 pp','tone':'warn'},
            ],
            'highlights':[
                'C1 corresponde a Fibonacci 50% y C2 a Fibonacci 61.8%, conforme a las reglas vigentes.',
                'Esta página todavía no trae anchors O2/O4 ni calcula precios límite finales.',
                'La distribución mostrada es visual y proporcional al déficit actual de composición.',
            ],
            'bars':[
                bar_card('Déficit por token','Prioridad relativa para nuevas compras',[
                    {'label':r['token'],'value':abs(r['drift_pp']),'display':f"{r['drift_pp']:.1f} pp",'tone':'warn'} for r in under
                ])
            ],
            'tables':[
                as_table('Candidatos estructurales',['Token','Peso actual','Target','Déficit','C1 ref.','C2 ref.'], buy_rows,
                         'Montos referenciales; los precios Fib y la estructura aún no están conectados.')
            ],
            'callouts':[{'tone':'warn','title':'Pendiente de integración','text':'Para igualar la salida de ChatGPT faltan los anchors aprobados O1/O3/O4, los precios Fib y las órdenes existentes por exchange.'}]
        }

    if slug == 'ventas':
        needed = max(0.0, usdt_gap)
        sell_rows=[]
        for r in sellable_over:
            excess_value = max(0.0, (r['weight']-r['target']) * d['crypto_value'])
            sell_rows.append([r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"+{r['drift_pp']:.1f} pp", fmt_money(excess_value), 'SELL'])
        return {
            **common,
            'metrics':[
                {'label':'USDT actual','value':fmt_money(d['usdt_total']),'help':f"{fmt_pct(d['usdt_pct']*100)} del patrimonio",'tone':'ok'},
                {'label':'Meta 40% USDT','value':fmt_money(d['liquidity_floor_usdt']),'help':'Objetivo estructural actual','tone':'neutral'},
                {'label':'Gap a cubrir','value':fmt_money(needed),'help':'0 si ya se cumple el piso','tone':'danger' if needed>0 else 'ok'},
                {'label':'Activos vendibles','value':str(len(sellable_over)),'help':'Sobreponderados, excluyendo BTC','tone':'danger'},
            ],
            'highlights':[
                'Modo Ventas es solo SELL; no compra ni rebalancea después de vender.',
                'BTC permanece en NEVER SELL.',
                'Las ventas reales deben respetar Core, HODL y reservas por órdenes pendientes.',
            ],
            'bars':[
                bar_card('Exceso de peso','Fuentes potenciales de liquidez',[
                    {'label':r['token'],'value':r['drift_pp'],'display':f"+{r['drift_pp']:.1f} pp",'tone':'danger'} for r in sellable_over
                ])
            ],
            'tables':[
                as_table('Propuesta preliminar de venta',['Token','Peso actual','Target','Exceso','Valor teórico','Lectura'], sell_rows,
                         'Valores teóricos; no se aplican límites de unidades disponibles ni ventas ya reservadas.')
            ],
            'callouts':[{'tone':'info','title':'Lectura del modo','text':'La vista replica el espíritu del reporte de Ventas en ChatGPT: objetivo de liquidez, activos fuente y restricciones principales.'}]
        }

    if slug == 'tradingbot':
        watch = [r for r in rows if r['token'] in ('BTC','ETH','SOL','HYPE','LINK')]
        return {
            **common,
            'metrics':[
                {'label':'Reserva Trading','value':fmt_money(d['trading_reserve']),'help':'Bolsa separada de Quantfury','tone':'primary'},
                {'label':'Activos watchlist','value':str(len(watch)),'help':'Núcleo táctico inicial','tone':'neutral'},
                {'label':'Motor táctico','value':'Preliminar','help':'No conectado aún al framework 4H','tone':'warn'},
                {'label':'Acciones habilitadas','value':'Solo lectura','help':'Sin envío de órdenes','tone':'ok'},
            ],
            'highlights':[
                'TradingBot debe vivir separado del portafolio estructural y de las compras C1/C2.',
                'La vista actual sirve como base visual del estado táctico y la reserva disponible.',
                'Falta integrar señales 1H/4H, SL/TP y el tamaño fijo por posición.',
            ],
            'bars':[
                bar_card('Watchlist base','Activos principales para análisis táctico',[
                    {'label':r['token'],'value':r['value'],'display':fmt_money(r['value']),'tone':'primary'} for r in watch
                ])
            ],
            'tables':[
                as_table('Activos tácticos',['Token','Precio','Tier','Valor actual','Rol'],[
                    [r['token'], fmt_price(r['price']), r['tier'], fmt_money(r['value']), 'WATCH / SETUP'] for r in watch
                ], 'Todavía no hay setups LONG/SHORT calculados por la web.')
            ],
            'callouts':[{'tone':'warn','title':'Pendiente de integración','text':'Para igualar TradingBot ChatGPT faltan estructuras de entrada, stop, take profit, timeframe activo y tamaño por posición.'}]
        }

    if slug == 'alertas':
        alert_rows=[]
        for r in rows:
            if abs(r['drift_pp']) > 1:
                alert_rows.append([r['token'], 'Composición', f"{r['drift_pp']:+.1f} pp", 'Revisar peso vs target'])
        for r in top_bsi[:4]:
            if r['bsi'] > 20:
                alert_rows.append([r['token'], 'BSI', f"{r['bsi']:+.1f}%", 'Posible vigilancia BSI (info only)'])
        if d['liquidity_headroom_usdt'] < 0:
            alert_rows.append(['USDT', 'Liquidez', fmt_money(d['liquidity_headroom_usdt']), 'Piso 40% comprometido'])
        return {
            **common,
            'metrics':[
                {'label':'Activos monitoreados','value':'12','help':'Universo Spot Kairos','tone':'primary'},
                {'label':'Watch flags','value':str(len(alert_rows)),'help':'Pre-alertas visuales','tone':'warn'},
                {'label':'Liquidez headroom','value':('+' if d['liquidity_headroom_usdt']>=0 else '-') + fmt_money(abs(d['liquidity_headroom_usdt'])),'help':'Frente al piso 40%','tone':'ok' if d['liquidity_headroom_usdt']>=0 else 'danger'},
                {'label':'Motor horario','value':'Pendiente','help':'1H · 4H · 1D aún no integrados','tone':'neutral'},
            ],
            'highlights':[
                'Alertas en la web serán de vigilancia, no de ejecución automática.',
                'Aquí se muestran pre-alertas útiles mientras se integra el motor oficial de proximidad.',
                'La salida final deberá respetar timeframe y política horaria Kairos.',
            ],
            'bars':[
                bar_card('Activos a vigilar','Se priorizan mayores desviaciones y BSI alto',[
                    {'label':r['token'],'value':abs(r['drift_pp']),'display':f"{r['drift_pp']:+.1f} pp",'tone':tone_from_drift(r['drift_pp'])}
                    for r in sorted(rows, key=lambda x: abs(x['drift_pp']), reverse=True)[:8]
                ])
            ],
            'tables':[
                as_table('Pre-alertas vigentes',['Activo','Tipo','Lectura','Acción sugerida'], alert_rows or [['—','—','—','Sin watch flags relevantes']],
                         'Esta tabla aún no usa zonas O2/O3/O4/O5 ni alertas por proximidad exacta.')
            ],
            'callouts':[{'tone':'info','title':'Lectura del modo','text':'La idea es que esta página muestre el equivalente visual de Kairos Alertas: qué revisar, por qué y con qué prioridad.'}]
        }

    if slug == 'forecast':
        sc = d['forecast_sensitivity']['scenarios']
        return {
            **common,
            'metrics':[
                {'label':'Portafolio base','value':fmt_money(d['forecast_sensitivity']['base_portfolio']),'help':'Escenario actual del snapshot','tone':'primary'},
                {'label':'BTC unidades','value':str(d['forecast_sensitivity']['btc_units']),'help':'Impacta la sensibilidad actual','tone':'neutral'},
                {'label':'Escenario -30% BTC','value':fmt_money(sc[0]['portfolio_value']),'help':f"{sc[0]['portfolio_change_pct']:+.2f}% del portafolio",'tone':'danger'},
                {'label':'Escenario +30% BTC','value':fmt_money(sc[-1]['portfolio_value']),'help':f"{sc[-1]['portfolio_change_pct']:+.2f}% del portafolio",'tone':'ok'},
            ],
            'highlights':[
                'Este Forecast es solo una sensibilidad preliminar, no el Forecast oficial O2–O5.',
                'No se proyectan acumulaciones, ventas parciales ni escenarios multi-activo.',
                'Aun así, sirve como página visual preliminar para el modo Forecast.',
            ],
            'bars':[
                bar_card('Sensibilidad del patrimonio','Variación del valor total ante cambios hipotéticos de BTC',[
                    {'label':('+' if x['btc_change_pct']>0 else '')+str(x['btc_change_pct'])+'% BTC', 'value':abs(x['portfolio_value']-d['forecast_sensitivity']['base_portfolio']), 'display':f"{x['portfolio_change_pct']:+.2f}%", 'tone':'danger' if x['btc_change_pct']<0 else 'ok' if x['btc_change_pct']>0 else 'neutral'}
                    for x in sc
                ])
            ],
            'tables':[
                as_table('Escenarios ilustrativos',['Shock BTC','Valor portafolio','Cambio portafolio'],[
                    [('+' if x['btc_change_pct']>0 else '')+str(x['btc_change_pct'])+'%', fmt_money(x['portfolio_value']), f"{x['portfolio_change_pct']:+.2f}%"] for x in sc
                ], 'No es una predicción; se usa solo para visualización.')
            ],
            'callouts':[{'tone':'warn','title':'Pendiente de integración','text':'Para igualar Forecast ChatGPT faltan los escenarios oficiales por onda, anchors aprobados y lógica de rotación/ventas del ciclo.'}]
        }

    if slug == 'benchmark':
        return {
            **common,
            'metrics':[
                {'label':'Patrimonio base','value':fmt_money(d['total_value']),'help':'Punto de comparación','tone':'primary'},
                {'label':'Top 3 concentración','value':fmt_pct(top3_conc*100),'help':'Mayor concentración del sleeve cripto','tone':'warn'},
                {'label':'Liquidez actual','value':fmt_pct(d['usdt_pct']*100),'help':'USDT consolidado / patrimonio','tone':'ok'},
                {'label':'Desviaciones activas','value':str(len(over)+len(under)),'help':'Activos fuera de la banda ±1 pp','tone':'neutral'},
            ],
            'highlights':[
                'Benchmark sirve como punto de partida para comparar portafolios o estructuras alternativas.',
                'La página muestra la base visual del portafolio vigente con targets y estado.',
                'Todavía no compara una segunda cartera o escenario externo.',
            ],
            'bars':[
                bar_card('Peso actual vs target','Referencia rápida de composición',[
                    {'label':r['token'],'value':r['weight']*100,'display':f"{fmt_pct(r['weight']*100)} / {fmt_pct(r['target']*100)}",'tone':tone_from_drift(r['drift_pp'])} for r in rows[:8]
                ])
            ],
            'tables':[
                as_table('Base de benchmark',['Token','Peso actual','Target','Desvío','Estado'],[
                    [r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"{r['drift_pp']:+.1f} pp", r['status']] for r in rows
                ], 'Usar esta vista como baseline antes de comparar otra estructura.')
            ],
            'callouts':[{'tone':'info','title':'Próxima fase','text':'Luego podemos añadir benchmark lado a lado entre portafolio actual, estructura objetivo y variantes simuladas.'}]
        }

    if slug == 'rotation':
        pairs=[]
        for src, dst in zip(sellable_over[:5], under[:5]):
            pairs.append([src['token'], dst['token'], f"{src['drift_pp']:+.1f} pp", f"{dst['drift_pp']:.1f} pp", 'Rotación simulada'])
        return {
            **common,
            'metrics':[
                {'label':'Fuentes potenciales','value':str(len(sellable_over)),'help':'Activos sobreponderados','tone':'danger'},
                {'label':'Destinos potenciales','value':str(len(under)),'help':'Activos infraponderados','tone':'warn'},
                {'label':'USDT operativo','value':fmt_money(d['usdt_operating']),'help':'Caja potencial de soporte','tone':'ok'},
                {'label':'Modo','value':'Simulación','help':'Sin cambios de target ni ejecución','tone':'neutral'},
            ],
            'highlights':[
                'Rotation sirve para explorar cambios entre activos sin alterar la estructura aprobada.',
                'Aquí se muestran fuentes y destinos potenciales de manera visual.',
                'No se envían propuestas automáticas ni se tocan órdenes existentes.',
            ],
            'bars':[
                bar_card('Fuentes de rotación','Activos con mayor sobrepeso',[
                    {'label':r['token'],'value':r['drift_pp'],'display':f"+{r['drift_pp']:.1f} pp",'tone':'danger'} for r in sellable_over
                ]),
                bar_card('Destinos de rotación','Activos con mayor déficit',[
                    {'label':r['token'],'value':abs(r['drift_pp']),'display':f"{r['drift_pp']:.1f} pp",'tone':'warn'} for r in under
                ])
            ],
            'tables':[
                as_table('Matriz preliminar de rotación',['Desde','Hacia','Exceso','Déficit','Lectura'], pairs or [['—','—','—','—','Sin oportunidades claras']],
                         'Emparejamiento visual simple: no representa órdenes finales.')
            ],
            'callouts':[{'tone':'info','title':'Lectura del modo','text':'Equivale a una vista preliminar del modo Rotation para comparar de dónde podría salir capital y hacia dónde podría rotar.'}]
        }

    if slug == 'montecarlo':
        # preliminary workbench, not a real Monte Carlo engine
        percentiles = [
            ('P10', d['forecast_sensitivity']['base_portfolio'] * 0.93),
            ('P50', d['forecast_sensitivity']['base_portfolio']),
            ('P90', d['forecast_sensitivity']['base_portfolio'] * 1.09),
        ]
        return {
            **common,
            'metrics':[
                {'label':'Workbench','value':'Preliminar','help':'Motor probabilístico aún no integrado','tone':'warn'},
                {'label':'Portafolio base','value':fmt_money(d['total_value']),'help':'Punto de partida para escenarios','tone':'primary'},
                {'label':'Proxy downside','value':fmt_money(percentiles[0][1]),'help':'Marcador visual P10 ilustrativo','tone':'danger'},
                {'label':'Proxy upside','value':fmt_money(percentiles[-1][1]),'help':'Marcador visual P90 ilustrativo','tone':'ok'},
            ],
            'highlights':[
                'MonteCarlo aquí es una página preliminar de trabajo, no una simulación estadística real.',
                'Se usa para reservar la experiencia visual antes de conectar el motor formal.',
                'La siguiente fase puede incorporar percentiles, drawdown y comparación entre estructuras.',
            ],
            'bars':[
                bar_card('Percentiles ilustrativos','Marcadores provisionales de dispersión',[
                    {'label':k,'value':v,'display':fmt_money(v),'tone':'primary' if k=='P50' else 'ok' if k=='P90' else 'danger'} for k,v in percentiles
                ])
            ],
            'tables':[
                as_table('Supuestos para futura simulación',['Componente','Estado'],[
                    ['Snapshot base del portafolio','Disponible'],
                    ['Precios spot en línea','Disponible'],
                    ['Motor Monte Carlo','Pendiente'],
                    ['Escenarios O2–O5 oficiales','Pendiente'],
                    ['Comparación entre portafolios','Pendiente'],
                ], 'Esta vista funciona como blueprint visual del modo MonteCarlo.')
            ],
            'callouts':[{'tone':'warn','title':'Importante','text':'Los percentiles mostrados son placeholders visuales y no deben interpretarse como forecast real.'}]
        }

    raise KeyError(slug)

@app.route('/')
def home():
    return render_template('index.html', modes=MODE_DEFS, master='5.3.5')

@app.route('/mode/<slug>')
def mode_page(slug):
    mode = MODES_BY_SLUG.get(slug)
    if not mode:
        abort(404)
    try:
        observed, dashboard = load_live_dashboard()
        payload = build_mode_payload(slug, dashboard, observed)
        return render_template('mode.html', mode=mode, payload=payload, error=None, master='5.3.5')
    except Exception as exc:
        return render_template('mode.html', mode=mode, payload=None, error=pretty_error(exc), master='5.3.5'), 503

@app.route('/health')
def health():
    return jsonify({'status':'UP','service':'Kairos Web','version':'3.2','snapshot_date':SNAPSHOT['units_snapshot_as_of']})

@app.route('/api/portfolio')
def portfolio():
    try:
        observed, dashboard = load_live_dashboard()
        return jsonify({'status':'OK', 'source':'Binance Spot MCP', 'observed_at':observed, **dashboard})
    except Exception as exc:
        app.logger.warning('portfolio MCP error: %s', type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':pretty_error(exc),'snapshot_date':SNAPSHOT['units_snapshot_as_of']}), 503

@app.route('/api/mcp-status')
def mcp_status():
    return jsonify({'binance_configured':bool(os.getenv('BINANCE_MCP_URL')),
                    'hyperliquid_configured':bool(os.getenv('HYPERLIQUID_MCP_URL')),
                    'hyperliquid_usage':'Macro HYPE only; no Binance/HYPE price fallback'})

@app.route('/api/hype-macro')
def hype_macro():
    try:
        data=asyncio.run(call_mcp('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                                  {'interval':'1w','start_date':'2024-11-29','limit':130}))
        if data.get('status') != 'OK':
            raise RuntimeError('Hyperliquid DATA_ERROR')
        return jsonify({'status':'OK','market':'HYPE/USDC spot, macro only','data':data})
    except Exception as exc:
        app.logger.warning('HYPE MCP error: %s', type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':pretty_error(exc)}),503

@app.route('/api/modes')
def modes_api():
    return jsonify({'status':'OK','execution':'PRELIMINARY_PAGES', 'read_only':True,
                    'modes':[dict(m, availability='PRELIMINARY_PAGE') for m in MODE_DEFS]})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
