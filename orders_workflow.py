"""KairosWeb order lifecycle journal (Google Sheets, append-only).

Records administrator-verified manual status/evidence; it NEVER sends exchange
orders or credits/debits holdings. Execution evidence must be reconciled against
05_ORDENES, 06_FILLS and the published inventory via a separate certified step.
"""
from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone
from orders_inbox import VENUES

TAB = '26_ORDENES_GESTION'
HEADERS = (
    'event_id', 'kairos_order_id', 'revision', 'actualizado_utc', 'snapshot_referencia',
    'venue', 'token', 'lado', 'tramo', 'origen', 'estado', 'exchange_order_id',
    'unidades_previstas', 'importe_previsto', 'unidades_ejecutadas',
    'importe_ejecutado', 'comision_token', 'comision_cotizada',
    'moneda_comision', 'evidencia', 'observaciones', 'conciliacion', 'moneda_cotizada',
)
STATES=('PROPUESTA','CONFIRMADA','PARCIAL','EJECUTADA')
CATEGORIES=('BALANCE','ESTRUCTURA','MANUAL')
_QUOTES={'HYPE':'USDC'}
_ALLOWED_TOKENS=set(VENUES)
_ID=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:\-]{2,119}$')
_STAGE=re.compile(r'^[A-Za-z0-9_]{2,25}$')


class WorkflowError(ValueError):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code=code


def number(value, field, *, positive=False):
    if isinstance(value,bool) or value in ('',None):
        if positive:raise WorkflowError('MISSING_AMOUNT',f'{field}: requerido')
        return 0.0
    try: result=float(value)
    except (TypeError, ValueError):raise WorkflowError('INVALID_AMOUNT',f'{field}: número inválido')
    if not math.isfinite(result) or result < 0 or (positive and result<=0):
        raise WorkflowError('INVALID_AMOUNT',f'{field}: debe ser positivo y finito')
    return result


def text(value,field,size=250,required=False):
    val=str(value or '').strip()
    if len(val)>size or (required and not val):
        raise WorkflowError('INVALID_FIELD',f'{field}: ausente o demasiado largo')
    return val


def events_from_rows(rows):
    if not rows:return []
    if tuple(rows[0][:len(HEADERS)])!=HEADERS:
        raise WorkflowError('SCHEMA_MISMATCH','Encabezados de la hoja 26 incompatibles; no escribir')
    records=[]
    for r in rows[1:]:
        if not r or not r[0]:continue
        item={k:r[i] if i<len(r) else None for i,k in enumerate(HEADERS)}
        if item['estado'] not in STATES or not item['kairos_order_id']:
            raise WorkflowError('INVALID_HISTORY','Historial de gestión inválido')
        try: item['revision']=int(item['revision'])
        except (ValueError,TypeError):raise WorkflowError('INVALID_HISTORY','Revisión histórica inválida')
        records.append(item)
    if len({r['event_id'] for r in records})!=len(records):
        raise WorkflowError('DUPLICATE_EVENT','Evento histórico duplicado')
    return records


def latest_orders(events):
    state={}
    for record in events:
        key=record['kairos_order_id'];old=state.get(key)
        if old and record['revision']!=old['revision']+1:
            raise WorkflowError('INVALID_HISTORY','Transiciones con revisiones incompatibles')
        if not old and record['revision']!=1:
            raise WorkflowError('INVALID_HISTORY','Falta el evento inicial')
        state[key]=record
    return list(reversed(list(state.values())))


def validate_transition(action, data, old=None, others=(), existing_exchange=()):
    """Pure validation, no Sheets or network effects."""
    action=str(action or '').upper().strip()
    if action not in STATES:raise WorkflowError('INVALID_TRANSITION','Estado de orden no admitido')
    if old is None and action!='PROPUESTA':
        raise WorkflowError('INVALID_TRANSITION','Primero registra la propuesta')
    if old and ((old['estado']=='EJECUTADA') or (old['estado']=='PROPUESTA' and action not in ('CONFIRMADA','EJECUTADA'))
                or (old['estado']=='CONFIRMADA' and action not in ('PARCIAL','EJECUTADA'))
                or (old['estado']=='PARCIAL' and action not in ('PARCIAL','EJECUTADA'))):
        raise WorkflowError('INVALID_TRANSITION','Transición no autorizada')
    if action=='PROPUESTA':
        token=text(data.get('token'),'Token',20,True).upper()
        side=text(data.get('side'),'Lado',8,True).upper()
        source=text(data.get('source') or 'MANUAL','Origen',20).upper()
        stage=text(data.get('stage') or 'MANUAL','Nivel',25,True).upper()
        venue=text(data.get('venue'),'Exchange',30,True)
        if token not in _ALLOWED_TOKENS or side not in ('BUY','SELL') or source not in CATEGORIES or not _STAGE.fullmatch(stage):
            raise WorkflowError('INVALID_ORDER','Token, lado u origen no admitido')
        if venue!=VENUES[token] or (token=='BTC' and side=='SELL'):
            raise WorkflowError('POLICY_BLOCK','Venue incorrecto o BTC NEVER SELL')
        qty=number(data.get('planned_units'),'Unidades previstas')
        amount=number(data.get('planned_usdt'),'Importe previsto')
        if (qty==0) != (amount==0):
            # A structure-only proposal may have no sizing at all, but never half-sizing.
            raise WorkflowError('INVALID_AMOUNT','Introduce unidades e importe, o deja ambos vacíos')
        return dict(venue=venue,token=token,lado=side,origen=source,tramo=stage,
                    moneda_cotizada=_QUOTES.get(token,'USDT'),unidades_previstas=qty,
                    importe_previsto=amount,estado='PROPUESTA',exchange_order_id='',
                    unidades_ejecutadas=0.,importe_ejecutado=0.,comision_token=0.,
                    comision_cotizada=0.,moneda_comision='',evidencia='',
                    observaciones=text(data.get('note'),'Nota',350),conciliacion='NO_APLICA')
    item={k:old.get(k) for k in HEADERS}
    if item['token']=='BTC' and item['lado']=='SELL':raise WorkflowError('POLICY_BLOCK','BTC NEVER SELL')
    if action=='CONFIRMADA':
        eid=text(data.get('exchange_order_id'),'ID de orden del exchange',120,True)
        if not _ID.fullmatch(eid):raise WorkflowError('INVALID_EXCHANGE_ID','ID de orden con formato inválido')
        if any(o['venue']==item['venue'] and str(o.get('exchange_order_id'))==eid
               and o['kairos_order_id']!=old['kairos_order_id'] for o in others) or (item['venue'],eid) in existing_exchange:
            raise WorkflowError('DUPLICATE_EXCHANGE_ORDER','Este ID de orden ya existe en el MASTER')
        item['exchange_order_id']=eid
        item['unidades_previstas']=number(data.get('planned_units'),'Unidades previstas',positive=True)
        item['importe_previsto']=number(data.get('planned_usdt'),'Importe previsto',positive=True)
        item['evidencia']=text(data.get('evidence'),'Evidencia de orden colocada',500,True)
        item['conciliacion']='PENDIENTE_FILL'
    elif action in ('EJECUTADA','PARCIAL'):
        if not item.get('exchange_order_id'):
            eid=text(data.get('exchange_order_id'),'ID de orden del exchange',120,True)
            if not _ID.fullmatch(eid):raise WorkflowError('INVALID_EXCHANGE_ID','Identificador de orden inválido')
            if any(o['venue']==item['venue'] and str(o.get('exchange_order_id'))==eid
                   and o['kairos_order_id']!=old['kairos_order_id'] for o in others) or (item['venue'],eid) in existing_exchange:
                raise WorkflowError('DUPLICATE_EXCHANGE_ORDER','Este ID ya está conciliado en 05_ORDENES')
            item['exchange_order_id']=eid
        inc_qty=number(data.get('executed_units'),'Unidades ejecutadas',positive=True)
        inc_usdt=number(data.get('executed_usdt'),'Importe ejecutado',positive=True)
        inc_fee_unit=number(data.get('fee_units'),'Comisión en token')
        inc_fee_quote=number(data.get('fee_quote'),'Comisión en cotizada')
        if item['lado']=='BUY' and inc_fee_unit>=inc_qty:
            raise WorkflowError('INVALID_FEE','Comisión token no puede superar lo comprado')
        if item['lado']=='SELL' and inc_fee_quote>=inc_usdt:
            raise WorkflowError('INVALID_FEE','Comisión cotizada no puede superar el ingreso')
        cum_qty=number(item.get('unidades_ejecutadas'),'Ejecutado previo')+inc_qty
        cum_usdt=number(item.get('importe_ejecutado'),'USDT previo')+inc_usdt
        pqty=number(item.get('unidades_previstas'),'Unidades previstas')
        pusdt=number(item.get('importe_previsto'),'USDT previsto')
        # Quantity must not exceed the confirmed size; never infer extra fills.
        if pqty>0 and cum_qty>pqty+1e-8:
            raise WorkflowError('OVERFILL','Las unidades superan la orden confirmada')
        if action=='EJECUTADA' and pqty>0 and cum_qty+1e-8 < pqty:
            raise WorkflowError('PARTIAL_FILL','Las unidades no alcanzan el total; usa PARCIAL')
        if action=='PARCIAL' and pqty>0 and cum_qty>=pqty-1e-8:
            raise WorkflowError('FULL_FILL','Las unidades están completas; usa EJECUTADA')
        evidence=text(data.get('evidence'),'Evidencia de ejecución',500,True)
        # Preserve cumulative history without inferring timestamp or exchange trades.
        item['unidades_ejecutadas']=cum_qty
        item['importe_ejecutado']=cum_usdt
        item['comision_token']=number(item.get('comision_token'),'Fee previa')+inc_fee_unit
        item['comision_cotizada']=number(item.get('comision_cotizada'),'Fee previa')+inc_fee_quote
        item['moneda_comision']=item['token'] if inc_fee_unit>0 else item['moneda_cotizada'] if inc_fee_quote>0 else item.get('moneda_comision','')
        # Every revision is append-only, so the event retains its own evidence.
        item['evidencia']=evidence
        item['conciliacion']='PENDIENTE_CONCILIACION'
    item['estado']=action
    item['observaciones']=text(data.get('note') or item.get('observaciones'),'Observaciones',350)
    return item


def to_sheet_row(item):
    return [item.get(k) if item.get(k) is not None else '' for k in HEADERS]


def registered_orders():
    """Read-only journal. Existing 05_ORDENES reconciled rows shown separately."""
    from kairos_sheets_features import _sheet_ids, _api
    sheetids=_sheet_ids()
    have_tab=TAB in sheetids
    ranges_arg=([('ranges',f"'{TAB}'!A1:W2000")] if have_tab else [])+[('ranges',"'05_ORDENES'!A4:P250"),('valueRenderOption','UNFORMATTED_VALUE')]
    result=_api('GET','/values:batchGet',params=ranges_arg[:-1]+[('ranges',"'06_FILLS'!A4:P250"),ranges_arg[-1]]);ranges=result.get('valueRanges') or []
    if len(ranges)!=(3 if have_tab else 2):raise WorkflowError('INCOMPLETE_READ','Datos incompletos del historial')
    events=events_from_rows(ranges[0].get('values',[])) if have_tab else []
    historical=[]
    for r in ranges[-2].get('values',[])[1:]:
        if r and len(r)>11 and str(r[11]).upper() in ('FILLED','COMPLETED'):
            historical.append({'venue':r[0], 'order_id':r[1], 'token':r[2], 'side':r[3],
                               'stage':r[5],'units':r[8], 'evidence':r[14] if len(r)>14 else ''})
    actual_receipts={(str(r[0]),str(r[1])) for r in ranges[-1].get('values',[])[1:] if len(r)>13 and str(r[13]).upper() in ('SI','TRUE','CONCILIADO','VERIFICADO')}
    reconciled={(str(h['venue']),str(h['order_id'])) for h in historical} & actual_receipts
    current=latest_orders(events)
    for rec in current:
        rec['conciliacion']=('CONCILIADA_EN_05' if rec['estado']=='EJECUTADA' and (rec['venue'],str(rec.get('exchange_order_id') or '')) in reconciled else rec['conciliacion'])
    return {'records':current,'historical':historical,'ledger_present':have_tab,
            'unreconciled':sum(r['estado'] in ('CONFIRMADA','PARCIAL','EJECUTADA') and r['conciliacion']!='CONCILIADA_EN_05' for r in current)}


def write_event(data, *, expected_snapshot_id):
    """Admin-only atomic append in 26. No changes to balances, 05 or 06."""
    from kairos_sheets_features import (_api,_sheet_ids,_sval,WRITE_LOCK)
    from google_sheets_master import get_state
    with WRITE_LOCK:
        state=get_state(force=True)
        if state['control']['snapshot_id']!=expected_snapshot_id:
            raise WorkflowError('SNAPSHOT_CONFLICT','El MASTER cambió; recarga antes de registrar')
        sheetids=_sheet_ids()
        req=[]
        if TAB not in sheetids:
            used=set(sheetids.values()); sid=2005002601
            while sid in used:sid+=1
            req.extend([{'addSheet':{'properties':{'sheetId':sid,'title':TAB,
                        'gridProperties':{'rowCount':2000,'columnCount':len(HEADERS),'frozenRowCount':1}}}},
                        {'updateCells':{'start':{'sheetId':sid,'rowIndex':0,'columnIndex':0},
                        'rows':[{'values':[_sval(x) for x in HEADERS]}], 'fields':'userEnteredValue'}}])
        else:sid=sheetids[TAB]
        if TAB in sheetids:
            response=_api('GET','/values:batchGet',params=[('ranges',f"'{TAB}'!A1:W2000"),('valueRenderOption','UNFORMATTED_VALUE')]); rows=response.get('valueRanges',[{}])[0].get('values',[])
            events=events_from_rows(rows)
        else:events=[]
        latest=latest_orders(events)
        key=text(data.get('kairos_order_id'),'ID Kairos',85)
        old=next((r for r in latest if r['kairos_order_id']==key),None) if key else None
        if old is None and str(data.get('action') or '').upper()=='PROPUESTA':key='KORD-'+uuid.uuid4().hex[:16]
        elif old is None:raise WorkflowError('UNKNOWN_ORDER','Primero registra la propuesta')
        expected_revision=data.get('expected_revision')
        if old and (str(expected_revision)!=str(old['revision'])):
            raise WorkflowError('REVISION_CONFLICT','La orden cambió; actualiza la página')
        action=str(data.get('action') or '').upper()
        existing=[]
        # These are canonical historical receipts, never import as new fills.
        ledger=_api('GET','/values:batchGet',params=[('ranges',"'05_ORDENES'!A4:P250"),('valueRenderOption','UNFORMATTED_VALUE')])
        for r in ledger.get('valueRanges',[{}])[0].get('values',[])[1:]:
            if len(r)>1 and r[0] and r[1]:existing.append((str(r[0]),str(r[1])))
        validated=validate_transition(action,data,old,latest,existing)
        now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        validated.update(event_id='KEVT-'+uuid.uuid4().hex,kairos_order_id=key,
            revision=(old['revision']+1 if old else 1),actualizado_utc=now,
            snapshot_referencia=state['control']['snapshot_id'])
        # A manual confirmation must not create an impossible cash/unit reservation
        # that would invalidate the reader on the next request. Venue-specific
        # capacity is checked against already registered open orders, not MCP Spot.
        if validated['estado'] in ('CONFIRMADA','PARCIAL','EJECUTADA'):
            venue=validated['venue'];token=validated['token'];side=validated['lado']
            reserved_qty=0.;reserved_usdt=0.
            for rec in latest:
                if old and rec['kairos_order_id']==old['kairos_order_id']:continue
                if rec['estado'] not in ('CONFIRMADA','PARCIAL','EJECUTADA'):continue
                if (rec['venue'],str(rec.get('exchange_order_id') or '')) in existing:continue
                if side=='BUY' and rec['lado']=='BUY' and rec['venue']==venue:
                    reserved_usdt+=number(rec.get('importe_previsto') or rec.get('importe_ejecutado'),'Importe reservado')
                if side=='SELL' and rec['lado']=='SELL' and rec['token']==token:
                    reserved_qty+=number(rec.get('unidades_previstas') or rec.get('unidades_ejecutadas'),'Unidades reservadas')
            if side=='BUY' and venue!='Hyperliquid':
                current_cash=float(state['snapshot']['liquidity_venues_USDT'].get(venue,0))
                this_cash=number(validated.get('importe_previsto') or validated.get('importe_ejecutado'),'Importe total')
                if reserved_usdt+this_cash>current_cash+0.01:
                    raise WorkflowError('VENUE_CAPACITY','El USDT de órdenes confirmadas supera la caja publicada en ese exchange')
            elif side=='SELL':
                bookkey='PUMPFUN' if token=='PUMP' else token
                available=state['snapshot']['custody_core_blocked__core_strategic__exchange'][bookkey][2]
                this_qty=number(validated.get('unidades_previstas') or validated.get('unidades_ejecutadas'),'Unidades total')
                from orders_inbox import TIER_SELL_FRACTIONS
                tier=state['tiers'][bookkey]
                tier_cap=state['snapshot']['holdings_total'][bookkey]*TIER_SELL_FRACTIONS[tier]
                if reserved_qty+this_qty>min(available,tier_cap)+1e-8:
                    raise WorkflowError('VENUE_CAPACITY','La venta supera Exchange libre o el máximo del Tier')
        req.append({'appendCells':{'sheetId':sid,'rows':[{'values':[_sval(x) for x in to_sheet_row(validated)]}],
                                   'fields':'userEnteredValue'}})
        _api('POST',':batchUpdate',write=True,payload={'requests':req})
        from google_sheets_master import invalidate_cache
        invalidate_cache()
        return {'status':'OK','order':validated,'notice':'Registro de gestión únicamente. No modifica inventario, saldos, 05_ORDENES ni 06_FILLS; una ejecución requiere conciliación independiente.'}
