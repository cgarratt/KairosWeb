"""Kairos Web v1: read-only dashboard backed exclusively by approved MCPs."""
import asyncio
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, Response, jsonify, render_template, request
from fastmcp import Client

BASE = Path(__file__).parent
app = Flask(__name__)
SNAPSHOT = json.loads((BASE / 'data/snapshot_master_2026-10-15.json').read_text())
CONFIG = json.loads((BASE / 'data/config.json').read_text())
TOKENS = [r['symbol'] for r in CONFIG['universe']]
TARGETS = {r['symbol']: r['target'] for r in CONFIG['universe']}
TIERS = {r['symbol']: r['tier'] for r in CONFIG['universe']}
MODES = [
    ('Balancer', 'Rebalanceo y liquidez', 'Propuestas; piso de liquidez y Core protegido'),
    ('Compras', 'O2 / O4', 'Planificar límites C1 50% y C2 61.8%'),
    ('Ventas', 'Objetivo USDT', 'Solo SELL; BTC nunca se vende'),
    ('TradingBot', 'Táctico 4H', 'Oportunidades LONG / SHORT y reserva separada'),
    ('Alertas', 'Vigilancia 1H · 4H · 1D', 'Señales según las políticas Kairos'),
    ('Resumen', 'Auditoría del portafolio', 'Posiciones, liquidez y custodia'),
    ('Forecast', 'Escenarios O2 → O5', 'Simulación de capital y acumulación de BTC'),
    ('Benchmark', 'Comparación estructural', 'Escenarios comparativos'),
    ('Rotation', 'Rotación de activos', 'Simulaciones sin cambios de targets'),
    ('MonteCarlo', 'Simulación probabilística', 'Riesgos, percentiles e hipótesis'),
]

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
    # Protected MCP endpoint may be configured with a bearer token.
    token = os.getenv(env_name.replace('_URL', '_TOKEN'), '').strip()
    from fastmcp.client.transports import StreamableHttpTransport
    transport = StreamableHttpTransport(endpoint, headers={'Authorization': f'Bearer {token}'} if token else None)
    async with Client(transport, timeout=25) as client:
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
    # Avoid including URLs, tokens, traceback or confidential details in client payloads.
    if isinstance(exc, RuntimeError) and ('no configurada' in str(exc) or 'debe usar HTTPS' in str(exc)):
        return str(exc)
    return 'MCP sin respuesta válida. Revisar conectividad y logs de Render.'

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
    # The operational pool is distinct from the Quantfury trading reserve.
    return {'rows': rows, 'crypto_value': portfolio_crypto, 'usdt_total':liquidity,
            'usdt_operating':SNAPSHOT['kairos_operating_USDT_before_commitments'],
            'trading_reserve':trading, 'total_value':portfolio_crypto+liquidity,
            'usdt_pct':liquidity/(portfolio_crypto+liquidity) if portfolio_crypto+liquidity else 0,
            'snapshot_date':SNAPSHOT['units_snapshot_as_of'],
            'note':'Unidades y USDT del snapshot Master 15/10/2026. No se leen balances privados de exchanges.'}

@app.route('/')
def home():
    return render_template('index.html', modes=MODES, master='5.3.5')

@app.route('/health')
def health():
    return jsonify({'status':'UP','service':'Kairos Web','version':'1.0','snapshot_date':SNAPSHOT['units_snapshot_as_of']})

@app.route('/api/portfolio')
def portfolio():
    try:
        data = asyncio.run(call_mcp('BINANCE_MCP_URL', 'get_kairos_spot_prices'))
        if data.get('status') != 'OK':
            raise RuntimeError('Binance MCP DATA_ERROR')
        records = data.get('records')
        if not isinstance(records,list):
            raise RuntimeError('Invalid records')
        prices = {}
        for record in records:
            s = record['symbol']
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
def modes():
    return jsonify({'status':'OK','execution':'NOT_CONNECTED', 'read_only':True,
                    'modes':[{'name':a,'subtitle':b,'description':c,'availability':'MENU_ONLY'} for a,b,c in MODES]})

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
