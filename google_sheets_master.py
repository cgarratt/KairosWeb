"""KairosWeb v1.0.0: strictly read-only Google Sheets client and contract validator.

No local snapshot/config JSON fallback.  Uses credentials only from Render secrets.
Snapshot publication and per-field parameter status are independent gates.
"""
import json
import math
import os
import threading
import time
from datetime import datetime, timezone
from urllib.parse import quote

SHEET_ID_DEFAULT = '1_tG5FK_u0biVZm2iXaK6fJi1enBYJYLAG6txkpTgsy8'
SHEETS = {
    'control': "'01_CONTROL'!A4:C31",
    'positions': "'02_POSICIONES'!A4:N17",
    'liquidity': "'03_LIQUIDEZ'!A4:F17",
    'custody': "'04_CUSTODIA'!A4:G7",
    'orders': "'05_ORDENES'!A4:P250",
    'fills': "'06_FILLS'!A4:P250",
    'pivots': "'07_PIVOTES'!A4:Q16",
    'integral': "'08_INTEGRAL'!A4:F15",
    'bsi': "'09_BSI'!A4:S16",
    'validation': "'11_VALIDACIONES'!A4:D25",
    'parameters': "'12_PARAMETROS_KAIROS'!A4:J180",
}
SYMBOLS = frozenset(('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE'))
REQUIRED_PARAMS = ('SNAPSHOT_PROVIDER','BTC_NEVER_SELL','FRESH_DATA_FAIL_CLOSED',
                   'DRIFT_BAND_PP','STRUCTURAL_USDT_TARGET','C1_BAG_FRACTION_P',
                   'C2_BAG_FRACTION_P','QF_MARGIN_CAP_PER_POSITION',
                   'QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL',
                   'RISK_REWARD_MIN','MAX_OPEN_POSITIONS','MAX_LEVERAGE',
                   'O5_BTC_PROCEEDS_FRACTION','O5_USDT_PROCEEDS_FRACTION',
                   'BSI_PROVIDER','HYPE_MACRO_PROVIDER')
_APPROVED = {'APROBADO', 'APROBADO_CONDICIONAL'}
_LOCK = threading.Lock()
_CACHE = {'loaded_at':0.0, 'state':None}

class SheetDataError(RuntimeError):
    """Sheet missing, untrusted, unavailable, or inconsistent. Never use stale JSON."""


def _cell(row, i, default=None):
    return row[i] if len(row)>i and row[i] is not None else default


def _number(value, label, *, minimum=0.0):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise SheetDataError(f'{label}: invalid numeric cell')
    result=float(value)
    if not math.isfinite(result) or result < minimum:
        raise SheetDataError(f'{label}: negative/non-finite value')
    return result


def _almost(a,b,eps=1e-6):
    return abs(a-b)<=max(eps, max(abs(a),abs(b))*1e-8)


def _map_rows(response):
    result={}
    for k,a1 in SHEETS.items():
        v=response.get(a1)
        if not isinstance(v,list):
            raise SheetDataError(f'{k}: missing Google Sheets range')
        result[k]=v
    return result


def parse_master(raw):
    """Build the v4 dashboard-compatible data shape from live Sheet data only."""
    blocks=_map_rows(raw)
    ctrl={str(r[0]):_cell(r,1) for r in blocks['control'][1:] if r and r[0]}
    if ctrl.get('estado_publicacion')!='PUBLICADO':
        raise SheetDataError('01_CONTROL: snapshot not PUBLICADO')
    if ctrl.get('schema_version')!='5.0.0' or not ctrl.get('snapshot_id') or not ctrl.get('fecha_corte') or not ctrl.get('publicado_utc'):
        raise SheetDataError('01_CONTROL: missing/invalid v5 publication identity')
    try:
        ts=datetime.fromisoformat(str(ctrl['publicado_utc']).replace('Z','+00:00'))
        if ts.tzinfo is None: raise ValueError('no UTC timezone')
        if ts.astimezone(timezone.utc)>datetime.now(timezone.utc).replace(microsecond=999999):
            raise ValueError('future publication')
    except (ValueError, TypeError) as exc:
        raise SheetDataError('01_CONTROL: invalid published_utc') from exc
    params={}
    for row in blocks['parameters'][1:]:
        if not row or not _cell(row,1):continue
        key=str(row[1]);
        if key in params:raise SheetDataError(f'duplicate parameter: {key}')
        params[key]={'module':_cell(row,0), 'value':_cell(row,2), 'type':_cell(row,3), 'unit':_cell(row,4),
                     'status':_cell(row,5), 'scope':_cell(row,6), 'source':_cell(row,7)}
    for key in REQUIRED_PARAMS:
        if key not in params or params[key]['status'] not in _APPROVED:
            raise SheetDataError(f'12_PARAMETROS_KAIROS: parameter {key} not approved')
    def pv(key):return params[key]['value']
    if pv('SNAPSHOT_PROVIDER')!='GOOGLE_SHEETS' or pv('BTC_NEVER_SELL') is not True or pv('FRESH_DATA_FAIL_CLOSED') is not True:
        raise SheetDataError('source/safety invariant not approved')
    # Ratios are governed by the approved Google Sheet, NOT hardcoded product constants.
    # The initial 30/70 was explicitly approved; a later administrative revision
    # changes the published Sheet revision and must preserve their total of 100%.
    btc_o5=_number(pv('O5_BTC_PROCEEDS_FRACTION'),'O5 BTC')
    usdt_o5=_number(pv('O5_USDT_PROCEEDS_FRACTION'),'O5 USDT')
    if max(btc_o5,usdt_o5)>1 or not _almost(btc_o5+usdt_o5,1):
        raise SheetDataError('O5 proceeds must sum to 100%')
    if _number(pv('STRUCTURAL_USDT_TARGET'),'USDT target')>1:
        raise SheetDataError('unapproved structural liquidity target')
    if pv('BSI_PROVIDER')!='BINANCE_SPOT_MCP_4H_SYNC' or pv('HYPE_MACRO_PROVIDER')!='HYPERLIQUID_SPOT_HYPE_USDC_MCP':
        raise SheetDataError('market source mismatch')
    for x in ('C1_BAG_FRACTION_P','C2_BAG_FRACTION_P','QF_MARGIN_CAP_PER_POSITION','QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL'):
        if _number(pv(x),x)>1: raise SheetDataError(f'{x}: invalid fraction')
    positions=[r for r in blocks['positions'][1:] if r and r[0] in SYMBOLS]
    if len(positions)!=12 or {r[0] for r in positions}!=SYMBOLS:
        raise SheetDataError('02_POSICIONES: exactly 12 unique assets required')
    holdings={}; custody={}; tiers={}; targets={}; costs={}; market_symbols={}; cost_total=0.0
    for r in positions:
        symbol=r[0]; quote_symbol=str(_cell(r,1,''))
        if quote_symbol != ('PUMP' if symbol=='PUMPFUN' else symbol):
            raise SheetDataError(f'{symbol}: MCP market symbol mismatch')
        t=_number(_cell(r,3),f'{symbol} target'); ho=_number(_cell(r,4),f'{symbol} HODL'); co=_number(_cell(r,5),f'{symbol} Core'); ex=_number(_cell(r,6),f'{symbol} Exchange')
        total=_number(_cell(r,7),f'{symbol} total'); declared=_number(_cell(r,13),f'{symbol} declared')
        if not _almost(ho+co+ex,total) or not _almost(total,declared):
            raise SheetDataError(f'{symbol}: custody units mismatch')
        if _cell(r,12)!='OK':raise SheetDataError(f'{symbol}: units validation not OK')
        cost=_number(_cell(r,8),f'{symbol} cost'); open_cost=_number(_cell(r,9),f'{symbol} open cost')
        if not _almost(total*cost,open_cost,eps=0.10):raise SheetDataError(f'{symbol}: cost mismatch')
        tiers[symbol]=r[2];targets[symbol]=t;holdings[symbol]=total;custody[symbol]=[ho,co,ex]
        costs[quote_symbol]=cost;market_symbols[symbol]=quote_symbol;cost_total+=open_cost
    if not _almost(sum(targets.values()),1.0):raise SheetDataError('targets do not total 100%')
    venues={}; qf=0.0
    for r in blocks['liquidity'][1:]:
        if not r or r[0] in ('TOTAL LIQUIDEZ','RESERVA TRADING QF','USDT OPERATIVO','Total informado por usuario','Diferencia de conciliación'):continue
        if _cell(r,1) is None:continue
        name=str(r[0]); amount=_number(r[1],f'{name} USDT'); classification=_cell(r,2)
        if name in venues: raise SheetDataError(f'duplicate USDT venue {name}')
        if classification not in ('TRADING_QF','OPERATIVO'):raise SheetDataError(f'{name}: unknown cash class')
        venues[name]=amount
        if classification=='TRADING_QF':
            if name!='Quantfury':raise SheetDataError('QF classification mismatch')
            qf+=amount
    if 'Quantfury' not in venues:raise SheetDataError('Quantfury reserve missing')
    liquidity=sum(venues.values());operating=liquidity-qf
    summary={str(r[0]):_cell(r,1) for r in blocks['liquidity'][1:] if r and len(r)>1 and r[0]}
    for k,v in (('TOTAL LIQUIDEZ',liquidity),('RESERVA TRADING QF',qf),('USDT OPERATIVO',operating),('Total informado por usuario',liquidity),('Diferencia de conciliación',0)):
        if not _almost(_number(summary.get(k),k),v,eps=.05):raise SheetDataError(f'03_LIQUIDEZ: {k} mismatch')
    if not _almost(_number(ctrl.get('Liquidez física'),'01_CONTROL cash'),liquidity,eps=.05):raise SheetDataError('01_CONTROL liquidity differs from 03_LIQUIDEZ')
    if not _almost(_number(ctrl.get('Costo abierto cripto'),'01_CONTROL cost'),cost_total,eps=.10):raise SheetDataError('01_CONTROL cost differs from positions')
    custody_targets={}
    for r in blocks['custody'][1:]:
        if not r or r[0] not in ('T1','T2','T3'):continue
        vals=[_number(_cell(r,i),f'{r[0]} custody fraction') for i in (1,2,3)]
        if not _almost(sum(vals),1.0) or _cell(r,4)!='OK':raise SheetDataError('04_CUSTODIA: invalid tier split')
        custody_targets[r[0]]=vals
    if set(custody_targets)!=set(('T1','T2','T3')):raise SheetDataError('04_CUSTODIA: missing tiers')
    # The user declared no open orders/fills pending; this is not remote exchange proof.
    for key in ('ordenes_activas_declaradas','fills_pendientes_registro_declarados'):
        if str(ctrl.get(key))!='0':raise SheetDataError(f'01_CONTROL: {key} requires current reconciliation')
    # Editorial notes are not transactions. Reconciled historical ledger rows may
    # remain on the Sheet; they must not change already-published holdings.
    # An OPEN or partially-filled order, an unverified fill or a duplicate key
    # still fails closed. This does not verify the remote exchange order book.
    _footnotes={
        'orders':'Al poblar órdenes: identificador único (Venue, Order ID), separar órdenes abiertas de fills, y reservar USDT antes de cualquier propuesta BUY.',
        'fills':'Jamás derivar fills de niveles tocados, simulaciones o LIMIT colocadas. Propuestas no son ejecución.',
    }
    _order_keys=set();_fill_keys=set();historical_orders=0;historical_fills=0
    for section in ('orders','fills'):
        for rownum,r in enumerate(blocks[section][1:],start=5):
            if not any(v not in (None,'') for v in r):continue
            if str(_cell(r,0,'')).strip()==_footnotes[section] and all(v in (None,'') for v in r[1:]):continue
            if section=='orders':
                venue=str(_cell(r,0,'')).strip();order_id=str(_cell(r,1,'')).strip()
                token=str(_cell(r,2,'')).strip();side=str(_cell(r,3,'')).upper().strip()
                status=str(_cell(r,11,'')).upper().strip();reconciled=str(_cell(r,15,'')).upper().strip()
                if not (venue and order_id and token in SYMBOLS.union({'PUMP'}) and side in ('BUY','SELL')
                        and status in ('FILLED','COMPLETED','CANCELLED','CANCELED','REJECTED','EXPIRED')
                        and reconciled in ('CONCILIADO','VERIFICADO')):
                    raise SheetDataError(f'orders: operational or unverified entry at row {rownum}; reconcile before use')
                key=(venue,order_id)
                if key in _order_keys:raise SheetDataError(f'orders: duplicate (venue,order_id) at row {rownum}')
                _order_keys.add(key);historical_orders+=1
            else:
                venue=str(_cell(r,0,'')).strip();order_id=str(_cell(r,1,'')).strip()
                trade_id=str(_cell(r,2,'')).strip();token=str(_cell(r,3,'')).strip()
                side=str(_cell(r,4,'')).upper().strip();confirmed=str(_cell(r,13,'')).upper().strip()
                if not (venue and order_id and trade_id and token in SYMBOLS.union({'PUMP'}) and side in ('BUY','SELL')
                        and confirmed in ('TRUE','CONCILIADO','VERIFICADO')):
                    raise SheetDataError(f'fills: operational or unverified entry at row {rownum}; reconcile before use')
                gross=_number(_cell(r,6),f'fills row {rownum} gross qty')
                net=_number(_cell(r,9),f'fills row {rownum} net qty')
                _number(_cell(r,10),f'fills row {rownum} gross USDT')
                if gross<=0 or net>gross:raise SheetDataError(f'fills: inconsistent gross/net units at row {rownum}')
                for i in (7,11):
                    if _cell(r,i) is not None:_number(_cell(r,i),f'fills row {rownum} fee')
                try:
                    ftime=datetime.fromisoformat(str(_cell(r,5,'')).replace('Z','+00:00'))
                    if ftime.tzinfo is None:raise ValueError('naive')
                except ValueError as e:raise SheetDataError(f'fills: invalid timestamp at row {rownum}') from e
                key=(venue,order_id,trade_id)
                if key in _fill_keys:raise SheetDataError(f'fills: duplicate (venue,order_id,trade_id) at row {rownum}')
                _fill_keys.add(key);historical_fills+=1
    pivot_levels={}; old_pivot_sources=set()
    for r in blocks['pivots'][1:]:
        if not r or r[0] not in SYMBOLS:continue
        symbol='PUMP' if r[0]=='PUMPFUN' else r[0]
        if _cell(r,14)=='REFERENCIA_HISTORICA':
            pivot_levels[symbol]={'c1':_cell(r,11),'c2':_cell(r,12),'state':'REFERENCIA_HISTORICA'}
            old_pivot_sources.add(str(_cell(r,15,'')))
        else:pivot_levels[symbol]={'c1':None,'c2':None,'state':'SIN_DATO'}
    if len(pivot_levels)!=12:raise SheetDataError('07_PIVOTES missing 12 rows')
    bsi_rows=[]
    for r in blocks['bsi'][1:]:
        if not r or r[0] not in SYMBOLS:continue
        bsi_rows.append({'token':'PUMP' if r[0]=='PUMPFUN' else r[0],
                         'legacy_anchor':_cell(r,1),'legacy_source':_cell(r,3),
                         'sample_bsi':_cell(r,14),'sample_close_utc':_cell(r,13),
                         'state':_cell(r,15), 'baseline':_cell(r,5), 'hwm':_cell(r,7)})
    if len(bsi_rows)!=12:raise SheetDataError('09_BSI missing 12 rows')
    if any(r['sample_close_utc']!=bsi_rows[0]['sample_close_utc'] for r in bsi_rows):
        raise SheetDataError('BSI archive 4H closes not synchronized')
    integral=blocks['integral']; meta={r[0]:_cell(r,1) for r in integral if r and r[0] in ('Capital inicial histórico','Pérdidas realizadas acumuladas','Capital vivo declarado')}
    segments=[]; mapping={'HODL + Core':'hodl_core','Exchange':'exchange','Liquidez':'liquidity','Trading':'trading','Lost · realizado':'lost'}
    for r in integral:
        if not r or r[0] not in mapping:continue
        segments.append({'key':mapping[r[0]],'name':r[0], 'target_usdt':_number(_cell(r,1),'integral target'),
                         'actual_usdt':_number(_cell(r,2),'integral value')})
    if len(segments)!=5:raise SheetDataError('08_INTEGRAL missing historical breakdown')
    validation={r[0]:_cell(r,1) for r in blocks['validation'][1:] if r and r[0]}
    for key in ('12 tokens Kairos presentes','Targets cripto suman 100%','Custodia suma unidades','Total USDT conciliado','Reserva QF sin duplicar'):
        if validation.get(key)!='OK':raise SheetDataError(f'11_VALIDACIONES: {key} not OK')
    if validation.get('Estado publicación')!='PUBLICADO':raise SheetDataError('11_VALIDACIONES: publication mismatch')
    snapshot={'holdings_total':holdings,'custody_core_blocked__core_strategic__exchange':custody,
              'physical_total_USDT':liquidity,'trading_real_fixed_USDT':qf,
              'kairos_operating_USDT_before_commitments':operating,
              'liquidity_venues_USDT':venues,'units_snapshot_as_of':ctrl['fecha_corte']}
    return {'control':ctrl,'snapshot':snapshot,'tokens':list(holdings), 'targets':targets,'tiers':tiers,
            'cost_basis':costs, 'parameters':params, 'custody_policy':custody_targets,
            'o2_levels':{'source':'Google Sheets 07_PIVOTES: REFERENCIA_HISTORICA NO CERTIFICADA',
                         'status':'REFERENCE_NOT_ACTIONABLE','levels':pivot_levels},
            'bsi_archive':bsi_rows,
            'integral':{'historical_capital_usdt':_number(meta.get('Capital inicial histórico'),'capital historical'),
                        'source_note':'Google Sheets 08_INTEGRAL: valores históricos, no precios actuales', 'segments':segments},
            'validation':validation, 'historical_ledger_counts':{'orders':historical_orders,'fills':historical_fills}}


def _remote_data():
    credentials_text=os.getenv('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON','').strip()
    file_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS','').strip()
    if not credentials_text and not file_path:
        raise SheetDataError('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS missing')
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    if credentials_text:
        try: creds=service_account.Credentials.from_service_account_info(json.loads(credentials_text),scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        except (ValueError,TypeError,KeyError) as exc:raise SheetDataError('Google service account JSON invalid') from exc
    elif file_path:
        creds=service_account.Credentials.from_service_account_file(file_path,scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    else:raise SheetDataError('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS missing')
    spreadsheet_id=os.getenv('KAIROS_GOOGLE_SHEET_ID',SHEET_ID_DEFAULT).strip()
    if not spreadsheet_id or not all(c.isalnum() or c in '-_' for c in spreadsheet_id):
        raise SheetDataError('KAIROS_GOOGLE_SHEET_ID invalid')
    # Never print service account secrets, request headers, or raw upstream URLs.
    url=f'https://sheets.googleapis.com/v4/spreadsheets/{quote(spreadsheet_id,safe="")}/values:batchGet'
    args=[('ranges',a) for a in SHEETS.values()]+[('valueRenderOption','UNFORMATTED_VALUE')]
    session=AuthorizedSession(creds)
    try:
        for attempt in range(3):
            response=session.get(url,params=args,timeout=20)
            if response.status_code in (429,502,503,504) and attempt < 2:
                time.sleep((1,3)[attempt]);continue
            if response.status_code!=200:
                raise SheetDataError(f'Google Sheets HTTP {response.status_code}')
            payload=response.json()
            items=payload.get('valueRanges')
            if not isinstance(items,list) or len(items)!=len(SHEETS):
                raise SheetDataError('Google Sheets incomplete batchGet')
            return {a1:r.get('values',[]) for a1,r in zip(SHEETS.values(),items)}
        raise SheetDataError('Google Sheets unavailable')
    finally:
        session.close()


def public_failure_code(exc):
    """Safe diagnostics: no credentials, request headers, private keys or URLs."""
    if not isinstance(exc,SheetDataError):
        return 'GOOGLE_TRANSPORT_OR_AUTH_ERROR'
    msg=str(exc)
    if 'missing' in msg and ('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON' in msg or 'GOOGLE_APPLICATION_CREDENTIALS' in msg):
        return 'GOOGLE_CREDENTIALS_MISSING'
    if 'service account JSON invalid' in msg:
        return 'GOOGLE_CREDENTIALS_INVALID_JSON'
    if msg.startswith('Google Sheets HTTP '):
        code=msg.rsplit(' ',1)[-1]
        return 'GOOGLE_SHEETS_HTTP_'+code if code.isdigit() else 'GOOGLE_SHEETS_HTTP_ERROR'
    if 'incomplete batchGet' in msg or 'unavailable' in msg:
        return 'GOOGLE_SHEETS_INCOMPLETE'
    if msg.startswith('orders:') or msg.startswith('fills:'):
        return 'ORDERS_FILLS_RECONCILIATION_REQUIRED'
    if 'PUBLICADO' in msg or 'publication' in msg:
        return 'SHEET_NOT_PUBLISHED'
    return 'GOOGLE_SHEETS_CONTRACT_INVALID'


def get_state(*,force=False):
    """Return a validated immutable-by-convention state; never fall back on stale/JSON."""
    ttl=min(300,max(10,int(os.getenv('KAIROS_SHEETS_CACHE_SECONDS','60'))))
    with _LOCK:
        if not force and _CACHE['state'] is not None and time.monotonic()-_CACHE['loaded_at']<ttl:
            return _CACHE['state']
        state=parse_master(_remote_data())
        _CACHE.update(state=state,loaded_at=time.monotonic())
        return state


def invalidate_cache():
    with _LOCK:
        _CACHE.update(state=None,loaded_at=0.0)


def cache_status():
    with _LOCK:
        age=max(0.0,time.monotonic()-_CACHE['loaded_at']) if _CACHE['state'] is not None else None
        return {'loaded':_CACHE['state'] is not None, 'age_seconds':round(age,1) if age is not None else None,
                'snapshot_id':_CACHE['state']['control']['snapshot_id'] if _CACHE['state'] else None}
