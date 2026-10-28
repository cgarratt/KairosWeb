"""KairosWeb v1.0.0: strictly read-only Google Sheets client and contract validator.

No local snapshot/config JSON fallback.  Uses credentials only from Render secrets.
Snapshot publication and per-field parameter status are independent gates.
"""
import json
import math
import os
import re
import threading
import time
from datetime import datetime, timezone
from urllib.parse import quote

HOMOLOGATION_RANGE = "'13_CONTROL_HOMOLOGACION'!A4:D20"
HOMOLOGATION_HISTORY_RANGE = "'25_HOMOLOGACION_HISTORIAL'!A1:O2000"
WORKFLOW_RANGE = "'26_ORDENES_GESTION'!A1:W2000"
SHEET_ID_DEFAULT = '1_tG5FK_u0biVZm2iXaK6fJi1enBYJYLAG6txkpTgsy8'
SHEETS = {
    'control': "'01_CONTROL'!A4:C31",
    'positions': "'02_POSICIONES'!A4:N17",
    'liquidity': "'03_LIQUIDEZ'!A4:F17",
    'custody': "'04_CUSTODIA'!A4:G7",
    'orders': "'05_ORDENES'!A4:P250",
    'fills': "'06_FILLS'!A4:P250",
    'pivots': "'07_PIVOTES'!A4:AA16",
    'integral': "'08_INTEGRAL'!A4:F15",
    'bsi': "'09_BSI'!A4:S16",
    'validation': "'11_VALIDACIONES'!A4:D25",
    'parameters': "'12_PARAMETROS_KAIROS'!A4:J230",
}
SYMBOLS = frozenset(('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE'))
REQUIRED_PARAMS = ('SNAPSHOT_PROVIDER','BTC_NEVER_SELL','FRESH_DATA_FAIL_CLOSED',
                   'DRIFT_BAND_PP','STRUCTURAL_USDT_TARGET','QF_MARGIN_CAP_PER_POSITION',
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
    # Optional diagnostic evidence; missing records do not rewrite or certify balances.
    result['homologation'] = response.get(HOMOLOGATION_RANGE, [])
    result['homologation_history'] = response.get(HOMOLOGATION_HISTORY_RANGE, [])
    result['order_workflow'] = response.get(WORKFLOW_RANGE, [])
    return result


def _legacy_cash_number(value):
    text=str(value or '')
    match=re.search(r'USDT f[íi]sico\s+([0-9.,]+)',text,re.IGNORECASE)
    if not match:return None
    digits=match.group(1).replace(',', '').replace('.', '')
    return int(digits) if digits.isdigit() else None


HOMOLOGATION_HEADERS = [
    'snapshot_id','fecha_corte','publicado_utc','homologado_utc','schema_version',
    'tokens','targets','custodia','liquidez_qf','usdt_fisico','qf','usdt_operativo',
    'pivotes','bsi','certificacion',
]


def homologation_certificate(state, snapshot_id, published_utc, certified_utc):
    """Validated accounting-only evidence; NEVER certifies remote fills/pivots/BSI."""
    snap=state['snapshot']
    if len(state['tokens'])!=12 or abs(sum(state['targets'].values())-1)>1e-7:
        raise SheetDataError('homologation: invalid token universe/targets')
    if set(state['custody_policy'])!={'T1','T2','T3'}:
        raise SheetDataError('homologation: incomplete custody policy')
    if any(k not in state['validation'] or state['validation'][k]!='OK'
           for k in ('12 tokens Kairos presentes','Targets cripto suman 100%',
                     'Custodia suma unidades','Total USDT conciliado','Reserva QF sin duplicar')):
        raise SheetDataError('homologation: pending critical validations')
    cash=float(snap['physical_total_USDT'])
    qf=float(snap['trading_real_fixed_USDT'])
    operating=float(snap['kairos_operating_USDT_before_commitments'])
    if qf<0 or operating<0 or abs(cash-qf-operating)>.05:
        raise SheetDataError('homologation: QF cash not reconciled')
    return [snapshot_id,str(state['control']['fecha_corte']),published_utc,certified_utc,
            '5.0.0','PASS','PASS','PASS','PASS',round(cash,8),round(qf,8),round(operating,8),
            'PENDIENTE_CERTIFICACION','BSI_SELL_BLOQUEADO','BASE_CONTABLE_VALIDADA']


def _review_history(control, rows, cash, qf):
    """Only the latest ledger entry is authoritative; an old PASS is never carried forward."""
    records=[r for r in (rows or [])[1:] if r and r[0]]
    if not records:return None
    newest=records[-1]
    snapshot=str(_cell(newest,0,'') or '')
    issues=[]
    if snapshot != str(control['snapshot_id']):
        issues.append({'code':'SNAPSHOT_REFERENCE_STALE','control':'25_HOMOLOGACION_HISTORIAL',
                       'detail':'La última homologación corresponde a otra publicación.'})
    if str(_cell(newest,1,'')) != str(control['fecha_corte']) or str(_cell(newest,2,'')) != str(control['publicado_utc']):
        issues.append({'code':'PUBLICATION_IDENTITY_MISMATCH','control':'25_HOMOLOGACION_HISTORIAL',
                       'detail':'Corte o momento de publicación diferente.'})
    if str(_cell(newest,4,''))!='5.0.0' or any(str(_cell(newest,i,''))!='PASS' for i in (5,6,7,8)):
        issues.append({'code':'HOMOLOGATION_VALIDATION_INCOMPLETE','control':'25_HOMOLOGACION_HISTORIAL',
                       'detail':'No están aprobados todos los controles contables obligatorios.'})
    try:
        values=[float(_cell(newest,i,'')) for i in (9,10,11)]
        if any(not math.isfinite(v) for v in values) or abs(values[0]-cash)>.05 or abs(values[1]-qf)>.05 or abs(values[2]-(cash-qf))>.05:
            raise ValueError('mismatch')
    except (ValueError,TypeError):
        issues.append({'code':'LIQUIDITY_REFERENCE_STALE','control':'25_HOMOLOGACION_HISTORIAL',
                       'detail':'Evidencia de USDT/QF no coincide con publicación.'})
    if str(_cell(newest,14,''))!='BASE_CONTABLE_VALIDADA':
        issues.append({'code':'HOMOLOGATION_SCOPE_UNVERIFIED','control':'25_HOMOLOGACION_HISTORIAL',
                       'detail':'Alcance de la certificación no válido.'})
    return {'status':'CURRENT' if not issues else 'STALE',
            'checked_against_snapshot':control['snapshot_id'],'issues':issues,
            'read_only':True,'source':'25_HOMOLOGACION_HISTORIAL',
            'certified_utc':_cell(newest,3),'certification_scope':'BASE_CONTABLE',
            'pending_controls':['PIVOTES_CERTIFICACION', 'BSI_SELL_BASELINE_HWM', 'LIBRO_EXCHANGE_REMOTO'],
            'history_count':len(records)}


def assess_homologation(control, rows, liquidity, history_rows=None, qf=0):
    """Read-only certification freshness audit; historical notes never replace published values.

    PASS in an old 13_CONTROL row is not proof of the current 01_CONTROL.
    Missing/partial homologation is UNKNOWN (not a forced Sheet contract error).
    """
    current=_review_history(control,history_rows,liquidity,qf)
    if current is not None:return current
    rows=list(rows or [])
    if not rows or len(rows)<2:
        return {'status':'NOT_VERIFIED','checked_against_snapshot':control['snapshot_id'],
                'issues':[{'code':'HOMOLOGATION_UNAVAILABLE','control':'13_CONTROL_HOMOLOGACION',
                           'detail':'No fue posible verificar los controles históricos contra la publicación vigente.'}],
                'read_only':True,'source':'13_CONTROL_HOMOLOGACION'}
    issues=[]
    for row in rows[1:]:
        if not row or not row[0]:continue
        label=str(row[0]); verdict=str(_cell(row,1,'')).upper(); evidence=str(_cell(row,2,'') or '')
        if label=='01_CONTROL PUBLICADO' and verdict=='PASS':
            if control['snapshot_id'] not in evidence:
                issues.append({'code':'SNAPSHOT_REFERENCE_STALE','control':label,
                               'detail':'El PASS histórico no corresponde al snapshot publicado actualmente.'})
        if label=='03_LIQUIDEZ QF UNA VEZ' and verdict=='PASS':
            quoted=_legacy_cash_number(evidence)
            if quoted is None:
                issues.append({'code':'LIQUIDITY_EVIDENCE_UNVERIFIED','control':label,
                               'detail':'La evidencia histórica no permite comprobar el USDT vigente.'})
            elif abs(quoted-liquidity)>.05:
                issues.append({'code':'LIQUIDITY_REFERENCE_STALE','control':label,
                               'detail':'El USDT de la evidencia histórica no coincide con el publicado.'})
    status='STALE' if any(i['code'].endswith('_STALE') for i in issues) else ('CHECK_REQUIRED' if issues else 'CURRENT')
    return {'status':status,'checked_against_snapshot':control['snapshot_id'],
            'issues':issues,'read_only':True,'source':'13_CONTROL_HOMOLOGACION'}


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
    for x in ('QF_MARGIN_CAP_PER_POSITION','QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL'):
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
    # Open orders are allowed when individually documented and reserved below.
    # A declared count is not evidence of exchange execution.
    declared_open=_number(int(str(ctrl.get('ordenes_activas_declaradas','0'))), 'declared open orders') if str(ctrl.get('ordenes_activas_declaradas','0')).isdigit() else None
    if declared_open is None or str(ctrl.get('fills_pendientes_registro_declarados','0'))!='0':
        raise SheetDataError('01_CONTROL: unresolved orders/fills declaration')
    # Editorial notes are not transactions. Reconciled historical ledger rows may
    # remain on the Sheet; they must not change already-published holdings.
    # An OPEN or partially-filled order, an unverified fill or a duplicate key
    # still fails closed. This does not verify the remote exchange order book.
    _footnotes={
        'orders':'Al poblar órdenes: identificador único (Venue, Order ID), separar órdenes abiertas de fills, y reservar USDT antes de cualquier propuesta BUY.',
        'fills':'Jamás derivar fills de niveles tocados, simulaciones o LIMIT colocadas. Propuestas no son ejecución.',
    }
    # Historical execution ledgers are evidence only: published units and USDT
    # already include their effects. Never add fills to the snapshot again.
    _order_keys=set();_order_records={};_fill_keys=set()
    _fill_forms_by_order={};historical_orders=0;historical_fills=0;pending_ledger=[]
    for section in ('orders','fills'):
        for rownum,r in enumerate(blocks[section][1:],start=5):
            if not any(v not in (None,'') for v in r):continue
            if str(_cell(r,0,'')).strip()==_footnotes[section] and all(v in (None,'') for v in r[1:]):continue
            if section=='orders':
                venue=str(_cell(r,0,'')).strip();order_id=str(_cell(r,1,'')).strip()
                token=str(_cell(r,2,'')).strip();side=str(_cell(r,3,'')).upper().strip()
                status=str(_cell(r,11,'')).upper().strip();reconciled=str(_cell(r,15,'')).upper().strip()
                # The published MASTER writes a longer, explicit link to the
                # reconciled fill ("CONCILIADO · 06_FILLS fila5; ..."). The old
                # exact-string gate incorrectly rejected that verified format.
                linked_reconciled=bool(re.match(r'^CONCILIADO\s*[·-]\s*06_FILLS\s+FILA\s*\d+\b',reconciled))
                is_pending=status in ('PENDIENT','PENDIENTE','OPEN','NEW','PARTIALLY_FILLED','PARCIAL','CONFIRMADA')
                is_closed=status in ('FILLED','COMPLETED','CANCELLED','CANCELED','REJECTED','EXPIRED')
                evidence=str(_cell(r,14,'') or '').strip()
                if not (venue and token in SYMBOLS.union({'PUMP'}) and side in ('BUY','SELL')
                        and (is_pending or is_closed) and evidence):
                    raise SheetDataError(f'orders: reconcile unverified entry at row {rownum}')
                if is_pending:
                    # A local reference is NOT an exchange order ID. Require a
                    # deterministic source reference and the missing-ID flag.
                    provisional=('PENDIENTE_ID_EXCHANGE' in reconciled and 'Referencia local' in evidence)
                    hype_quote=(venue=='Hyperliquid' and token=='HYPE' and side=='BUY'
                                and 'PENDIENTE_ID_QTY_QUOTE_INSTRUMENTO' in reconciled
                                and 'HYPE' in evidence)
                    if not order_id and not (provisional or hype_quote):
                        raise SheetDataError(f'orders: missing provisional reference at row {rownum}')
                    if not _almost(_number(_cell(r,8,0), 'executed qty'),0):
                        raise SheetDataError(f'orders: reconcile partial execution needs fill at row {rownum}')
                    price=_number(_cell(r,6), 'pending LIMIT price')
                    raw_qty=_cell(r,7)
                    quantity=0.0 if raw_qty in (None,'') and hype_quote else _number(raw_qty, 'pending qty')
                    budget=_number(_cell(r,9), 'pending commitment')
                    if price<=0 or budget<=0 or (not hype_quote and
                        (quantity<=0 or not _almost(price*quantity,budget,eps=.05))):
                        raise SheetDataError(f'orders: pending budget mismatch at row {rownum}')
                    if hype_quote and quantity and not _almost(price*quantity,budget,eps=.05):
                        raise SheetDataError(f'orders: HYPE quantity/budget mismatch at row {rownum}')
                    if hype_quote and not order_id:
                        # Local identity, never a fabricated exchange order ID.
                        key=(venue,'HYPE_QUOTE|'+str(price)+'|'+str(budget)+'|'+evidence)
                    else:
                        key=(venue,order_id or evidence.split('Referencia local (NOOrderID):',1)[-1].split('"',1)[0].strip())
                elif status in ('CANCELLED','CANCELED'):
                    # Cancellation is not a fill. The user can attest that a
                    # pending order was cancelled even when the exchange ID
                    # was absent from the original screenshot. No liquidity is
                    # added; its prior commitment simply ceases to be reserved.
                    if ('CANCELACION_DECLARADA_USUARIO_2026-10-26' not in reconciled
                            or 'NO_VERIFICADA_API' not in reconciled
                            or not _almost(_number(_cell(r,8,0),'cancelled executed qty'),0)):
                        raise SheetDataError(f'orders: cancelled entry lacks attestation at row {rownum}')
                    price=_number(_cell(r,6),'cancelled limit price')
                    budget=_number(_cell(r,9),'cancelled commitment')
                    if price<=0 or budget<=0 or side!='BUY':
                        raise SheetDataError(f'orders: invalid cancelled order at row {rownum}')
                    key=(venue,order_id or f'CANCELLED|{token}|{price}|{budget}|{rownum}')
                else:
                    if not (order_id and (reconciled in ('CONCILIADO','VERIFICADO') or linked_reconciled)):
                        raise SheetDataError(f'orders: closed entry not reconciled at row {rownum}')
                    key=(venue,order_id)
                if key in _order_keys:raise SheetDataError(f'orders: duplicate key at row {rownum}')
                _order_keys.add(key)
                if is_pending:
                    pending_ledger.append((venue,token,side,quantity,budget,key))
                else:
                    _order_records[key]={'token':token,'side':side,'status':status,
                        'qty_executed':_cell(r,8), 'evidence':evidence,
                        'linked_reconciled':linked_reconciled}
                historical_orders+=1
            else:
                venue=str(_cell(r,0,'')).strip();order_id=str(_cell(r,1,'')).strip()
                trade_id=str(_cell(r,2,'') or '').strip();token=str(_cell(r,3,'')).strip()
                side=str(_cell(r,4,'')).upper().strip();confirmed=str(_cell(r,13,'')).upper().strip()
                ledger_key=str(_cell(r,15,'') or '').strip()
                order=_order_records.get((venue,order_id))
                # Trade IDs and timezone are not always exposed in screenshot
                # evidence. Permit an ORDER-LEVEL AGGREGATE only if it has a
                # dedicated, non-duplicable provenance key, a reconciled FILLED
                # order, evidence on both ledgers, and matching quantities.
                aggregate=(not trade_id and ledger_key==f'{venue}|{order_id}|ORDER_AGGREGATE_NO_TRADE_IDS')
                closed_link=(order and order['status'] in ('FILLED','COMPLETED')
                             and order['side']==side and order['token']==token
                             and order['linked_reconciled'] and order['evidence']
                             and str(_cell(r,14,'') or '').strip())
                if not (venue and order_id and token in SYMBOLS.union({'PUMP'}) and side in ('BUY','SELL')
                        and ((aggregate and confirmed in ('SI','TRUE','CONCILIADO','VERIFICADO') and closed_link)
                             or (trade_id and confirmed in ('TRUE','CONCILIADO','VERIFICADO')))):
                    raise SheetDataError(f'fills: operational or unverified entry at row {rownum}; reconcile before use')
                gross=_number(_cell(r,6),f'fills row {rownum} gross qty')
                net=_number(_cell(r,9),f'fills row {rownum} net qty')
                gross_usdt=_number(_cell(r,10),f'fills row {rownum} gross USDT')
                if gross<=0 or gross_usdt<=0 or net>gross or net<=0:
                    raise SheetDataError(f'fills: inconsistent gross/net units at row {rownum}')
                for i in (7,11):
                    if _cell(r,i) is not None:_number(_cell(r,i),f'fills row {rownum} fee')
                raw_time=_cell(r,5)
                if raw_time not in (None,''):
                    try:
                        ftime=datetime.fromisoformat(str(raw_time).replace('Z','+00:00'))
                        if ftime.tzinfo is None:raise ValueError('naive')
                    except ValueError as e:raise SheetDataError(f'fills: invalid timestamp at row {rownum}') from e
                elif not aggregate:
                    raise SheetDataError(f'fills: missing UTC timestamp at row {rownum}; reconcile before use')
                if aggregate:
                    if not _almost(_number(order['qty_executed'],f'orders qty matched row {rownum}'),gross,eps=1e-8):
                        raise SheetDataError(f'fills: aggregate quantity does not match linked order at row {rownum}')
                    fee=_cell(r,7,0)
                    if str(_cell(r,8,''))==token and not _almost(gross-_number(fee,'fee'),net,eps=1e-7):
                        raise SheetDataError(f'fills: aggregate token fee mismatch at row {rownum}')
                form='aggregate' if aggregate else 'trade'
                forms=_fill_forms_by_order.setdefault((venue,order_id),set())
                if forms and form not in forms:
                    raise SheetDataError(f'fills: aggregate and trade-level records overlap at row {rownum}')
                forms.add(form)
                key=('AGG',venue,order_id) if aggregate else ('TRADE',venue,order_id,trade_id)
                if key in _fill_keys:raise SheetDataError(f'fills: duplicate evidence key at row {rownum}')
                _fill_keys.add(key);historical_fills+=1
    # Confirmed manual orders are tracked separately in 26_ORDENES_GESTION.
    # Never credit a stated execution to physical custody or balances until
    # 05_ORDENES/06_FILLS and the next published snapshot are reconciled.
    from orders_workflow import events_from_rows, latest_orders, WorkflowError
    reservations={};reserved_buy_usdt=0.;workflow_pending=[];foreign_quote_pending=False
    reserved_buy_by_venue={};pending_foreign_quotes=[]
    for venue,token,side,qty,budget,key in pending_ledger:
        if side=='BUY':
            if token=='HYPE' and venue=='Hyperliquid':
                foreign_quote_pending=True  # HYPE USDC: do not treat as USDT
                pending_foreign_quotes.append({"venue":venue,"token":token,"amount":budget,"currency":"USDC_UNVERIFIED"})
            else:
                reserved_buy_usdt+=budget
                reserved_buy_by_venue[venue]=reserved_buy_by_venue.get(venue,0.)+budget
        else:
            symbol='PUMPFUN' if token=='PUMP' else token
            if symbol=='BTC':raise SheetDataError('orders: BTC NEVER SELL')
            reservations[symbol]=reservations.get(symbol,0.)+qty
    if declared_open!=len(pending_ledger):
        raise SheetDataError(f'orders: reconcile declared open count {declared_open} differs from {len(pending_ledger)} verified')
    try:
        active=latest_orders(events_from_rows(blocks['order_workflow']))
        for entry in active:
            if entry['estado'] not in ('CONFIRMADA','PARCIAL','EJECUTADA'):continue
            if (entry['venue'],str(entry['exchange_order_id'])) in _fill_forms_by_order:
                continue  # only actual filled evidence in canonical 05 AND 06 releases funds
            token=str(entry['token']);side=str(entry['lado'])
            qty=_number(entry['unidades_previstas'],'workflow qty')
            gross=_number(entry['importe_previsto'],'workflow budget')
            # A direct fill may have no planned size; then its actual quantity is
            # still pending and must remain quarantined from available positions.
            if qty==0:qty=_number(entry['unidades_ejecutadas'],'workflow filled qty')
            if gross==0:gross=_number(entry['importe_ejecutado'],'workflow filled amount')
            if side=='BUY':
                if entry['moneda_cotizada']!='USDT':
                    # Exchange USDC is not USDT. Treat pending HYPE quotes as a
                    # global simulation hold, never as new cash/real transfer.
                    foreign_quote_pending=True
                    pending_foreign_quotes.append({"venue":entry["venue"],"token":token,"amount":gross,"currency":entry["moneda_cotizada"]})
                else:
                    reserved_buy_usdt+=gross
                    reserved_buy_by_venue[entry["venue"]]=reserved_buy_by_venue.get(entry["venue"],0.)+gross
            elif side=='SELL':
                key='PUMPFUN' if token=='PUMP' else token
                reservations[key]=reservations.get(key,0.)+qty
            else:raise WorkflowError('INVALID_ORDER','Tipo de orden inválido')
            workflow_pending.append(entry)
        # Foreign-quoted HYPE orders cannot be deducted from USDT as if USDC.
        # Quarantine only the affected venue's USDT balance until independently
        # verified; never block unrelated Binance/KuCoin balances.
        quarantined_venue_usdt=sum(float(venues.get(v,0)) for v in {e['venue'] for e in pending_foreign_quotes})
        # Venue-level availability is reported separately; unverified venue
        # settlement must not be assumed to release committed funds.
        if reserved_buy_usdt>operating+0.01:
            raise WorkflowError('OVERCOMMITTED','Órdenes de compra confirmadas superan caja no QF')
        for token,amount in reservations.items():
            if token=='BTC' or amount>custody[token][2]+1e-8:
                raise WorkflowError('OVERCOMMITTED','Órdenes de venta pendientes superan Exchange libre')
    except WorkflowError as exc:
        raise SheetDataError(f'26_ORDENES_GESTION: {exc.code}') from exc
    from wave_pivots import wave_row, fib_from_anchors, WavePivotError
    pivot_levels={}; wave_pivots={}; old_pivot_sources=set()
    for r in blocks['pivots'][1:]:
        if not r or r[0] not in SYMBOLS:continue
        symbol='PUMP' if r[0]=='PUMPFUN' else r[0]
        try:wave_pivots[symbol]=wave_row(r)
        except WavePivotError as exc:raise SheetDataError(str(exc)) from exc
        anchors=fib_from_anchors(wave_pivots[symbol]['cycle_low'],wave_pivots[symbol]['waves']['o1']['price'])
        if not wave_pivots[symbol]['timeline_valid']:
            pivot_levels[symbol]={'c1':None,'c2':None,'state':'CRONOLOGIA_INVALIDA','issues':wave_pivots[symbol]['timeline_issues']}
        elif anchors:
            pivot_levels[symbol]={**anchors,'state':'ANCHORS_ESTIMADOS_O_CONFIRMADOS',
                                  'certified_o1':wave_pivots[symbol]['waves']['o1']['status']=='CONFIRMADO',
                                  'source':'07_PIVOTES CL/O1; sólo simulación'}
        elif _cell(r,11) is not None and _cell(r,12) is not None:
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
    historical_notes=[str(_cell(r,5,'')) for r in integral if r and r[0] in mapping]
    historical_date_refs=sorted(set(re.findall(r'\b(\d{1,2}/\d{1,2})(?:/\d{4})?\b', ' '.join(historical_notes))))
    historical_reference_label=(' / '.join(historical_date_refs) + ' (año no indicado en la hoja)') if historical_date_refs else 'N/D (fecha no publicada)'
    validation={r[0]:_cell(r,1) for r in blocks['validation'][1:] if r and r[0]}
    for key in ('12 tokens Kairos presentes','Targets cripto suman 100%','Custodia suma unidades','Total USDT conciliado','Reserva QF sin duplicar'):
        if validation.get(key)!='OK':raise SheetDataError(f'11_VALIDACIONES: {key} not OK')
    if validation.get('Estado publicación')!='PUBLICADO':raise SheetDataError('11_VALIDACIONES: publication mismatch')
    homologation=assess_homologation(ctrl,blocks['homologation'],liquidity,blocks['homologation_history'],qf)
    snapshot={'holdings_total':holdings,'custody_core_blocked__core_strategic__exchange':custody,
              'physical_total_USDT':liquidity,'trading_real_fixed_USDT':qf,
              'kairos_operating_USDT_before_commitments':operating,
              'liquidity_venues_USDT':venues,'units_snapshot_as_of':ctrl['fecha_corte'],
              'reserved_buy_usdt':reserved_buy_usdt+quarantined_venue_usdt,
              'reserved_buy_usdt_verified':reserved_buy_usdt,
              'reserved_buy_usdt_by_venue':reserved_buy_by_venue,
              'foreign_quote_pending':pending_foreign_quotes,
              'quarantined_venue_usdt':quarantined_venue_usdt,
              'reserved_sell_units_by_token':reservations}
    return {'control':ctrl,'snapshot':snapshot,'tokens':list(holdings), 'targets':targets,'tiers':tiers,
            'cost_basis':costs, 'parameters':params, 'custody_policy':custody_targets,
            'wave_pivots':wave_pivots,
            'o2_levels':{'source':'Google Sheets 07_PIVOTES: CL/O1 estimados o confirmados por onda; referencias históricas supletorias, simulación',
                         'status':'REFERENCE_NOT_ACTIONABLE','levels':pivot_levels},
            'bsi_archive':bsi_rows,
            'integral':{'historical_capital_usdt':_number(meta.get('Capital inicial histórico'),'capital historical'),
                        'source_note':'Google Sheets 08_INTEGRAL: valores históricos, no precios actuales',
                            'reference_date_label':historical_reference_label,'segments':segments},
            'validation':validation,'homologation':homologation, 'workflow_pending':workflow_pending,'historical_ledger_counts':{'orders':historical_orders,'fills':historical_fills},'pending_ledger_count':len(pending_ledger)}


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
    args=[('ranges',a) for a in SHEETS.values()]+[('ranges',HOMOLOGATION_RANGE),('valueRenderOption','UNFORMATTED_VALUE')]
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
            if not isinstance(items,list) or len(items) not in (len(SHEETS),len(SHEETS)+1):
                raise SheetDataError('Google Sheets incomplete batchGet')
            result={a1:r.get('values',[]) for a1,r in zip(SHEETS.values(),items)}
            if len(items)>len(SHEETS):result[HOMOLOGATION_RANGE]=items[-1].get('values',[])
            # New append-only ledger is optional for installations older than v2.0.31.
            # Never mutate a Sheet on GET; 404/400 indicates tab not created yet.
            history_response=session.get(url,params=[('ranges',HOMOLOGATION_HISTORY_RANGE),
                                                        ('valueRenderOption','UNFORMATTED_VALUE')],timeout=20)
            if history_response.status_code==200:
                history=history_response.json().get('valueRanges') or []
                result[HOMOLOGATION_HISTORY_RANGE]=(history[0].get('values',[]) if history else [])
            elif history_response.status_code in (400,404):
                result[HOMOLOGATION_HISTORY_RANGE]=[]
            else:
                raise SheetDataError(f'Google Sheets HTTP {history_response.status_code}')
            # Workflow sheet is optional until an authorized manager creates it.
            workflow_response=session.get(url,params=[('ranges',WORKFLOW_RANGE),
                         ('valueRenderOption','UNFORMATTED_VALUE')],timeout=20)
            if workflow_response.status_code==200:
                seq=workflow_response.json().get('valueRanges') or []
                result[WORKFLOW_RANGE]=seq[0].get('values',[]) if seq else []
            elif workflow_response.status_code in (400,404):
                result[WORKFLOW_RANGE]=[]
            else:raise SheetDataError(f'Google Sheets workflow HTTP {workflow_response.status_code}')
            return result
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
