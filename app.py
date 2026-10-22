"""KairosWeb: Google Sheets published state + Binance/Hyperliquid MCP only."""
import asyncio
import json
import math
import os
import secrets
import time
import threading
import uuid
import logging
import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from admin_origin import same_origin_allowed

from flask import Flask, Response, jsonify, render_template, request, abort, redirect, g, session, url_for
from fastmcp import Client
from wave_macro_context import resolve as resolve_weekly_wave_context, resolve_long_term_buy
from forecast_fibo_policy import defaults_from_master
from werkzeug.local import LocalProxy
from werkzeug.exceptions import HTTPException
from google_sheets_master import get_state, SheetDataError, public_failure_code, cache_status as sheet_cache_status
from hype_weekly import aggregate_weeks, HypeHistoryError
from portfolio_unrealized import summarize_unrealized, portfolio_allocation, category_allocation, pri_valuation_history, btc_equivalent
from custody_balancer import compare_custody, CustodyError
from orders_inbox import drift_tone, tradingbot_tokens
from kairos_sheets_features import (
    unread_alerts, mark_alert_read, mark_all_alerts_read, settings_data, prepare_changes,
    save_changes, homologate_current_snapshot, homologation_readiness, HomologationWorkflowError, SettingsError, _remote_data as _unused_remote_marker
)

BASE = Path(__file__).parent
APP_VERSION = '2.0.34'  # product release; distinct from Sheets schema_version=5.0.0
app = Flask(__name__)
# A dedicated administrator login is required; NEVER fall back to the Basic web password.
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
                  SESSION_COOKIE_SECURE=True, PERMANENT_SESSION_LIFETIME=timedelta(minutes=30))
app.secret_key = os.getenv('KAIROS_SESSION_SECRET', '') or None

# Bound to validated Google Sheets state, once per request.  No disk JSON source.
SNAPSHOT=LocalProxy(lambda:g.kairos_state['snapshot'])
COST_BASIS=LocalProxy(lambda:g.kairos_state['cost_basis'])
O2_LEVELS=LocalProxy(lambda:g.kairos_state['o2_levels'])
TOKENS=LocalProxy(lambda:g.kairos_state['tokens'])
TARGETS=LocalProxy(lambda:g.kairos_state['targets'])
TIERS=LocalProxy(lambda:g.kairos_state['tiers'])
PARAMETERS=LocalProxy(lambda:g.kairos_state['parameters'])
BSI_ARCHIVE=LocalProxy(lambda:g.kairos_state['bsi_archive'])
INTEGRAL=LocalProxy(lambda:g.kairos_state['integral'])

def approved_numeric(key):
    row=PARAMETERS.get(key)
    if not row or row['status'] not in ('APROBADO','APROBADO_CONDICIONAL'):
        raise SheetDataError(f'12_PARAMETROS_KAIROS: {key} no aprobado')
    return float(row['value'])

def policy_numeric(key, allowed):
    row=PARAMETERS.get(key)
    if not row or row['status'] not in allowed:
        raise SheetDataError(f'12_PARAMETROS_KAIROS: {key} not permitted')
    return float(row['value'])

MODE_DEFS = [
    {'slug':'portafolio','name':'Portafolio','subtitle':'Visión ejecutiva y valoración en BTC','description':'Única página principal: distribución, balance, rentabilidad y custodia.'},
    {'slug':'balancer','name':'Balancer','subtitle':'Rebalanceo y liquidez','description':'Propuestas de rebalanceo, control de piso de liquidez y protección de Core.'},
    {'slug':'compras','name':'Compras','subtitle':'Despliegue de liquidez','description':'Retrocesos desde P1 semanal PROPUESTO/VALIDADO/CONFIRMADO y P2 máximo posterior; solo simulaciones INFRA.'},
    {'slug':'ventas','name':'Ventas','subtitle':'Objetivo USDT','description':'Propuestas solo SELL para acercarse a la meta de liquidez y reducir sobrepeso.'},
    {'slug':'forecast','name':'Forecast','subtitle':'Cycle Low → O5','description':'Tabla de niveles O2C1–O2C4 y ondas/pivotes proyectados; todo es simulación.'},
    {'slug':'ordenes','name':'Órdenes','subtitle':'Bandeja de propuestas','description':'Balance de portafolio y objetivos LIMIT Fibonacci 1W, por exchange y token; fase 1 solo lectura.'},
    {'slug':'tradingbot','name':'TradingBot','subtitle':'Táctico 4H','description':'Vista táctica preliminar para la reserva de trading y activos de seguimiento.'},
]
# Future mode enablement is centralized: disabled modes do not appear in any global nav.
ENABLED_MODE_SLUGS = tuple(x['slug'] for x in MODE_DEFS)

MODES_BY_SLUG = {m['slug']: m for m in MODE_DEFS}
# Short TTL protects the MCP service from 10 simultaneous page loads, without
# ever labeling cached observations as real-time without their original time.
_MARKET_CACHE = {'stored': 0.0, 'observed': None, 'prices': None}
_MARKET_LOCK = threading.Lock()
_FETCH_LOCK = threading.Lock()
CACHE_TTL_SECONDS = 30
RETRY_HTTP_CODES = frozenset((502, 503, 504))
MCP_RETRY_DELAYS = (2, 5, 10)
MCP_TIMEOUT_SECONDS = 35


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

@app.before_request
def bind_published_sheet():
    # The health and diagnostics endpoints remain reachable during source outages.
    independent={'/health','/api/mcp-status','/api/mcp-config-check','/api/mcp-diagnostics',
                 '/api/alerts/unread','/api/alerts/read','/api/alerts/read-all',
                 '/api/market-status','/api/modes','/api/hype-macro','/api/sheets-status', '/api/mcp-refresh', '/api/health/diagnostics'}
    if request.path in independent or request.path in ('/admin/login','/api/admin/session') or request.path=='/settings' or request.path.startswith('/static/'):
        return None
    try:
        g.kairos_state=get_state()
        return None
    except Exception as exc:
        incident=uuid.uuid4().hex[:10]
        app.logger.error('Kairos Sheets DATA_ERROR id=%s category=%s class=%s',incident,public_failure_code(exc),type(exc).__name__)
        msg='Google Sheets Master no disponible o no cumple el esquema PUBLICADO 5.0.0. No se utilizan snapshots locales.'
        if request.path.startswith('/api/'):
            return jsonify({'status':'DATA_ERROR','origin':'GOOGLE_SHEETS','reason':msg,'category':public_failure_code(exc),'error_id':incident}),503
        return render_template('sheet_error.html',master=APP_VERSION,error_id=incident,message=msg),503

@app.after_request
def headers(resp):
    resp.headers['Cache-Control'] = 'no-store'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    resp.headers['Referrer-Policy'] = 'same-origin'
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
    async with Client(transport, timeout=MCP_TIMEOUT_SECONDS) as client:
        result = await client.call_tool(tool, args or {})
    if result.is_error:
        raise RuntimeError(f'{tool}: error remoto')
    if isinstance(result.data, dict):
        payload = result.data
        # Some MCP providers wrap the application payload in structuredContent.
        if 'structuredContent' in payload and isinstance(payload['structuredContent'], dict):
            return payload['structuredContent']
        return payload
    for block in result.content:
        if getattr(block, 'type', None) == 'text':
            value = json.loads(block.text)
            if isinstance(value, dict):
                return value
    raise RuntimeError(f'{tool}: respuesta MCP no reconocida')

def call_mcp_resilient(env_name, tool, args=None):
    """Fresh MCP sessions each attempt; retry only gateway errors/timeouts.

    Keep diagnostics/HTML and the live market loader on a shared retry policy.
    Never retry authorization, application errors, or malformed URLs.
    """
    for attempt in range(len(MCP_RETRY_DELAYS) + 1):
        try:
            return asyncio.run(call_mcp(env_name, tool, args))
        except Exception as exc:
            status = _http_status(exc)
            timeout = isinstance(exc, (TimeoutError, httpx.TimeoutException)) or 'timeout' in type(exc).__name__.lower()
            if attempt >= len(MCP_RETRY_DELAYS) or (status not in RETRY_HTTP_CODES and not timeout):
                raise
            delay = MCP_RETRY_DELAYS[attempt]
            app.logger.warning('MCP transient retry provider=%s tool=%s attempt=%s http_status=%s wait_s=%s',
                               'binance' if env_name=='BINANCE_MCP_URL' else 'hyperliquid', tool,
                               attempt + 1, status if status is not None else 'timeout', delay)
            time.sleep(delay)


def market_cache_status():
    """Only metadata from last valid observation; stale valuations are never served."""
    with _MARKET_LOCK:
        observed = _MARKET_CACHE['observed']
        stored = _MARKET_CACHE['stored']
    age = round(max(0.0, time.monotonic() - stored), 1) if observed else None
    return {'last_valid_observed_at':observed, 'cache_age_seconds':age,
            'cache_state':'FRESH' if observed and age < CACHE_TTL_SECONDS else ('STALE' if observed else 'EMPTY')}


def _http_status(exc):
    """Find real HTTP status through wrappers without logging URL or headers."""
    seen=set()
    pending=[exc]
    while pending:
        current=pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, httpx.HTTPStatusError):
            return current.response.status_code
        for nxt in (getattr(current, '__cause__', None), getattr(current,'__context__',None)):
            if nxt is not None:
                pending.append(nxt)
        group=getattr(current, 'exceptions', None)
        if group:
            pending.extend(group)
    return None

def diagnostic_error(exc, scope):
    error_id=uuid.uuid4().hex[:10]
    http_status=_http_status(exc)
    etype=type(exc).__name__
    msg=str(exc).lower()
    # Safe structured logging: never log exception text, headers, URLs or tokens.
    app.logger.error('Kairos MCP failure ID=%s scope=%s exception=%s http_status=%s',
                     error_id,scope,etype,http_status if http_status is not None else 'n/a')
    if http_status in (401,403):
        category='AUTH'; hint='El MCP respondió con un error de autorización.'
    elif http_status in (404,405,406,415):
        category='ENDPOINT'; hint='Revisa la ruta MCP o la negociación del protocolo HTTP.'
    elif http_status == 429:
        category='RATE_LIMIT'; hint='El MCP aplicó un límite de solicitudes.'
    elif http_status is not None and http_status >= 500:
        category='UPSTREAM_HTTP'; hint='El servicio MCP devolvió un error del servidor.'
    elif http_status is not None:
        category='UPSTREAM_HTTP'; hint='El servicio MCP devolvió una respuesta HTTP fallida.'
    elif 'no configurada' in msg:
        category='NOT_CONFIGURED'; hint='Falta configurar la URL MCP.'
    elif 'url debe usar https' in msg:
        category='INVALID_URL'; hint='La URL MCP debe usar HTTPS.'
    elif isinstance(exc,(TimeoutError,httpx.TimeoutException)) or 'timeout' in etype.lower():
        category='TIMEOUT';hint='Se agotó el tiempo de espera del servicio MCP.'
    elif 'stale' in msg:
        category='STALE_DATA';hint='Las cotizaciones no cumplen el límite de frescura.'
    elif 'missing one' in msg or 'invalid records' in msg:
        category='INCOMPLETE_DATA';hint='La respuesta no contiene todas las cotizaciones requeridas.'
    else:
        category='MCP_ERROR';hint='Consulta los logs privados usando el ID del error.'
    return {'code':category,'message':hint,'error_id':error_id,
            'exception_type':etype,'http_status':http_status}

def pretty_error(exc):
    if isinstance(exc, RuntimeError) and ('no configurada' in str(exc) or 'debe usar HTTPS' in str(exc)):
        return str(exc)
    return 'MCP sin respuesta válida. Revisar conectividad y logs de Render.'

def fmt_money(v):
    return f"${v:,.0f}" if abs(v) >= 100 else f"${v:,.2f}"

def fmt_price(v):
    """Display token price with up to five decimals, retaining raw arithmetic precision."""
    if v is None or not math.isfinite(float(v)) or v <= 0:
        return 'N/D'
    if 0 < v < 0.00001:
        return '$<0.00001'
    return f'${v:,.5f}'.rstrip('0').rstrip('.')

def fmt_pct(v):
    return f"{v:.1f}%"

def tone_from_drift(d, band_pp=None):
    # The same MASTER-approved band drives classification and visual styling.
    band=approved_numeric('DRIFT_BAND_PP') if band_pp is None else float(band_pp)
    if not math.isfinite(band) or band < 0:
        raise SheetDataError('DRIFT_BAND_PP: invalid band')
    return drift_tone(d,band)

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
    # This is an archived 4H-synchronized MCP sample, NOT a live BSI signal.
    # Do NOT mix old TradingView anchors with current Binance quotes for trading.
    archive=list(BSI_ARCHIVE)
    out=[]
    for row in archive:
        if row['token']=='BTC':continue
        try: value=float(row['sample_bsi']) if row['sample_bsi'] is not None else None
        except (TypeError,ValueError): value=None
        out.append({'token':row['token'],'bsi':round(value,2) if value is not None else None,
                    'status':'MCP_ARCHIVE_INFO_ONLY'})
    return {'status':'INFORMATIVE_ONLY','anchor_date':'2026-10-05',
            'basis':'Muestra MCP histórica 4H archivada en Google Sheets (candidata, no homologada)',
            'sample_close_utc':archive[0]['sample_close_utc'] if archive else None,
            'signals_enabled':False,
            'note':'BSI SELL BLOQUEADO: anclas, baseline y HWM monetizado sin certificar.',
            'rows':sorted(out,key=lambda x:(x['bsi'] is None,-(x['bsi'] or 0)))}

def forecast_sensitivity(rows, usdt):
    btc_value=next((r['value'] for r in rows if r['token']=='BTC'),0.0)
    base=sum(r['value'] for r in rows)+usdt
    shocks=[-30,-15,0,15,30]
    return {'status':'ILLUSTRATIVE_ONLY','model':'BTC price shock, altcoins and USDT unchanged, no transactions',
            'base_portfolio':base,'btc_units':SNAPSHOT['holdings_total']['BTC'],
            'scenarios':[{'btc_change_pct':s,'portfolio_value':round(base+btc_value*s/100,2),
                          'portfolio_change_pct':round((btc_value*s/100)/base*100,2) if base else 0} for s in shocks],
            'official_forecast':'NOT_CONNECTED','note':'NO es Forecast O2-O5 ni predicción. Falta motor y precios hipotéticos por onda.'}

def portfolio_profitability(rows):
    """Rank indicative unrealized P&L by user-declared average acquisition cost. Missing != zero."""
    results=[]
    for row in rows:
        basis=COST_BASIS.get(row['token'])
        if not isinstance(basis,(int,float)) or isinstance(basis,bool) or basis <= 0 or row['units'] <= 0:
            continue
        pnl=row['units']*(row['price']-basis)
        results.append({'token':row['token'],'cost_basis_usdt':basis,'pnl_usdt':round(pnl,2),
                        'pnl_pct':round((row['price']/basis-1)*100,2)})
    return {'status':'PARTIAL' if len(results)<len(rows) else 'OK',
            'basis':'P&L no realizado estimado vs costo promedio declarado por usuario',
            'verified_count':len(results),'missing_count':len(rows)-len(results),
            'top5':sorted(results,key=lambda r:r['pnl_pct'],reverse=True)[:5]}

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
        custody = SNAPSHOT['custody_core_blocked__core_strategic__exchange'].get(key, [0,0,0])
        rows.append({'token':market_key,'tier':TIERS[token], 'target':TARGETS[token],
                     'units':units,'hodl_units':float(custody[0]),'core_units':float(custody[1]),
                     'exchange_units':float(custody[2]),'price':price,'value':value,
                     'avg_cost':float(COST_BASIS[market_key]) if isinstance(COST_BASIS.get(market_key),(int,float)) and COST_BASIS.get(market_key)>0 else None,
                     'pnl_pct':(price/float(COST_BASIS[market_key])-1)*100 if isinstance(COST_BASIS.get(market_key),(int,float)) and COST_BASIS.get(market_key)>0 else None})
    for row in rows:
        row['weight']=row['value']/portfolio_crypto if portfolio_crypto else 0
        row['drift_pp']=(row['weight']-row['target'])*100
        band=approved_numeric('DRIFT_BAND_PP')
        row['status']='SOBRE' if row['drift_pp']>band else 'INFRA' if row['drift_pp'] < -band else 'NEUTRAL'
    liquidity=SNAPSHOT['physical_total_USDT']
    trading=SNAPSHOT['trading_real_fixed_USDT']
    total_value = portfolio_crypto+liquidity
    btc_usdt_spot = prices['BTC']
    total_btc_equivalent = btc_equivalent(total_value, btc_usdt_spot)
    return {
        'rows': rows,
        'crypto_value': portfolio_crypto,
        'usdt_total':liquidity,
        'usdt_operating':SNAPSHOT['kairos_operating_USDT_before_commitments'],
        'trading_reserve':trading,
        'total_value':total_value,
        'total_btc_equivalent':total_btc_equivalent,
        'btc_usdt_spot':btc_usdt_spot,
        'usdt_pct':liquidity/total_value if total_value else 0,
        'crypto_pct':portfolio_crypto/total_value if total_value else 0,
        'snapshot_date':SNAPSHOT['units_snapshot_as_of'],
        'note':f"Google Sheets PUBLICADO {g.kairos_state['control']['snapshot_id']} · Corte {SNAPSHOT['units_snapshot_as_of']}. No se leen balances privados de exchanges.",
        'liquidity_venues':SNAPSHOT['liquidity_venues_USDT'],
        'liquidity_floor_usdt':total_value*approved_numeric('STRUCTURAL_USDT_TARGET'),
        'liquidity_headroom_usdt':liquidity-total_value*approved_numeric('STRUCTURAL_USDT_TARGET'),
        'custody_summary':custody_summary(prices),
        'profitability': portfolio_profitability(rows),
        'bsi_historical':historical_bsi(prices),
        'forecast_sensitivity':forecast_sensitivity(rows,liquidity)
    }

def _load_live_dashboard_uncached():
    with _MARKET_LOCK:
        if _MARKET_CACHE['prices'] is not None and (time.monotonic() - _MARKET_CACHE['stored']) < CACHE_TTL_SECONDS:
            return _MARKET_CACHE['observed'], core_dashboard(dict(_MARKET_CACHE['prices']))
    # Shared resilient fetch with fresh session for each transient gateway failure.
    data = call_mcp_resilient('BINANCE_MCP_URL', 'get_kairos_spot_prices')
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
        _MARKET_CACHE.update(stored=time.monotonic(), observed=observed, prices=dict(prices))
    return observed, dashboard

def load_live_dashboard():
    # One in-flight market fetch per application process, shared by all pages.
    # The cache contains a real timestamp and is never used beyond TTL.
    with _FETCH_LOCK:
        return _load_live_dashboard_uncached()

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
    band=approved_numeric('DRIFT_BAND_PP')
    under = top_n(rows, key=lambda r: r['drift_pp'], n=6, reverse=False, predicate=lambda r: r['drift_pp'] < -band)
    over = top_n(rows, key=lambda r: r['drift_pp'], n=6, reverse=True, predicate=lambda r: r['drift_pp'] > band)
    sellable_over = [r for r in over if r['token'] != 'BTC']
    bsi_rows = [r for r in d['bsi_historical']['rows'] if r['bsi'] is not None]
    top_bsi = sorted(bsi_rows, key=lambda x: x['bsi'], reverse=True)[:6]
    top_pos = rows[0]
    top3_conc = sum(r['weight'] for r in rows[:3])
    usdt_gap = d['liquidity_floor_usdt'] - d['usdt_total']
    fibo_allocations=defaults_from_master(g.kairos_state['parameters'])
    o2_weights=fibo_allocations['o2']
    c1_budget = d['total_value'] * 0.25 * (o2_weights[1]/100)  # historical Fib 50% = O2C2
    c2_budget = d['total_value'] * 0.25 * (o2_weights[2]/100)  # historical Fib 61.8% = O2C3
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
        return balancer_report(d, observed)
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
                bar_card('BTC Strength Index (BSI)','Información relativa frente a BTC (referencial)',[
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

    if slug in ('compras','forecast'):
        p=d['total_value']; cash=d['usdt_total']; trading=d['trading_reserve']
        max_percent=(100*max(0.0,cash-trading)/p) if p else 0.0
        reference_cap=max(0.0,cash-trading)
        purchase_tokens=[{'token':r['token'],'tier':r['tier'],'price':r['price'],'weight':r['weight'],'target':r['target'],
            'current_usdt':r['value'],'units':r['units'],
            'gap_usdt':max(0.0,(r['target']-r['weight'])*d['crypto_value']),
            'c1_price':None,
            'c2_price':None}
            for r in d['rows']]
        purchase_current={'P':p,'cash':cash,'trading':trading,'cash_pct':d['usdt_pct']*100,
             'floor':approved_numeric('STRUCTURAL_USDT_TARGET')*p,'max_percent':max_percent,'reference_cap':reference_cap,
             'crypto_value':d['crypto_value']}
    if slug in ('compras','forecast'):
        # Shared CL -> weekly O1 -> O2 Fibonacci source for every scenario.
        # The historical C1/C2 archive is NEVER inverted to synthesize O1.
        from concurrent.futures import ThreadPoolExecutor
        from pivot_preload import archive_candidates, ARCHIVE_A1
        from kairos_sheets_features import read_ranges
        try:
            archive=archive_candidates(read_ranges({'archive':ARCHIVE_A1})['archive'],g.kairos_state['parameters'])
            archive_by_token={a['token']:a for a in archive}
        except Exception:
            archive_by_token={}
        pub=g.kairos_state['wave_pivots']
        def weekly_reference(row):
            token=row['token']; source_token='PUMPFUN' if token=='PUMP' else token
            try:
                if source_token=='HYPE':
                    data=call_mcp_resilient('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                        {'interval':'1d','start_date':'2024-11-29','limit':750})
                else:
                    # For proposed previews, retain the dated CL week even
                    # when 365-day history would begin after the CL.
                    from cl_review_history import fetch_closed_binance_history
                    candidate_cl=(pub.get(token,{}) or {}).get('cl_date') or (archive_by_token.get(source_token,{}) or {}).get('cl_date')
                    if candidate_cl:
                        data=fetch_closed_binance_history(call_mcp_resilient,token,candidate_cl)
                    else:
                        data=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',
                            {'symbol':token+'USDT','interval':'1d','limit':365})
                return token,(resolve_long_term_buy(source_token,pub.get(token,{}),data,archive_by_token.get(source_token,{})) if slug=='compras'
                    else resolve_weekly_wave_context(source_token,pub.get(token,{}),
                    archive_by_token.get(source_token,{}),data))
            except Exception:
                return token,{'status':'MCP_DATA_ERROR','eligible':False,'levels':None,
                    'history':{'status':'DATA_ERROR'},'anchors':None, 'reason':'MCP_REQUERIDO_NO_DISPONIBLE'}
        with ThreadPoolExecutor(max_workers=6) as pool:
            weekly_context=dict(pool.map(weekly_reference,purchase_tokens))
        weekly_levels={token:(ctx.get('levels') or {}) for token,ctx in weekly_context.items()}
        weekly_histories={token:ctx.get('history',{'status':'N/D'}) for token,ctx in weekly_context.items()}
    if slug == 'compras':
        return {'o2_histories':weekly_histories,'generated_at':observed,'status_badge':'LIVE MCP · SIMULACIÓN','snapshot_note':d['note'],
            'kind':'compras', 'current':purchase_current, 'tokens':purchase_tokens,
            'o2_level_reference':'MCP_WEEKLY_PROPOSED_OR_VALIDATED_SIMULATION_ONLY',
            'forecast_o2_allocation':o2_weights, 'o2_levels':weekly_levels,
            'buy_eligibility':{t:bool(c.get('eligible',False)) for t,c in weekly_context.items()},
            'buy_stage_weights':{t:(fibo_allocations['o4'] if c.get('mode')=='O4' else o2_weights)
                                  for t,c in weekly_context.items()},
            'weekly_context':weekly_context,
            'drift_band_pp':approved_numeric('DRIFT_BAND_PP'),
            'structural_liquidity_target':approved_numeric('STRUCTURAL_USDT_TARGET'),
            'notes':['Compras: P1 es el último mínimo semanal fechado (PROPUESTO/VALIDADO/CONFIRMADO); P2 es el mayor máximo semanal cerrado posterior.',
             'O2 aplica sus pesos; O4 sus pesos; retroceso alcista genérico utiliza pesos O2 publicados.',
             'Sin P1 con fecha/precio válidos o sin máximo semanal posterior P2: USDT 0. PROPUESTO permite simulación, nunca ejecución real; compra solo INFRA y fondo no gastado queda en USDT.',
             'Ventas ordinarias y Forecast hipotético no heredan este bloqueo. Simulación no genera órdenes.']}
        buy_rows=[]
        for r in under:
            share = abs(r['drift_pp'])/deficits_sum
            buy_rows.append([r['token'], fmt_pct(r['weight']*100), fmt_pct(r['target']*100), f"{r['drift_pp']:.1f} pp", fmt_money(c1_budget*share), fmt_money(c2_budget*share)])
        return {
            **common,
            'metrics':[
                {'label':'USDT operativo','value':fmt_money(d['usdt_operating']),'help':'Antes de compromisos y fees','tone':'ok'},
                {'label':'O2C2 Fib 50% · presupuesto orientativo','value':fmt_money(c1_budget),'help':'Tramo variable del 25% de P','tone':'primary'},
                {'label':'O2C3 Fib 61.8% · presupuesto orientativo','value':fmt_money(c2_budget),'help':'Tramo variable del 25% de P','tone':'primary'},
                {'label':'Activos con déficit','value':str(len(under)),'help':'Con banda de -1 pp','tone':'warn'},
            ],
            'highlights':[
                'Referencias históricas C1/C2 equivalen a O2C2 (50%) y O2C3 (61.8%), respectivamente; no son órdenes nuevas.',
                'Esta página todavía no trae anchors O2/O4 ni calcula precios límite finales.',
                'La distribución mostrada es visual y proporcional al déficit actual de composición.',
            ],
            'bars':[
                bar_card('Déficit por token','Prioridad relativa para nuevas compras',[
                    {'label':r['token'],'value':abs(r['drift_pp']),'display':f"{r['drift_pp']:.1f} pp",'tone':'warn'} for r in under
                ])
            ],
            'tables':[
                as_table('Candidatos estructurales',['Token','Peso actual','Target','Déficit','O2C2 ref. Fib 50%','O2C3 ref. Fib 61.8%'], buy_rows,
                         'Montos referenciales; los precios Fib y la estructura aún no están conectados.')
            ],
            'callouts':[{'tone':'warn','title':'Pendiente de integración','text':'Para igualar la salida de ChatGPT faltan los anchors aprobados O1/O3/O4, los precios Fib y las órdenes existentes por exchange.'}]
        }

    if slug == 'ventas':
        stage1=PARAMETERS.get('SALES_STAGE_1',{})
        stage2=PARAMETERS.get('SALES_STAGE_2',{})
        if stage1.get('value')!='SELL_SOBRE_EXCHANGE_FREE_FIRST' or stage1.get('status')!='APROBADO' or stage2.get('value')!='SELL_REST_MINIMIZE_SQUARED_PP_DRIFT' or stage2.get('status')!='APROBADO_SIMULACION':
            raise SheetDataError('VENTAS: etapa 2 optimizada aún no aprobada en MASTER')
        p=d['total_value']; cash=d['usdt_total']
        custody=SNAPSHOT['custody_core_blocked__core_strategic__exchange']
        sell_tokens=[]
        # Todos los activos no-BTC son potenciales fuentes de venta una vez agotados los sobreponderados.
        # El inventario disponible se limita a Exchange confirmado por snapshot, no a Core/HODL.
        for r in d['rows']:
            # BTC appears in the weights comparator; optimizer sets hard SELL cap=0.
            key='PUMPFUN' if r['token']=='PUMP' else r['token']
            exch=max(0.0,float(custody.get(key,[0,0,0])[2]))
            value=max(0.0,exch*r['price'])
            excess=max(0.0,(r['weight']-r['target'])*d['crypto_value'])
            sell_tokens.append({'token':r['token'],'price':r['price'],'weight':r['weight'],
                                'target':r['target'],'exchange_units':exch,
                                'units':r['units'],'tier':r['tier'],'reserved_sell_units':float(r.get('reserved_sell_units',0)),
                                'max_usdt':min(excess,value), 'free_exchange_usdt':value,
                                'overweight':r['drift_pp']>band})
        return {'generated_at':observed,'status_badge':'LIVE MCP · SIMULACIÓN','snapshot_note':d['note'],'kind':'ventas','current':{'P':p,'cash':cash,'cash_pct':d['usdt_pct']*100,'floor':approved_numeric('STRUCTURAL_USDT_TARGET')*p,'max_percent':max(100*policy_numeric('SLIDER_MAX_SIMULATED_USDT_TARGET',{'APROBADO_SIMULACION'}),d['usdt_pct']*100),'default_percent':100*approved_numeric('ORDINARY_DEFAULT_USDT_TARGET'),'trading':d['trading_reserve'],'band_pp':band},'tokens':sell_tokens, 'notes':['Solo SELL; BTC NEVER SELL. No se altera Core/HODL.','Slider hasta la meta simulada configurada en Google Sheets; 40% no es límite del simulador.','Inventario referencial de Exchange; usuario declara 0 órdenes y 0 fills pendientes, sin certificación remota del exchange.']}
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
        tb_policy={'reserve_usdt':d['trading_reserve'],
            'max_loss_fraction':approved_numeric('QF_ACCOUNT_RISK_PER_TRADE'),
            'max_margin_fraction':approved_numeric('QF_MARGIN_CAP_PER_POSITION'),
            'max_risk_total_fraction':approved_numeric('QF_ACCOUNT_RISK_TOTAL'),
            'max_positions':int(approved_numeric('MAX_OPEN_POSITIONS')),
            'max_leverage':approved_numeric('MAX_LEVERAGE'),
            'min_rr':approved_numeric('RISK_REWARD_MIN'),
            'power_buying_reference':policy_numeric('QF_POWER_BUYING_REFERENCE',{'REFERENCIA_USUARIO_NO_BALANCE'})}
        allowed=tradingbot_universe()
        watch = [r for r in rows if r['token'] in allowed]
        return {
            **common,
            'tb_risk_policy':tb_policy,
            'metrics':[
                {'label':'Reserva Trading','value':fmt_money(d['trading_reserve']),'help':'Bolsa separada de Quantfury','tone':'primary'},
                {'label':'Activos watchlist','value':str(len(watch)),'help':'Núcleo táctico inicial','tone':'neutral'},
                {'label':'Motor táctico','value':'Preliminar','help':'No conectado aún al framework 4H','tone':'warn'},
                {'label':'Acciones habilitadas','value':'Solo lectura','help':'Sin envío de órdenes','tone':'ok'},
            ],
            'highlights':[
                'TradingBot debe vivir separado del portafolio estructural y de las compras por tramos O2C1–O2C4.',
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
            if abs(r['drift_pp']) > approved_numeric('DRIFT_BAND_PP'):
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
        pivot_rows=[]
        for r in purchase_tokens:
            ctx=weekly_context[r['token']]
            anchors=ctx.get('anchors') or {}
            pair=ctx.get('levels') or {}
            w=g.kairos_state['wave_pivots'].get(r['token'],{})
            pivot_rows.append({'token':r['token'],'c1':pair.get('c1'),'c2':pair.get('c2'),
                'ref382':pair.get('ref382'),'ref786':pair.get('ref786'),
                'cycle_low':anchors.get('CL'),'o1':anchors.get('O1'),
                'o1_date':anchors.get('O1_date'),
                'published_cl':w.get('cycle_low'),'published_cl_date':w.get('cl_date'),
                'cl_status':w.get('cl_status','PROPUESTO'),'waves':w.get('waves',{}),
                'anchor_state':ctx.get('status')})
        # Both O3/O5 allocation pairs come from the currently PUBLICADO Sheet.
        # If either is pending, malformed or no longer totals 100%, fail closed.
        split_o3=(approved_numeric('O3_BTC_PROCEEDS_FRACTION'),approved_numeric('O3_USDT_PROCEEDS_FRACTION'))
        split_o5=(approved_numeric('O5_BTC_PROCEEDS_FRACTION'),approved_numeric('O5_USDT_PROCEEDS_FRACTION'))
        if any(x < 0 or x > 1 or not math.isfinite(x) for x in (*split_o3,*split_o5)) or any(abs(sum(pair)-1)>1e-8 for pair in (split_o3,split_o5)):
            raise SheetDataError('12_PARAMETROS_KAIROS: reparto BTC/USDT O3/O5 debe sumar 100% en cada onda')
        return {'generated_at':observed,'status_badge':'LIVE MCP · SIMULACIÓN','snapshot_note':d['note'],
            'kind':'forecast', 'current':purchase_current,'tokens':purchase_tokens, 'custody':{('PUMP' if k=='PUMPFUN' else k):v for k,v in SNAPSHOT['custody_core_blocked__core_strategic__exchange'].items()}, 'cash_total':d['usdt_total'], 'trading_reserve':d['trading_reserve'],
            'pivot_rows':pivot_rows, 'o2_source':'WEEKLY_STRUCTURAL_CANDIDATE',
            'custody_policy':g.kairos_state['custody_policy'],
            'c1_share':defaults_from_master(g.kairos_state['parameters'])['o2'][1]/100,
            'official_o3_split':split_o3[0], 'official_o3_usdt_split':split_o3[1],
            'official_o5_split':split_o5[0], 'official_o5_usdt_split':split_o5[1],
            'o3_liquidity_target':approved_numeric('STRUCTURAL_USDT_TARGET'),
            'forecast_fibo_allocations':__import__('forecast_fibo_policy').defaults_from_master(g.kairos_state['parameters']),
            'reference_type':'O2_ANCHORED_TO_WEEKLY_CL_O1',
            'notes':['Retrocesos simulados 38.2%, 50%, 61.8% y 78.6%; máximo USDT físico menos ReservaTrading QF, sin tope de 25% P.',
               'Las columnas históricas C1 Fib 50% y C2 Fib 61.8% se presentan como O2C2 y O2C3; no son órdenes activas.',
               'CL/O1 provienen de referencias publicadas o candidatos semanales UTC; no se infieren inversamente desde Fibonacci.',
               'O2/O3/O4/O5 son escenarios hipotéticos con parámetros ajustables; no son señales Elliott ni objetivos aprobados.',
               'La simulación de Forecast NO calcula BTC acumulado oficial ni probabilidades. Sin órdenes ni fills.']}

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


def balancer_report(d, observed):
    """Read-only liquidity accounting and independent illustrative buy/sell projections.

    Commitments cannot be inferred from this static snapshot; don't label theoretical
    capacity as real executable cash.
    """
    rows=sorted(d['rows'],key=lambda r:r['value'],reverse=True)
    p=d['total_value']; cash=d['usdt_total']; crypto=d['crypto_value']
    floor=approved_numeric('STRUCTURAL_USDT_TARGET')*p
    excess=max(0,cash-floor)
    gap=max(0,floor-cash)
    operational_25=.25*p  # forecast purchase envelope; legacy C1/C2 are NOT added
    c1=operational_25; c2=0.0  # read-only compatibility for older templates
    trading=d['trading_reserve']
    operational_25=.25*p
    residual_after_bags=cash-operational_25-trading
    # The 5% P is a non-binding reference. Formula approved by the user displays
    # what remains in physical USDT after protecting C1+C2 and Trading.
    if PARAMETERS['BALANCER_RESERVE_FORMULA']['status']!='APROBADO' or PARAMETERS['BALANCER_RESERVE_FORMULA']['value']!='MAX(0,USDT_TOTAL-0.25*P-QF_REAL)':
        raise SheetDataError('Balancer formula has changed; engine revalidation required')
    reserve=max(0,residual_after_bags)
    reserve_nominal=policy_numeric('BALANCER_NOMINAL_REFERENCE_P',{'REFERENCIA_NO_TOPE'})*p
    # Indicative ONLY; actual commitments and reserved bags are not reconciled.
    theoretical_ceiling=max(0,min(excess,residual_after_bags,reserve+excess))
    band=approved_numeric('DRIFT_BAND_PP')
    # Custody Balancer: published 02_POSICIONES + 04_CUSTODIA, unit-only calculation.
    # The comparison does not assume orders filled or any custody transfer.
    custody_positions = {
        ('PUMPFUN' if r['token']=='PUMP' else r['token']): {
            'tier':r['tier'], 'units':r['units'], 'hodl':r['hodl_units'],
            'core':r['core_units'], 'exchange':r['exchange_units']
        } for r in d['rows']
    }
    custody_comparison = compare_custody(custody_positions, g.kairos_state['custody_policy'])
    buy_candidates=[r for r in rows if r['drift_pp'] < -band]
    sell_candidates=[r for r in rows if r['drift_pp'] > band and r['token']!='BTC']
    from orders_inbox import allocate_infra_buys, overweight_sell_plan
    # Reader certifies 05_ORDENES contains no operational open orders.
    # This is *only* the published ledger, NOT live exchange verification.
    sale_preview=overweight_sell_plan(rows,band)
    sale_total=sum(x['value'] for x in sale_preview)
    current_cash_capacity=reserve
    # Conditional scenario: sale proceeds are hypothetical until fill is verified.
    projected_cash_capacity=reserve+sale_total
    buy_preview=allocate_infra_buys(rows,current_cash_capacity,band)
    buy_total=sum(x['value'] for x in buy_preview)
    sold_by_token={x['token']:x['value'] for x in sale_preview}
    conditional_rows=[{**r,'value':r['value']-sold_by_token.get(r['token'],0.)} for r in rows]
    conditional_crypto=max(0.,crypto-sale_total)
    for r in conditional_rows:
        r['weight']=r['value']/conditional_crypto if conditional_crypto else 0.0
        r['drift_pp']=(r['weight']-r['target'])*100
    conditional_buys=allocate_infra_buys(conditional_rows,projected_cash_capacity,band)
    conditional_by_token={x['token']:x['value'] for x in conditional_buys}
    # Keep all conditional candidates visible, including INFRA created by a
    # hypothetical sale. The 'after sales' column is purely conditional.
    initial_by_token={x['token']:x for x in buy_preview}
    displayed={r['token']:r for r in buy_candidates}
    displayed.update({r['token']:r for r in rows if r['token'] in conditional_by_token})
    buy_preview=[initial_by_token.get(token,{'token':token,'value':0.,'reference':0.,
                 'weight':r['weight'],'target':r['target'],'drift':r['drift_pp']})
                 for token,r in displayed.items()]
    buy_with_sales=[{'token':r['token'],'value':conditional_by_token.get(r['token'],0.)}
                    for r in buy_preview]
    buy_total_after_sales=sum(x['value'] for x in conditional_buys)
    # Independent outcomes: BUY-only and SELL-only, never count proceeds as real.
    after_buy_crypto=crypto+buy_total
    after_sell_crypto=max(0,crypto-sale_total)
    bought={x['token']:x['value'] for x in buy_preview}
    buy_weights={r['token']:(r['value']+bought.get(r['token'],0.))/after_buy_crypto if after_buy_crypto else 0 for r in rows}
    sell_weights={r['token']:(r['value']-sold_by_token.get(r['token'],0.))/after_sell_crypto if after_sell_crypto else 0 for r in rows}
    return {'generated_at':observed,'snapshot_note':d['note'],'status_badge':'MCP Spot + Sheets PUBLICADO',
      'current':{'P':p,'cash':cash,'crypto':crypto,'floor':floor,'gap':gap,'excess':excess,
                 'reserve':reserve,'current_cash_capacity':current_cash_capacity,'projected_cash_capacity':projected_cash_capacity,'reserve_nominal':reserve_nominal,'residual_after_bags':residual_after_bags,'operational_25':operational_25,'c1':c1,'c2':c2,'trading':trading,
                 'operating':d['usdt_operating'],'buy_ceiling':theoretical_ceiling},
      'metrics':[
        {'label':'USDT físico','value':fmt_money(cash),'help':f"{cash/p*100:.1f}% del patrimonio" if p else '', 'tone':'primary'},
        {'label':'Meta estructural USDT','value':fmt_money(floor),'help':'Protección de liquidez','tone':'neutral'},
        {'label':'Reserva Balancer estimada','value':fmt_money(reserve),'help':'USDT menos 25% P de presupuesto compras y Reserva Trading, sin límite 40%','tone':'warn'},
        {'label':'Reserva Trading','value':fmt_money(trading),'help':'Reserva separada Quantfury; incluida en USDT físico','tone':'primary'}],
      'custody_comparison':custody_comparison,
      'buys':buy_preview,'sells':sale_preview,'buy_total':buy_total,'sell_total':sale_total,
      'buy_with_sales':buy_with_sales, 'buy_total_after_sales':buy_total_after_sales,
      'buy_chart':[{'token':r['token'],'actual':r['weight']*100,'post':buy_weights[r['token']]*100,'target':r['target']*100} for r in buy_candidates],
      'sell_chart':[{'token':r['token'],'actual':r['weight']*100,'post':sell_weights[r['token']]*100,'target':r['target']*100} for r in sell_candidates],
      'buy_cash_after':cash-buy_total,'sell_cash_after':cash+sale_total,
      'limitations':'05_ORDENES no contiene órdenes activas según MASTER; el libro privado de Exchange no está verificado. Se respetan topes acumulados por Tier y BTC NEVER SELL. Escenarios independientes: ni ventas ni compras son fills.'}

@app.context_processor
def common_nav():
    return {'nav_modes':[m for m in MODE_DEFS if m['slug'] in ENABLED_MODE_SLUGS]}

@app.route('/')
def home():
    # Single canonical dashboard/portfolio view. Legacy bookmarks still work.
    return redirect(url_for('integral_portfolio_page'), code=302)

@app.route('/mode/portafolio')
def integral_portfolio_page():
    # Strategic historical ledger, deliberately independent of live crypto valuation.
    values = dict(INTEGRAL)
    base = values['historical_capital_usdt']
    segments = values['segments']
    alive = sum(x['actual_usdt'] for x in segments if x['key'] != 'lost')
    lost = next(x['actual_usdt'] for x in segments if x['key'] == 'lost')
    gain_to_recover = (base / alive - 1) * 100 if alive > 0 else None
    # Retrospective pricing chart intentionally retired by user's design approval.
    # Historical BSI is displayed for information only; no SELL signal.
    spot_breakdown = None
    spot_observed = None
    pnl_report = None
    allocation = None
    categories = None
    portfolio_rows = []
    btc_total = None
    btc_reference_price = None
    bsi_archive = None
    portfolio_diagnostic = None
    attempt_utc = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    stage = 'BINANCE_SPOT_MCP'
    try:
        observed, live = load_live_dashboard()
        stage = 'PORTFOLIO_VALUATION'
        # All-or-nothing rendering: no totals/graphs from a partially constructed valuation.
        candidate_rows = live['rows']
        candidate_pnl = summarize_unrealized(candidate_rows)
        candidate_allocation = portfolio_allocation(candidate_rows,live['usdt_total'])
        candidate_categories = category_allocation(candidate_rows)
        core_value = sum((r['hodl_units']+r['core_units'])*r['price'] for r in candidate_rows)
        exchange_value = sum(r['exchange_units']*r['price'] for r in candidate_rows)
        cash_total = live['usdt_total']
        qf = live['trading_reserve']
        candidate_spot = {'core':core_value,'exchange':exchange_value,
                          'liquidity':cash_total-qf,'trading':qf,
                          'total':live['total_value'],'source':'Binance MCP + Google Sheets PUBLICADO'}
        spot_breakdown,spot_observed,pnl_report = candidate_spot,observed,candidate_pnl
        allocation,categories,portfolio_rows=candidate_allocation,candidate_categories,candidate_rows
        btc_reference_price,btc_total=live['btc_usdt_spot'],live['total_btc_equivalent']
        bsi_archive=live['bsi_historical']
    except Exception as exc:
        origin='BINANCE_SPOT_MCP' if stage=='BINANCE_SPOT_MCP' else 'PORTFOLIO_CALCULATION'
        info=diagnostic_error(exc,'portfolio') if stage=='BINANCE_SPOT_MCP' else None
        error_id=info['error_id'] if info else uuid.uuid4().hex[:10]
        category=info['code'] if info else 'CALCULATION_ERROR'
        app.logger.error('Portfolio unavailable id=%s origin=%s category=%s class=%s snapshot=%s',
                         error_id,origin,category,type(exc).__name__,g.kairos_state['control']['snapshot_id'])
        portfolio_diagnostic={'status':'DATA_ERROR','origin':origin,'category':category,
                              'error_id':error_id,'checked_utc':attempt_utc,
                              'snapshot_id':g.kairos_state['control']['snapshot_id'],
                              'fecha_corte':g.kairos_state['control']['fecha_corte'],
                              'last_valid_spot_utc':market_cache_status()['last_valid_observed_at'],
                              'message':'Valoración actual no disponible. No se muestran cifras Spot parciales ni se reutiliza una cotización anterior.'}
    return render_template('portfolio_integral.html', master=APP_VERSION, segments=segments,
                           base=base, alive=alive, lost=lost, gain_to_recover=gain_to_recover,
                           spot=spot_breakdown, spot_observed=spot_observed, pnl_report=pnl_report,
                           allocation=allocation, categories=categories, portfolio_rows=portfolio_rows,
                           btc_total=btc_total, btc_reference_price=btc_reference_price,
                           bsi_archive=bsi_archive, portfolio_diagnostic=portfolio_diagnostic,
                           homologation=g.kairos_state.get('homologation'),
                           historical_reference_date=values.get('reference_date_label'),
                           source_note=values['source_note'], total_recorded=sum(x['actual_usdt'] for x in segments),
                           total_target=sum(x['target_usdt'] for x in segments))

@app.route('/mode/ordenes')
def orders_inbox_page():
    """Separate market/snapshot gate from independent balance and weekly sources.

    Weekly pivots are required for structural proposals, never for ordinary
    Balancer recommendations. Missing structural quotes must not erase valid
    balance proposals. All outputs remain phase-1, non-executable.
    """
    mode=MODES_BY_SLUG['ordenes']
    stage='MASTER y Spot MCP'
    try:
        observed,d=load_live_dashboard()  # MUST remain fail-closed.
        stage='Balance de portafolio'
        bal=balancer_report(d,observed)
        stage='Estructura semanal MCP'
        structural_note=None
        try:
            buy=build_mode_payload('compras',d,observed)
            blocked=sorted(t for t,c in buy.get('weekly_context',{}).items()
                           if c.get('status') in ('MCP_DATA_ERROR','DATA_ERROR'))
            if blocked:
                structural_note='Estructura incompleta para '+', '.join(blocked)+'. N/D para niveles sin velas 1W suficientes.'
        except Exception as exc:
            app.logger.exception('Orders structure unavailable; balance can still be shown')
            structural_note='Estructura MCP no certificable; niveles Fibonacci N/D. Balance independiente permanece en modo propuesta.'
            tokens=[{'token':r['token'],'price':r['price'],'current_usdt':r['value'],
                     'units':r['units'],'target':r['target']} for r in d['rows']]
            buy={'tokens':tokens,'o2_levels':{},'buy_eligibility':{},
                 'buy_stage_weights':{},'forecast_o2_allocation':[25.,25.,25.,25.],
                 'drift_band_pp':approved_numeric('DRIFT_BAND_PP'),'weekly_context':{}}
        stage='Ensamblaje de propuestas'
        from orders_inbox import build_order_inbox
        from wave_macro_context import published_wave_levels
        wave_levels=published_wave_levels(g.kairos_state['wave_pivots'])
        inbox=build_order_inbox(d,buy,bal,wave_levels=wave_levels)
        return render_template('ordenes.html',mode=mode,inbox=inbox,observed=observed,
                               snapshot=g.kairos_state['control']['snapshot_id'],master=APP_VERSION,error=None,
                               structural_note=structural_note,
                               tier_by_token={row['token']:row['tier'] for row in d['rows']})
    except Exception as exc:
        incident=uuid.uuid4().hex[:10]
        app.logger.exception('Orders inbox DATA_ERROR id=%s stage=%s',incident,stage)
        # Do not leak raw MCP credentials, response bodies or sensitive traces.
        return render_template('ordenes.html',mode=mode,inbox=None,observed=None,
                               snapshot=None,master=APP_VERSION,error='No se pudo verificar '+stage+'. Ninguna propuesta nueva mostrada.',
                               structural_note=None,error_id=incident,error_stage=stage),503

@app.route('/mode/<slug>')
def mode_page(slug):
    if slug == 'resumen':
        return redirect('/')
    mode = MODES_BY_SLUG.get(slug)
    if not mode or slug not in ENABLED_MODE_SLUGS:
        abort(404)
    try:
        observed, dashboard = load_live_dashboard()
    except Exception as exc:
        diag = diagnostic_error(exc, f'mode:{slug}:market')
        return render_template('mode.html', mode=mode, payload=None, error=diag['message'], diagnostic=diag, master=APP_VERSION), 503
    try:
        payload = build_mode_payload(slug, dashboard, observed)
        if slug == 'ventas':
            override=request.args.get('usdt_pct')
            if override is not None:
                try:
                    override=float(override)
                    if not math.isfinite(override) or not 0<=override<=100:
                        raise ValueError('porcentaje fuera de rango')
                except (ValueError, TypeError):
                    abort(400, description='Objetivo de USDT inválido: usar 0–100%')
                payload['current']['requested_percent']=override
        # All four simulation modes receive the same read-only wave reference.
        # A slider can modify a scenario, never the Master-confirmed wave price.
        payload['wave_pivots']=g.kairos_state['wave_pivots']
        from wave_macro_context import published_wave_levels
        payload['wave_levels']=published_wave_levels(payload['wave_pivots'])
        payload['confirmed_pivot_count']=sum(1 for rec in payload['wave_pivots'].values()
               for wave in rec['waves'].values() if wave['status']=='CONFIRMADO')
        return render_template('balancer.html' if slug=='balancer' else 'trade_sim.html' if slug in ('compras','ventas') else 'forecast.html' if slug=='forecast' else 'tradingbot.html' if slug=='tradingbot' else 'mode.html', mode=mode, payload=payload, error=None, diagnostic=None, master=APP_VERSION)
    except HTTPException:
        raise
    except Exception as exc:
        error_id = uuid.uuid4().hex[:10]
        app.logger.exception('Kairos MODE_RENDER slug=%s ID=%s',slug,error_id)
        diag = {'code':'MODE_RENDER','error_id':error_id, 'message':'Error interno al generar el reporte del modo (no es un error MCP).'}
        return render_template('mode.html', mode=mode, payload=None, error=diag['message'], diagnostic=diag, master=APP_VERSION), 500


# Unified bell inbox sourced exclusively from KairosGPT Google Sheets 1H/4H/1D ledger.
# Read receipts are stored separately in 17_ALERTAS_LECTURAS; no SQLite/local fallback.
@app.route('/api/alerts/unread')
def alerts_unread():
    try:
        return jsonify(unread_alerts(timeframe=request.args.get('timeframe')))
    except SettingsError as exc:
        return jsonify({'status':'INVALID','reason':str(exc)}),400
    except Exception as exc:
        app.logger.error('Alertas error id=%s class=%s',uuid.uuid4().hex[:10],type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','origin':'GOOGLE_SHEETS_ALERTAS',
                        'message':'No se pudo leer el histórico de Alertas 1H/4H/1D. No se muestran notificaciones de otra fuente.'}),503


def _same_origin(*, csrf_protected_login=False):
    # Reject explicit foreign origins.  Browser Fetch Metadata provides a safe
    # fallback when Render/proxy/referrer policy hides Referer/Origin; only a
    # CSRF-protected login form can fall back when metadata is completely absent.
    return same_origin_allowed(
        request_host=request.host,
        origin=request.headers.get('Origin', ''),
        referer=request.headers.get('Referer', ''),
        fetch_site=request.headers.get('Sec-Fetch-Site', ''),
        render_host=os.getenv('RENDER_EXTERNAL_HOSTNAME', ''),
        public_origin=os.getenv('KAIROS_PUBLIC_ORIGIN', ''),
        csrf_protected_login=csrf_protected_login,
    )


@app.route('/api/alerts/read-all', methods=['POST'])
def alerts_mark_all_read():
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    body=request.get_json(silent=True) or {}
    try:return jsonify(mark_all_alerts_read(timeframe=body.get('timeframe')))
    except SettingsError as exc:return jsonify({'status':'INVALID','reason':str(exc)}),400
    except Exception as exc:
        app.logger.error('Mark all alerts read class=%s',type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','message':'No se pudieron guardar los acuses en Google Sheets.'}),503


@app.route('/api/alerts/read',methods=['POST'])
def alerts_mark_read():
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    body=request.get_json(silent=True) or {}
    try:
        result=mark_alert_read(body.get('id'))
        return jsonify(result)
    except SettingsError as exc:
        return jsonify({'status':'INVALID','reason':str(exc)}),409
    except Exception as exc:
        app.logger.error('Mark alert read class=%s',type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','message':'No se pudo persistir la lectura en Google Sheets.'}),503


_SETTINGS_TABS = frozenset(('units', 'targets', 'tier_custody', 'liquidity', 'capital_targets',
                           'pivots', 'parameters', 'mcp'))


def _settings_destination(tab):
    # Preserve only one recognized Configuration tab; no arbitrary redirect URL.
    return url_for('settings_page', **({'tab': tab} if tab in _SETTINGS_TABS else {}))


@app.route('/settings')
def settings_page():
    # One administrator login gates the entire Configuration module (all tabs).
    if not _admin_authorized():
        tab = request.args.get('tab', '')
        return redirect(url_for('admin_login', **({'tab': tab} if tab in _SETTINGS_TABS else {})))
    return render_template('settings.html',master=APP_VERSION)



@app.route('/api/settings/data')
def get_settings_data():
    if not _admin_authorized():
        return jsonify({'status':'ADMIN_AUTH_REQUIRED',
                        'reason':'Accede a Configuración con la sesión administrativa.'}),403
    try:
        data=settings_data()
        data['is_admin']=_admin_authorized()
        data['csrf_token']=session.get('csrf_token') if _admin_authorized() else None
        return jsonify(data)
    except Exception as exc:
        app.logger.error('Settings data class=%s',type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','message':'No se pudo cargar Configuración desde Google Sheets.'}),503


def _admin_authorized():
    # Signed, HttpOnly, Secure 30-minute session; never use Basic as write permission.
    return bool(app.secret_key and os.getenv('KAIROS_SETTINGS_ADMIN_KEY') and session.get('kairos_admin'))


def _csrf_ok():
    saved=session.get('csrf_token')
    given=request.headers.get('X-Kairos-Csrf','')
    return bool(saved and given and secrets.compare_digest(saved,given))


@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    # Keep the selected Configuration section across the one-time login.
    selected_tab = request.args.get('tab', '')
    if selected_tab not in _SETTINGS_TABS:
        selected_tab = ''
    if request.method == 'GET' and _admin_authorized():
        return redirect(_settings_destination(selected_tab))
    if not app.secret_key or not os.getenv('KAIROS_SETTINGS_ADMIN_KEY'):
        return render_template('admin_login.html',not_configured=True,error='Falta KAIROS_SESSION_SECRET o KAIROS_SETTINGS_ADMIN_KEY en Render.'),503
    if request.method == 'POST':
        supplied_token=request.form.get('login_csrf','')
        saved_token=session.get('login_csrf','')
        token_ok=bool(saved_token and supplied_token and
                      secrets.compare_digest(saved_token,supplied_token))
        # Rejected submissions must never grant an administrative session.
        if not token_ok:
            return render_template('admin_login.html',error='Sesión de acceso caducada o no disponible. Recarga esta página e inténtalo nuevamente.',
                                   not_configured=False,login_csrf=session.get('login_csrf', ''),settings_tab=selected_tab),403
        if not _same_origin(csrf_protected_login=True):
            app.logger.warning('Admin login rejected: untrusted origin metadata (no URLs/credentials logged)')
            return render_template('admin_login.html',error='Origen no autorizado. Abre el acceso desde la misma web.',
                                   not_configured=False,login_csrf=session.get('login_csrf',''),settings_tab=selected_tab),403
        # One-use login CSRF: rotate even after a wrong password.
        session.pop('login_csrf',None)
        supplied=request.form.get('admin_key','')
        expected=os.getenv('KAIROS_SETTINGS_ADMIN_KEY','')
        if supplied and secrets.compare_digest(supplied,expected):
            session.clear();session.permanent=True
            session['kairos_admin']=True
            session['csrf_token']=secrets.token_urlsafe(32)
            return redirect(_settings_destination(selected_tab))
        new_csrf=secrets.token_urlsafe(32)
        session['login_csrf']=new_csrf
        return render_template('admin_login.html',error='Clave administrativa incorrecta.',
                               not_configured=False,login_csrf=new_csrf,settings_tab=selected_tab),403
    login_csrf=secrets.token_urlsafe(32)
    session['login_csrf']=login_csrf
    return render_template('admin_login.html',error=None,not_configured=False,login_csrf=login_csrf,settings_tab=selected_tab)


@app.route('/admin/logout',methods=['POST'])
def admin_logout():
    if not _same_origin() or not _csrf_ok():return jsonify({'status':'FORBIDDEN'}),403
    session.clear();return jsonify({'status':'OK'})


@app.route('/api/settings/save',methods=['POST'])
def settings_save():
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    if not _admin_authorized() or not _csrf_ok():return jsonify({'status':'ADMIN_AUTH_REQUIRED','reason':'Inicia sesión administrativa para guardar cambios.'}),403
    if not os.getenv('KAIROS_GOOGLE_WRITER_JSON'):return jsonify({'status':'WRITE_DISABLED','reason':'Sin identidad Google editora en Render.'}),503
    body=request.get_json(silent=True) or {}
    # A manual CONFIRMADO pivot must be previewed and explicitly published.
    # Legacy direct-save remains available only for candidates and other settings.
    if body.get('section')=='pivots' and any(
        entry.get(w+'_status') in ('VALIDADO','VALIDADO_TECNICAMENTE','CONFIRMADO')
        for entry in (body.get('entries') if isinstance(body.get('entries'),list) else [])
        if isinstance(entry,dict) for w in ('o1','o2','o3','o4','o5','cl')):
        return jsonify({'status':'PREVIEW_REQUIRED','reason':'Usa Validar y Publicar para confirmar pivotes por onda.'}),409
    try:
        # Shared transaction includes complete validation, audit log, new revision and fresh read.
        return jsonify(save_changes(body))
    except HomologationWorkflowError as exc:
        return jsonify({'status':'DATA_ERROR','error_code':exc.code,'phase':exc.phase,'reason':str(exc),
                        'write_may_have_committed':exc.write_may_have_committed}),503
    except SettingsError as exc:return jsonify({'status':'INVALID','reason':str(exc)}),409
    except Exception as exc:
        app.logger.error('Settings save error id=%s type=%s',uuid.uuid4().hex[:10],type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':'No se pudo verificar la publicación; revisar Google Sheets antes de reintentar.'}),503


def _preview_signature(body, issued_at):
    canonical={k:body.get(k) for k in ('expected_snapshot_id','section','entries','evidence','as_of_date')}
    payload=f'{issued_at}:'.encode('utf-8')+json.dumps(canonical,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hmac.new(os.getenv('KAIROS_SETTINGS_ADMIN_KEY','').encode('utf-8'),payload,hashlib.sha256).hexdigest()


def _verify_preview_token(body):
    token=body.get('preview_token','')
    if not isinstance(token,str) or len(token)>130 or '.' not in token:return False
    epoch,digest=token.split('.',1)
    if not epoch.isdigit() or len(digest)!=64:return False
    now=int(time.time());at=int(epoch)
    return 0<=now-at<=900 and secrets.compare_digest(digest,_preview_signature(body,at))


@app.route('/api/settings/preview',methods=['POST'])
def settings_preview():
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    if not _admin_authorized() or not _csrf_ok():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    body=request.get_json(silent=True) or {}
    try:
        raw=_unused_remote_marker()
        current=get_state(force=True)
        if current['control']['snapshot_id']!=body.get('expected_snapshot_id'):
            raise SettingsError('CONFLICTO: actualiza página y recarga snapshot')
        patches,validated=prepare_changes(raw,body.get('section'),body.get('entries'),
             evidence=body.get('evidence'),as_of_date=body.get('as_of_date'))
        issued=int(time.time())
        return jsonify({'status':'VALIDATED_DRAFT','preview_token':f'{issued}.{_preview_signature(body,issued)}','expected_snapshot_id':current['control']['snapshot_id'],
                        'changed_fields':len(patches),'section':body.get('section'),
                        'warning':'Todavía NO se ha modificado Google Sheets. Publicar es una acción distinta.'})
    except SettingsError as exc:return jsonify({'status':'INVALID','reason':str(exc)}),400
    except Exception as exc:
        app.logger.error('Settings preview error class=%s',type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':'Error de validación Google Sheets'}),503


@app.route('/api/settings/publish',methods=['POST'])
def settings_publish():
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    if not _admin_authorized() or not _csrf_ok():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    body=request.get_json(silent=True) or {}
    if body.get('confirm')!='PUBLICAR':return jsonify({'status':'CONFIRMATION_REQUIRED'}),400
    if not _verify_preview_token(body):return jsonify({'status':'PREVIEW_REQUIRED','reason':'Validación previa ausente, caducada o distinta del contenido a publicar'}),409
    try:return jsonify(save_changes(body))
    except HomologationWorkflowError as exc:
        return jsonify({'status':'DATA_ERROR','error_code':exc.code,'phase':exc.phase,'reason':str(exc),
                        'write_may_have_committed':exc.write_may_have_committed}),503
    except SettingsError as exc:return jsonify({'status':'INVALID','reason':str(exc)}),409
    except Exception as exc:
        app.logger.error('Settings publish error id=%s class=%s',uuid.uuid4().hex[:10],type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':'No se pudo publicar nueva versión del Master.'}),503


@app.route('/api/settings/homologation-status',methods=['GET'])
def settings_homologation_status():
    if not _admin_authorized():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    try:return jsonify(homologation_readiness())
    except HomologationWorkflowError as exc:
        return jsonify({'status':'DATA_ERROR','error_code':exc.code,'phase':exc.phase,'reason':str(exc)}),503
    except Exception as exc:
        incident=uuid.uuid4().hex[:10]
        app.logger.error('Homologation readiness id=%s class=%s',incident,type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','error_code':'HOM_UNKNOWN_READ_FAILURE',
                        'phase':'READ','error_id':incident,'reason':'No fue posible consultar el estado de la homologación.'}),503


@app.route('/api/settings/homologate',methods=['POST'])
def settings_homologate():
    """Explicit administrator action to reconcile the current publication; no balance writes."""
    if not _same_origin():return jsonify({'status':'FORBIDDEN_ORIGIN'}),403
    if not _admin_authorized() or not _csrf_ok():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    if not os.getenv('KAIROS_GOOGLE_WRITER_JSON'):
        return jsonify({'status':'WRITE_DISABLED','error_code':'HOM_WRITER_MISSING',
                        'phase':'PREFLIGHT','reason':'Falta KAIROS_GOOGLE_WRITER_JSON en Render.'}),503
    body=request.get_json(silent=True) or {}
    if body.get('confirm')!='HOMOLOGAR':return jsonify({'status':'CONFIRMATION_REQUIRED'}),400
    try:return jsonify(homologate_current_snapshot(body.get('expected_snapshot_id')))
    except HomologationWorkflowError as exc:
        return jsonify({'status':'DATA_ERROR','error_code':exc.code,'phase':exc.phase,
                        'reason':str(exc),'write_may_have_committed':exc.write_may_have_committed}),503
    except SettingsError as exc:return jsonify({'status':'INVALID','error_code':'HOM_INVALID_INPUT',
                                                'phase':'VALIDATION','reason':str(exc)}),409
    except Exception as exc:
        incident=uuid.uuid4().hex[:10]
        app.logger.error('Master homologation id=%s class=%s',incident,type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','error_code':'HOM_UNEXPECTED_ERROR',
                        'phase':'UNKNOWN','reason':'Homologación no verificada. Revisar logs privados y MASTER antes de reintentar.',
                        'error_id':incident}),503


@app.route('/api/settings/pivots/cl-review')
def cl_technical_review_endpoint():
    """Independent evidence gate: 1W 5L/5R + BOS; NEVER confirms a CL.

    Issued proof authorizes just a short-lived technical-status update via
    Settings preview/publish. Only the user can later publish CONFIRMADO.
    """
    if not _admin_authorized():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    from pivot_preload import TOKENS
    from wave_structure import full_utc_weeks
    from cl_validation import review_cl, sign_review
    from wave_pivots import date_iso
    token=request.args.get('token','').upper().strip()
    if token not in TOKENS:return jsonify({'status':'INVALID_TOKEN'}),400
    try:
        low=float(request.args.get('cl_price',''))
        when=date_iso(request.args.get('cl_date'))
        if not when or not math.isfinite(low) or low<=0:return jsonify({'status':'INVALID_ANCHOR'}),400
    except (ValueError,TypeError):return jsonify({'status':'INVALID_ANCHOR'}),400
    try:
        if token=='HYPE':
            market=call_mcp_resilient('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                                      {'interval':'1d','start_date':'2024-11-29','limit':750})
            if market.get('pair')!='HYPE/USDC':raise RuntimeError('HYPE macro pair mismatch')
        else:
            name='PUMP' if token=='PUMPFUN' else token
            from cl_review_history import fetch_closed_binance_history
            market=fetch_closed_binance_history(call_mcp_resilient,name,when)
            if market.get('symbol')!=name+'USDT':raise RuntimeError('Binance symbol mismatch')
        if market.get('status')!='OK' or not market.get('closed_only') or not market.get('records'):
            raise RuntimeError('Closed daily MCP history unavailable')
        weeks=full_utc_weeks(market['records'])
        result=review_cl(weeks,low,when,left=int(approved_numeric('WEEKLY_PIVOT_LEFT')),
                         right=int(approved_numeric('WEEKLY_PIVOT_RIGHT')))
        snapshot=g.kairos_state['control']['snapshot_id']
        result.update(token=token,cl_price=low,cl_date=when,source='HYPERLIQUID_SPOT_HYPE_USDC' if token=='HYPE' else 'BINANCE_SPOT_USDT',
                      closed_weeks=len(weeks),scope='TECHNICAL_REVIEW_ONLY',certified=False,
                      snapshot_id=snapshot)
        if result['validated']:
            result['review_proof']=sign_review(token,low,when,snapshot)
        return jsonify(result)
    except Exception as exc:
        app.logger.warning('CL technical review failed token=%s class=%s',token,type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','token':token,'reason':'No fue posible validar 1W 5L/5R+BOS con MCP cerrado; CL sigue candidato.'}),503


@app.route('/api/settings/pivots/technical-review')
def pivot_technical_review_endpoint():
    """MCP 1W evidence for ONE proposed/validated extreme; never publishes."""
    if not _admin_authorized():return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    from pivot_preload import TOKENS
    from wave_pivots import date_iso
    from wave_structure import full_utc_weeks
    from cl_validation import review_cl, review_wave, sign_review
    token=request.args.get('token','').strip().upper()
    wave=request.args.get('wave','').lower().strip()
    if token not in TOKENS or wave not in ('cl','o1','o2','o3','o4','o5'):
        return jsonify({'status':'INVALID_PIVOT'}),400
    try:
        price=float(request.args.get('price',''));when=date_iso(request.args.get('date'))
        if not when or not math.isfinite(price) or price<=0:return jsonify({'status':'INVALID_ANCHOR'}),400
    except (ValueError,TypeError):return jsonify({'status':'INVALID_ANCHOR'}),400
    try:
        if token=='HYPE':
            market=call_mcp_resilient('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                                     {'interval':'1d','start_date':'2024-11-29','limit':750})
            if market.get('pair')!='HYPE/USDC':raise ValueError('Wrong HYPE macro market')
        else:
            from cl_review_history import fetch_closed_binance_history
            name='PUMP' if token=='PUMPFUN' else token
            market=fetch_closed_binance_history(call_mcp_resilient,name,when)
            if market.get('symbol')!=name+'USDT':raise ValueError('Wrong Binance market')
        if market.get('status')!='OK' or market.get('closed_only') is not True or not market.get('records'):
            raise ValueError('Closed MCP candles unavailable')
        weeks=full_utc_weeks(market['records'])
        opts={'left':int(approved_numeric('WEEKLY_PIVOT_LEFT')),'right':int(approved_numeric('WEEKLY_PIVOT_RIGHT'))}
        result=(review_cl(weeks,price,when,**opts) if wave=='cl' else review_wave(weeks,price,when,wave,**opts))
        if result.get('validated'):
            result['status']='VALIDADO'
            result['review_proof']=sign_review(token if wave=='cl' else token+'|'+wave,price,when,g.kairos_state['control']['snapshot_id'])
        return jsonify({**result,'token':token,'wave':wave,'source':'HYPERLIQUID_SPOT_USDC' if token=='HYPE' else 'BINANCE_SPOT_USDT',
                       'scope':'TECHNICAL_REVIEW_ONLY','certified':False,'closed_weeks':len(weeks)})
    except Exception as exc:
        app.logger.warning('Pivot technical review failed token=%s wave=%s type=%s',token,wave,type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','reason':'Revisión 1W no disponible; no actualizar este pivote',
                        'token':token,'wave':wave}),503


@app.route('/api/settings/pivots/preliminary')
def pivot_preliminary_endpoint():
    """Review-only preliminary data. Default is archived MCP; refresh one token live.

    Never issue a 12-token synchronous fan-out: transient Render/MCP delays
    would make the entire UI hang. One-token refreshes can fail independently.
    """
    from pivot_preload import TOKENS, ARCHIVE_A1, archive_candidates, review_result
    token = request.args.get('token', '').strip().upper()
    if not token:
        try:
            from kairos_sheets_features import read_ranges
            rows = read_ranges({'archive':ARCHIVE_A1})['archive']
            records=archive_candidates(rows,g.kairos_state['parameters'])
            return jsonify({'status':'OK','scope':'EXPLORATORY_ONLY','certified':False,
                            'source':'GOOGLE_SHEETS_ARCHIVED_MCP_NOT_LIVE',
                            'observed_utc':None, 'records':records})
        except Exception as exc:
            app.logger.error('Pivot archive error category=%s',type(exc).__name__)
            return jsonify({'status':'DATA_ERROR','reason':'No se pudieron recuperar los pivotes históricos archivados; revisa conexión Google Sheets.'}),503

    if token not in TOKENS:
        return jsonify({'status':'INVALID_TOKEN'}),400
    try:
        from pivot_candidates import candidates_binance, candidates_hype, add_uncertified_daily_extrema
        # Lightweight O1-only route avoids the slower H4 5L/5R cycle scanner.
        # It reads the provisional archived CL date and uses fully closed 1D
        # Spot candles; it does not alter official pivots or certify Elliott.
        if request.args.get('o1_only') == '1':
            from kairos_sheets_features import read_ranges
            archive=archive_candidates(read_ranges({'archive':ARCHIVE_A1})['archive'],g.kairos_state['parameters'])
            record=next(x for x in archive if x['token']==token)
            if record.get('o1') is None and record.get('cl_date') and token!='HYPE':
                from datetime import date
                delta=(datetime.now(timezone.utc).date()-date.fromisoformat(str(record['cl_date'])[:10])).days
                count=min(999,max(35,delta+18))
                symbol='PUMP' if token=='PUMPFUN' else token
                daily=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',
                                         {'symbol':symbol+'USDT','interval':'1d','limit':count})
                record=add_uncertified_daily_extrema(record,daily)
            return jsonify({'status':'OK','scope':'EXPLORATORY_ONLY','certified':False,
                           'source':'BINANCE_SPOT_CLOSED_WEEK' if token!='HYPE' else 'HYPERLIQUID_ARCHIVED',
                           'observed_utc':datetime.now(timezone.utc).isoformat(),
                           'records':[review_result(record)]})
        if token=='HYPE':
            data=call_mcp_resilient('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                      {'interval':'1d','start_date':'2024-11-29','limit':750})
            record=candidates_hype(data,left=int(approved_numeric('WEEKLY_PIVOT_LEFT')),
                                        right=int(approved_numeric('WEEKLY_PIVOT_RIGHT')))
            if record.get('o3') is None and record.get('o3_unconfirmed_high') is not None:
                record['o3']=record['o3_unconfirmed_high']
                record['o3_date']=record.get('o3_unconfirmed_date')
                record['warning']+='; O3 máximo OBSERVADO sin 5R, NO certificado'
        else:
            symbol='PUMP' if token=='PUMPFUN' else token
            pkey={'SUI':'SUI_CL_SELECTED','PUMPFUN':'PUMP_CL_CANDIDATE'}.get(token)
            param=g.kairos_state['parameters'].get(pkey,{}) if pkey else {}
            selected=param.get('value') if param.get('status') in ('APROBADO_COMO_ANCLA_MANUAL','CANDIDATO_NO_CONFIRMADO') else None
            raw=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_cycle_phase',{'symbol':symbol+'USDT'})
            record=candidates_binance(token,raw,selected_low=selected)
            if record.get('status')!='DATA_ERROR' and record.get('o1') is None and record.get('cl_date'):
                try:
                    from datetime import date
                    count=min(999,max(35,(datetime.now(timezone.utc).date()-date.fromisoformat(record['cl_date'])).days+18))
                    daily=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',
                                            {'symbol':symbol+'USDT','interval':'1d','limit':count})
                    record=add_uncertified_daily_extrema(record,daily)
                except Exception:
                    record['warning']=(record.get('warning') or '')+'; máximo O1 no disponible por fallo OHLCV; conservar archivo MCP'
        record=review_result(record)
        return jsonify({'status':'OK','scope':'EXPLORATORY_ONLY','certified':False,
                        'observed_utc':datetime.now(timezone.utc).isoformat(),
                        'records':[record]})
    except Exception as exc:
        app.logger.warning('Pivot MCP unavailable token=%s class=%s',token,type(exc).__name__)
        return jsonify({'status':'PARTIAL','scope':'EXPLORATORY_ONLY','certified':False,
                        'records':[{'token':token,'status':'DATA_ERROR','certified':False,
                                    'warning':'MCP no disponible para este activo; conserva candidato archivado y revisa el diagnóstico.'}]}),200


# Technical candidates based only on fully closed Binance Spot 4H candles.
# Heuristic screening, never claim certified Kairos TradingBot signals.
def tradingbot_universe():
    record=PARAMETERS.get('UNIVERSE')
    if not record or record.get('module')!='TRADINGBOT' or record.get('status')!='APROBADO':
        raise SheetDataError('12_PARAMETROS_KAIROS: TradingBot UNIVERSE no aprobado')
    try:
        return tradingbot_tokens(record.get('value'),TIERS)
    except ValueError as exc:
        raise SheetDataError(str(exc)) from exc
@app.route('/api/tradingbot/candidates')
def tradingbot_candidates():
    symbol=request.args.get('token','ETH').upper()
    try:
        if symbol not in tradingbot_universe():return jsonify({'status':'INVALID_TOKEN'}),400
        # Both timeframes consist of confirmed, closed candles only. No actionable
        # recommendation without a separately reconciled QF account/instrument.
        four=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',{'symbol':symbol+'USDT','interval':'4h','limit':180})
        one=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_ohlcv',{'symbol':symbol+'USDT','interval':'1h','limit':250})
        indicators=call_mcp_resilient('BINANCE_MCP_URL','get_kairos_indicators',{'symbol':symbol+'USDT','interval':'1h','history':300})
        if any(r.get('status')!='OK' for r in (four,one,indicators)):
            return jsonify({'status':'DATA_ERROR','reason':'Datos 4H/1H no disponibles'}),503
        return jsonify({'status':'OK','source':'Binance MCP','classification':'STRUCTURAL_SCREEN_NOT_QF_CERTIFIED',
                        'four_h':four,'one_h':one,'indicators_1h':indicators,
                        'risk_policy':{'reserve_usdt':float(SNAPSHOT['trading_real_fixed_USDT']),
                            'max_margin_fraction':approved_numeric('QF_MARGIN_CAP_PER_POSITION'),
                            'max_loss_fraction':approved_numeric('QF_ACCOUNT_RISK_PER_TRADE'),
                            'aggregate_loss_fraction':approved_numeric('QF_ACCOUNT_RISK_TOTAL'),
                            'max_leverage':approved_numeric('MAX_LEVERAGE'),
                            'min_rr':approved_numeric('RISK_REWARD_MIN'),
                            'max_positions':int(approved_numeric('MAX_OPEN_POSITIONS')),
                            'power_buying_reference':policy_numeric('QF_POWER_BUYING_REFERENCE',{'REFERENCIA_USUARIO_NO_BALANCE'})},
                        'qf_instrument_verified':False,'qf_open_positions_verified':False,'tradingbot_state':'WATCH'})
    except Exception as exc:
        diag=diagnostic_error(exc,'tradingbot:ohlcv:'+symbol)
        return jsonify({'status':'DATA_ERROR','diagnostic':diag}),503

def _deployed_asset_status():
    """Report what is actually on disk, not merely the app.py version string.

    This catches partial GitHub/Render deployments where app.py is new but the
    templates or static files are from an older release. No secrets exposed.
    """
    critical = {
        'compras_template': ('templates/trade_sim.html', ('<th>% Peso</th>', 'renderO2Fibonacci', 'allocation-slider', 'data-o2-ui-version')),
        'o2_simulator': ('static/o2_sequential.js', ('classifyDrift', 'snapshots')),
        'alerts_bell': ('static/alert_bell.js', ('alert-timeframe', '/api/alerts/read', 'event-bull', 'event-bear')),
        'integral_donut': ('templates/portfolio_integral.html', ('data-capital-chart="donut"', 'integral-donut-sector')),
        'portfolio_layout_v2022': ('templates/portfolio_integral.html', ('data-layout-row="1"','data-layout-row="2"','data-layout-row="3"','data-layout-row="4"')),
        'allocation_legend_v2032': ('templates/portfolio_integral.html', ('data-token-columns="6+6"', 'data-allocation-cash="USDT"', 'data-allocation-column=', 'port-alloc-columns')),
        'balancer_sell_units_v2033': ('templates/balancer.html', ('<th>Unidades</th>', "'{:,.2f}'.format(r.units)", 'data-private="units"')),
        'health_three_tiers_v2030': ('app.py', ("@app.route('/api/health/diagnostics')", 'operational_providers', 'functional_modules')),
        'health_diagnostics_ui_v2030': ('templates/settings.html', ('id="health-deep-panel"', 'id="health-check-all"')),
        'health_diagnostics_js_v2030': ('static/mcp_settings.js', ('/api/health/diagnostics', 'health-check-output')),
        'portfolio_error_contract_v2030': ('templates/portfolio_integral.html', ('id="portfolio-diagnostic"','portfolio_diagnostic')),
        'homologation_contract_v2030': ('google_sheets_master.py', ('HOMOLOGATION_RANGE', 'assess_homologation(', 'SNAPSHOT_REFERENCE_STALE')),
        'homologation_ledger_v2031': ('kairos_sheets_features.py', ('HOMOLOGATION_TAB', '_certificate_append(', 'homologate_current_snapshot(')),
        'homologation_diagnostics_v2033': ('app.py', ('/api/settings/homologation-status', 'HOM_WRITER_MISSING', 'write_may_have_committed')),
        'capital_targets_ui_v2034': ('templates/settings.html', ('data-tab="capital_targets"', 'Objetivos de liquidez y ReservaTrading (%)')),
        'capital_targets_engine_v2034': ('kairos_sheets_features.py', ("elif category=='capital_targets'", 'CAPITAL_TARGET_SEGMENTS', 'sumar 100%')),
        'historical_provenance_v2030': ('templates/portfolio_integral.html', ('historical_reference_date', 'HISTÓRICO NO SPOT')),
        'consolidated_dashboard_v2027': ('templates/portfolio_integral.html', ('id="btc-portfolio-total"', 'data-bsi-chart="archived"', 'data-portfolio-executive="12"', 'class="port-status', 'port-coin-logo')),
        'consolidated_navigation_v2025': ('templates/base.html', ('href="/mode/{{ mode.slug }}"', 'global-nav-link')),
        'portfolio_allocation_v2022': ('portfolio_unrealized.py', ('def portfolio_allocation(', 'def category_allocation(', 'def pri_valuation_history(')),
        'portfolio_unrealized_chart': ('templates/portfolio_integral.html', ('data-portfolio-chart="unrealized"', 'integral-pnl-bar gain', 'integral-pnl-bar loss')),
        'portfolio_unrealized_calc': ('portfolio_unrealized.py', ('def summarize_unrealized(', "'missing_tokens': missing")),
        'pivots_cl_editor': ('static/settings_master.js', ('reviewUnconfirmedToken', 'waveReviewProofs', 'cl_status')),
        'cl_review_gate': ('cl_validation.py', ('def review_cl(', 'BOS', 'sign_review')),
        'weekly_fibonacci': ('wave_structure.py', ('def full_utc_weeks(', 'def fib_grid(')),
        'buy_weekly_gate': ('buy_weekly_policy.py', ('def select_buy_impulse(', 'BOS_ALCISTA_SEMANAL_PENDIENTE')),
        'buy_weekly_ui': ('templates/trade_sim.html', ('buy_eligibility', 'requireEligibility')),
        'buy_p1p2_anchors': ('templates/trade_sim.html', ('Maestro de Precios - Retrocesos Fibo', '<th>P1</th><th>P2</th>', 'pivot-anchor-dot')),
        'buy_p1p2_policy': ('buy_weekly_policy.py', ('def select_p1_p2_buy_impulse(', 'P1_ADMITIDO_P2_MAXIMO_SEMANAL_POSTERIOR')),
        'orders_page': ('templates/ordenes.html', ('Backlog de Ordenes Compra / Venta', 'Próximas órdenes por Token', 'USDT compra', 'Unidades venta', 'id="orders-level"', 'FASE 1 · SOLO PROPUESTAS')),
        'orders_partial_structural_fallback': ('app.py', ('def orders_inbox_page(', 'Estructura semanal MCP', 'build_order_inbox(d,buy,bal')),
        'orders_engine': ('orders_inbox.py', ('def build_order_inbox(', 'def structural_sell_candidates(', 'def portfolio_candidates(', "'buy_usdt':", "'sell_units':")),
        'orders_filters': ('static/orders_inbox.js', ('function visible(', 'orders-venue', 'orders-tier', 'orders-side', 'orders-token', 'orders-level')), 
        'pivot_mcp_status_protection': ('static/settings_master.js', ("current.cl_status!=='PROPUESTO'", "statusInput?.value!=='PROPUESTO'", "if(rec[field]!=='PROPUESTO')continue")),
        'virtual_flash_exclusion': ('structural_outliers.py', ('VIRTUAL_FLASH_WEEK_START', 'virtual_flash_cl')), 
        'config_admin_entry': ('app.py', ("@app.route('/settings')", "return redirect(url_for('admin_login'", "@app.route('/api/settings/data')")),
        'config_admin_login': ('templates/admin_login.html', ('login_csrf', 'settings_tab', 'Acceso administrativo')),
        'mobile_no_tooltips': ('static/tooltips.js', ("(hover: none) and (pointer: coarse)", "node.removeAttribute('title')", "node.setAttribute('title',previousTitles.get(node))")),
        'forecast_published_pivot_locks': ('static/forecast_fibo_plan.js', ("function wavePath(p,selectors)", "const approved=s=>s==='VALIDADO'||s==='CONFIRMADO'", 'fixed[wave]=price;locked.push(wave)')),
        'forecast_locked_chart': ('templates/forecast.html', ('Fibo.wavePath(p,selectors)', "'data-wave-fixed':locked?'true':'false'", '🔒 ${r.statuses[key]}')),
        'forecast_spot_overlay_v2029': ('templates/forecast.html', ("class:'fc-spot-line'", "'data-spot-reference':'binance-mcp'", 'fc.generated_at', "validSpot?[...prices,spot]:prices")),
        'buy_post_fibo_weights': ('static/o2_sequential.js', ('postWeights','postCrypto','stageBudgets','unallocated','policy.stageBudgets')),
        'buy_postweight_semaphore': ('static/o2_sequential.js', ('function postBuySemaphore(', "state:'green'", "state:'amber'", "state:'red'", "state:'none'")),
        'buy_postweight_color_ui': ('templates/trade_sim.html', ('buy-weight-green', 'buy-weight-amber', 'buy-weight-red', 'postBuySemaphore(amount,postWeight,t.target)', 'USDT &gt; 0')),
        'buy_custom_fibo_weights': ('static/purchase_weights.js', ('function rebalance(', 'function normalize(', 'function asFractions(', 'function waterfall(', 'function validateDraft(')),
        'buy_slider_percent_available': ('templates/trade_sim.html', ('Capital para compras (% de USDT disponible)', 'budgetFromAvailablePercent(target,maxBuyCash)', 'Llenado secuencial: primero C1, luego C2, C3 y C4')),
        'buy_waterfall_fixed_percentages': ('static/purchase_weights.js', ('function waterfall(budget,maximum,percentages)', 'function budgetFromAvailablePercent(percent,maximum)', 'function validateDraft(rawValues)')),
        'balancer_math_v2026': ('orders_inbox.py', ('def sell_capacity_usdt(', 'def overweight_sell_plan(', 'def allocate_infra_buys(', 'def tradingbot_tokens(')),
        'balancer_wiring_v2026': ('app.py', ('sale_preview=overweight_sell_plan(rows,band)', 'buy_preview=allocate_infra_buys(rows,current_cash_capacity,band)', 'return drift_tone(d,band)', 'def tradingbot_universe():')),
        'sales_optimizer_engine': ('static/sales_optimizer.js', ('function calculate(items,physicalCash,targetPct,bandPp,qf=0)', 'const stage1=', 'const stage2Amount=', 'TARGET_REACHED', 'CAPACITY_LIMITED')),
        'sales_optimizer_ui': ('templates/trade_sim.html', ('KairosSalesOptimizer.calculate(', 'sell-plan-status', 'sim-body', 'requested_percent')),
        'balancer_custody_engine': ('custody_balancer.py', ('def compare_custody(', "'ideal_nominal'", "'ideal_feasible'", "'transfer_count'")),
        'balancer_custody_ui': ('templates/balancer.html', ('id="custody-balancer"', 'Movimientos y distribución posterior', 'r.feasible_pct.hodl', 'payload.custody_comparison')), 
        'buy_custom_fibo_ui': ('templates/trade_sim.html', ('id="fibo-split-reset"', 'id="fibo-split-apply"', 'refreshFiboDraft', 'showFiboControls();paint();')),
        'forecast_elliott_table': ('templates/forecast.html', ('Simulación - Ondas Elliott', '<th>O5 (SH3)</th>')),
        'orders_simple_filters': ('templates/ordenes.html', ('Backlog de Ordenes Compra / Venta','id="orders-venue"','id="orders-tier"','id="orders-side"','id="orders-token"')),
        'forecast_master_pivots': ('app.py', ("'published_cl':w.get('cycle_low')", "'cl_status':w.get('cl_status','PROPUESTO')", "'waves':w.get('waves',{})")),
    }
    files = {}
    for key, (filename, markers) in critical.items():
        try:
            payload = (BASE / filename).read_bytes()
            content = payload.decode('utf-8')
            files[key] = {'present': True, 'sha256_12': hashlib.sha256(payload).hexdigest()[:12],
                          'markers_ok': all(marker in content for marker in markers)}
        except (OSError, UnicodeError):
            files[key] = {'present': False, 'sha256_12': None, 'markers_ok': False}
    return {'consistent': all(f['present'] and f['markers_ok'] for f in files.values()),
            'files': files}


# B05: health has separate tiers. /health remains a cheap liveness check for Render.
# An authenticated, explicit diagnostic request performs live provider calls.
_DEPENDENCY_LOCK=threading.Lock()
_DEPENDENCY_LAST={'checked_utc':None,'providers':{},'modules':{},'status':'NOT_CHECKED'}


def _live_provider_probe(provider):
    if provider=='sheets':
        try:
            state=get_state(force=True)
            return {'status':'OK','snapshot_id':state['control']['snapshot_id'],
                    'schema_version':state['control']['schema_version'],
                    'homologation':state.get('homologation',{}).get('status','NOT_VERIFIED')}
        except Exception as exc:
            return {'status':'DATA_ERROR','category':public_failure_code(exc)}
    spec={'binance':('BINANCE_MCP_URL','get_kairos_spot_prices'),
          'hyperliquid':('HYPERLIQUID_MCP_URL','get_hype_spot_market')}
    env,tool=spec[provider]
    if not os.getenv(env,'').strip():
        return {'status':'NOT_CONFIGURED','category':'MCP_URL_MISSING'}
    try:
        # One direct request (no cascading gateway retries); no remote order/fill access.
        data=asyncio.run(call_mcp(env,tool,{}))
        if data.get('status')!='OK':raise RuntimeError('non-OK MCP response')
        if provider=='binance':
            rows=data.get('records') or []
            symbols={str(x.get('symbol')) for x in rows if isinstance(x,dict)}
            expected={('PUMP' if t=='PUMPFUN' else t)+'USDT' for t in (
                'BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE')}
            if len(rows)!=12 or symbols!=expected:raise RuntimeError('incomplete MCP coverage')
        return {'status':'OK','source':provider,'checked_utc':datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        diag=diagnostic_error(exc,provider)
        return {'status':'DATA_ERROR','category':diag['code'],'error_id':diag['error_id']}


def _module_dependency_states(providers):
    dependencies={
        'portafolio':('sheets','binance'),
        'balancer':('sheets','binance'),
        'compras':('sheets','binance','hyperliquid'),
        'ventas':('sheets','binance'),
        'forecast':('sheets','binance','hyperliquid'),
        'ordenes':('sheets','binance','hyperliquid'),
        'tradingbot':('sheets','binance'),
        'configuracion':('sheets',),
    }
    return {name:{'status':'DEPENDENCIES_OK' if all(providers.get(d,{}).get('status')=='OK' for d in deps)
                  else 'BLOCKED_OR_PARTIAL','dependencies':list(deps),
                  'scope':'DEPENDENCY_READINESS_ONLY_NOT_END_TO_END'}
            for name,deps in dependencies.items()}


@app.route('/api/health/diagnostics')
def health_diagnostics():
    checked=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={name:pool.submit(_live_provider_probe,name) for name in ('sheets','binance','hyperliquid')}
        providers={name:future.result() for name,future in futures.items()}
    modules=_module_dependency_states(providers)
    assets=_deployed_asset_status()
    status='OK' if assets['consistent'] and all(p['status']=='OK' for p in providers.values()) else 'DEGRADED'
    with _DEPENDENCY_LOCK:
        _DEPENDENCY_LAST.update(checked_utc=checked,providers=providers,modules=modules,status=status)
    return jsonify({'status':status,'checked_utc':checked,
                    'server':{'status':'UP' if assets['consistent'] else 'DEGRADED',
                              'version':APP_VERSION,'release_assets_consistent':assets['consistent']},
                    'operational_providers':providers,'functional_modules':modules,
                    'note':'Módulos: evaluación de dependencias, NO prueba funcional extremo a extremo. Sin órdenes ni escrituras.'}), (200 if status=='OK' else 503)


@app.route('/health')
def health():
    assets = _deployed_asset_status()
    with _DEPENDENCY_LOCK:
        last=dict(_DEPENDENCY_LAST)
    response = {'status': 'UP' if assets['consistent'] else 'DEGRADED',
                'service': 'KairosWeb', 'version': APP_VERSION,
                'server':{'status':'UP' if assets['consistent'] else 'DEGRADED'},
                'operational_providers':{k:v.get('status','NOT_CHECKED') for k,v in last['providers'].items()},
                'functional_modules':{k:v.get('status','NOT_CHECKED') for k,v in last['modules'].items()},
                'last_deep_check_utc':last['checked_utc'],
                'deep_check_status':last['status'], 'release_assets': assets,
                'sheets_status': sheet_cache_status()}
    return jsonify(response), (200 if assets['consistent'] else 503)

@app.route('/api/portfolio')
def portfolio():
    try:
        observed, dashboard = load_live_dashboard()
        return jsonify({'status':'OK', 'source':'Binance Spot MCP + Google Sheets PUBLICADO',
                    'snapshot_id':g.kairos_state['control']['snapshot_id'],
                    'config_source':'12_PARAMETROS_KAIROS', 'observed_at':observed, **dashboard})
    except Exception as exc:
        diag = diagnostic_error(exc, 'portfolio')
        return jsonify({'status':'DATA_ERROR','reason':diag['message'],'diagnostic':diag,**market_cache_status()}), 503

@app.route('/api/market-status')
def market_status_endpoint():
    return jsonify(market_cache_status())

@app.route('/api/mcp-status')
def mcp_status():
    return jsonify({'binance_configured':bool(os.getenv('BINANCE_MCP_URL')),
                    'hyperliquid_configured':bool(os.getenv('HYPERLIQUID_MCP_URL')),
                    'hyperliquid_usage':'Macro HYPE only; no Binance/HYPE price fallback',
                    'google_sheets_configured':bool(os.getenv('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))})

@app.route('/api/mcp-config-check')
def mcp_config_check():
    checks={}
    for name, env in [('binance','BINANCE_MCP_URL'),('hyperliquid','HYPERLIQUID_MCP_URL')]:
        endpoint=os.getenv(env,'').strip()
        parsed=urlsplit(endpoint) if endpoint else None
        checks[name]={
            'configured':bool(endpoint),
            'https':bool(parsed and parsed.scheme=='https'),
            'host_present':bool(parsed and parsed.hostname),
            'path_is_mcp':bool(parsed and parsed.path.rstrip('/')=='/mcp'),
            'contains_quotes':('\"' in endpoint or "'" in endpoint),
            'contains_whitespace':any(c.isspace() for c in endpoint),
        }
    return jsonify({'status':'OK','checks':checks,'note':'El diagnóstico no revela URLs, contraseñas ni tokens.'})

_MCP_LAST_OK = {}
_MCP_LAST_LOCK = threading.Lock()


def _check_provider(provider):
    checks={
        'binance':('BINANCE_MCP_URL','get_kairos_spot_prices',{}),
        'hyperliquid':('HYPERLIQUID_MCP_URL','get_hype_spot_market',{}),
    }
    if provider not in checks:
        raise ValueError('Proveedor no reconocido')
    env,tool,args=checks[provider]
    if not os.getenv(env):return {'status':'NOT_CONFIGURED','category':'NOT_CONFIGURED','last_success_utc':None}
    try:
        response=call_mcp_resilient(env,tool,args)
        if response.get('status')!='OK':raise RuntimeError('MCP status not OK')
        if provider=='binance' and len(response.get('records') or [])!=12:
            raise RuntimeError('MCP incomplete Binance token coverage')
        now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        with _MCP_LAST_LOCK:_MCP_LAST_OK[provider]=now
        return {'status':'OK','source':response.get('source'),
                'records':len(response.get('records') or []) if provider=='binance' else None,
                'checked_utc':now,'last_success_utc':now}
    except Exception as exc:
        diag=diagnostic_error(exc,provider)
        with _MCP_LAST_LOCK:previous=_MCP_LAST_OK.get(provider)
        return {'status':'DATA_ERROR','diagnostic':diag,'last_success_utc':previous,
                'checked_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z')}


@app.route('/api/mcp-diagnostics')
def mcp_diagnostics():
    provider=request.args.get('provider','').strip().lower()
    if provider and provider not in ('binance','hyperliquid'):
        return jsonify({'status':'INVALID_PROVIDER'}),400
    names=[provider] if provider else ['binance','hyperliquid']
    results={name:_check_provider(name) for name in names}
    return jsonify({'status':'OK' if all(x['status']=='OK' for x in results.values()) else 'CHECK_REQUIRED',
                    'providers':results,'refresh':'Consulta read-only; /health NO reinicia Render.'})


@app.route('/api/admin/session')
def admin_session_state():
    # Does not disclose the secret or grant authentication. Allows MCP diagnosis
    # even when 01_CONTROL cannot be read from Google Sheets.
    return jsonify({'status':'OK','is_admin':bool(_admin_authorized()),
                    'csrf_token':session.get('csrf_token') if _admin_authorized() else None})


@app.route('/api/mcp-refresh',methods=['POST'])
def mcp_refresh():
    # A refresh never restarts Render services, changes credentials or writes Sheets.
    if not _same_origin() or not _admin_authorized() or not _csrf_ok():
        return jsonify({'status':'ADMIN_AUTH_REQUIRED'}),403
    payload=request.get_json(silent=True) or {}
    provider=payload.get('provider')
    if provider not in ('binance','hyperliquid'):
        return jsonify({'status':'INVALID_PROVIDER'}),400
    if provider=='binance':
        with _MARKET_LOCK:
            _MARKET_CACHE.update(stored=0.0,observed=None,prices=None)
    check=_check_provider(provider)
    return jsonify({'status':check['status'],'provider':provider,'result':check,
                    'note':'Caché local invalidada cuando aplica; se abrió nueva consulta MCP. Sin reinicio de Render.'}), (200 if check['status']=='OK' else 503)


@app.route('/api/hype-macro')
def hype_macro():
    try:
        # Macro from closed native Spot HYPE/USDC days, aggregated ourselves to
        # Monday-Sunday UTC full weeks; 1w provider candles may have another anchor.
        data=call_mcp_resilient('HYPERLIQUID_MCP_URL','get_hype_spot_ohlcv',
                                  {'interval':'1d','start_date':'2024-11-29','limit':1200})
        weekly=aggregate_weeks(data)
        return jsonify({'status':'OK','market':'HYPE/USDC Spot macro', 'data':weekly})
    except Exception as exc:
        app.logger.error('HYPE macro error type=%s', type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','origin':'HYPERLIQUID_MCP',
                        'reason':'HYPE Spot 1D o semanas UTC completas no disponibles.'}),503

@app.route('/api/sheets-status')
def google_sheets_status():
    # Does not reveal secrets, share names, or sheet values. Live read requested.
    try:
        state=get_state()
        return jsonify({'status':'OK','source':'GOOGLE_SHEETS',
                        'snapshot_id':state['control']['snapshot_id'],
                        'published_utc':state['control']['publicado_utc'],
                        'fecha_corte':state['control']['fecha_corte'],
                        'schema_version':state['control']['schema_version'],
                        'tokens':len(state['tokens']), 'parameter_count':len(state['parameters']),
                        'o5_proceeds_split':{'BTC':state['parameters']['O5_BTC_PROCEEDS_FRACTION']['value'],
                                              'USDT':state['parameters']['O5_USDT_PROCEEDS_FRACTION']['value']},
                        'bsi_sell':'BLOQUEADO', 'tradingbot':'WATCH',
                        'homologation':state.get('homologation',{}),
                        'cache':sheet_cache_status()})
    except Exception as exc:
        app.logger.error('Sheets status failure category=%s type=%s',public_failure_code(exc),type(exc).__name__)
        return jsonify({'status':'DATA_ERROR','origin':'GOOGLE_SHEETS',
                        'reason':'Error de conexión, credenciales, publicación o integridad de Google Sheets.',
                        'category':public_failure_code(exc)}),503

@app.route('/api/modes')
def modes_api():
    return jsonify({'status':'OK','execution':'PRELIMINARY_PAGES', 'read_only':True,
                    'modes':[dict(m, availability='PRELIMINARY_PAGE') for m in MODE_DEFS if m['slug'] in ENABLED_MODE_SLUGS]})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
