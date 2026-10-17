"""Shared Google Sheets features: 1H alert inbox, receipts, and controlled settings writes.

Credentials: read-only KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON (existing), and optional
separate KAIROS_GOOGLE_WRITER_JSON with Editor permission ONLY on Master.
No fallback to an embedded snapshot, SQLite inbox, or local JSON.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import os
import threading
from urllib.parse import quote

from google_sheets_master import SHEET_ID_DEFAULT, SHEETS, SheetDataError, parse_master, _remote_data

SPREADSHEET_HOST = "https://sheets.googleapis.com/v4/spreadsheets"
INBOX_SHEETS = {
    'runs': "'15_ALERTAS_RUNS'!A1:T1500",
    'events': "'16_ALERTAS_EVENTOS'!A1:U2000",
    'receipts': "'17_ALERTAS_LECTURAS'!A1:E2000",
}
WRITE_LOCK = threading.Lock()
EDITABLE_PARAM_KEYS = frozenset({
    'DRIFT_BAND_PP','STRUCTURAL_USDT_TARGET',
    'C1_BAG_FRACTION_P','C2_BAG_FRACTION_P',
    'O3_BTC_PROCEEDS_FRACTION','O3_USDT_PROCEEDS_FRACTION',
    'O5_BTC_PROCEEDS_FRACTION','O5_USDT_PROCEEDS_FRACTION',
    'O5_STAGED_TRANCHES','ORDINARY_DEFAULT_USDT_TARGET',
    'RISK_REWARD_MIN','QF_MARGIN_CAP_PER_POSITION',
    'QF_ACCOUNT_RISK_PER_TRADE','QF_ACCOUNT_RISK_TOTAL',
    'MAX_LEVERAGE','MAX_OPEN_POSITIONS',
    'TRIGGER_STRICT_GT','PROXIMITY_BAND',
})
VALID_CATEGORIES = frozenset(('units','targets','tier_custody','liquidity','parameters','pivots'))


class SettingsError(ValueError):
    pass


def _id():
    value=os.getenv('KAIROS_GOOGLE_SHEET_ID',SHEET_ID_DEFAULT).strip()
    if not value or not all(ch.isalnum() or ch in '-_' for ch in value):
        raise SettingsError('KAIROS_GOOGLE_SHEET_ID incorrecto')
    return value


def _session(write=False):
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    if write:
        raw=os.getenv('KAIROS_GOOGLE_WRITER_JSON','').strip()
        if not raw:
            raise SettingsError('WRITE_DISABLED: falta configurar KAIROS_GOOGLE_WRITER_JSON en Render')
        scope='https://www.googleapis.com/auth/spreadsheets'
    else:
        raw=os.getenv('KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON','').strip()
        if not raw:
            raise SettingsError('READ_DISABLED: falta KAIROS_GOOGLE_SERVICE_ACCOUNT_JSON')
        scope='https://www.googleapis.com/auth/spreadsheets.readonly'
    try:
        credentials=service_account.Credentials.from_service_account_info(json.loads(raw),scopes=[scope])
    except (ValueError,KeyError,TypeError) as exc:
        raise SettingsError('Credenciales Google no válidas') from exc
    return AuthorizedSession(credentials)


def _api(method, suffix, *, write=False, params=None, payload=None):
    session=_session(write=write)
    try:
        r=session.request(method, f'{SPREADSHEET_HOST}/{quote(_id(),safe="")}{suffix}',
                          params=params,json=payload,timeout=25)
        if r.status_code>=400:
            raise SettingsError('Google Sheets HTTP '+str(r.status_code))
        return r.json()
    finally:
        session.close()


def read_ranges(ranges):
    """Read source records using read-only service identity; no cached fallback."""
    response=_api('GET','/values:batchGet',params=[('ranges',x) for x in ranges.values()]+[('valueRenderOption','UNFORMATTED_VALUE')])
    vr=response.get('valueRanges') or []
    if len(vr)!=len(ranges):raise SettingsError('Google Sheets devolvió rangos incompletos')
    return {k:vr[i].get('values',[]) for i,k in enumerate(ranges)}


def _header_records(rows):
    if not rows:return []
    keys=[str(x).strip() for x in rows[0]]
    return [{k:(r[i] if i<len(r) else None) for i,k in enumerate(keys) if k} for r in rows[1:] if r and r[0]]


# Notification visibility is stricter than the archival KairosGPT event ledger.
# Never turn WATCH, PRECONFIRMADO or provisional BSI/TradingBot signals into orders.
_ACTIONABLE_STATES = frozenset(('READY','ACCIONABLE','CERTIFICADA','VALIDADA','APROBADA','LISTA_PARA_REVISION'))
_APPROVED_CERT = frozenset(('CERTIFICADA','CERTIFICADO','VALIDADA','VERIFICADA','APROBADA'))
_FORBIDDEN_ACTION = ('NO ORDEN','SIN CAJA','NO ELEGIBLE','NO VERIFICADO','NO CERTIFICAD',
                     'SEGUIMIENTO','ESPERAR DATOS','SIN PRESUPUESTO','PENDIENTE CERTIFIC')


def alert_category(event, *, bsi_enabled=False):
    """Fail-closed interpretation of explicitly certified actions only.

    Return a category or None. The ledger has separate fields for action type,
    state, certification, level and budget: all required constraints are checked.
    Even a text saying BUY cannot promote a noncertified event.
    """
    state=str(event.get('estado_evento') or '').upper().strip()
    kind=str(event.get('tipo_alerta') or '').upper().strip()
    cert=str(event.get('certificacion') or '').upper().strip()
    action=str(event.get('accion_sugerida') or '').upper().strip()
    if state not in _ACTIONABLE_STATES or not action or any(t in action for t in _FORBIDDEN_ACTION):
        return None
    try:
        level=float(event.get('nivel_usdt') or 0)
        budget=float(event.get('usdt_preparar') or 0)
        if not(math.isfinite(level) and math.isfinite(budget) and level>=0 and budget>=0):return None
    except (ValueError,TypeError):return None
    if kind.startswith('BSI_') or kind in ('BSI_SELL','VENTA_BSI'):
        if not bsi_enabled or cert not in _APPROVED_CERT or level<=0 or not any(t in action for t in ('VENDER','VENTA','SELL')):
            return None
        return 'BSI SELL'
    if kind.startswith('TRADINGBOT_'):
        if cert not in ('CERTIFICADA_QF','VERIFICADA_QF','READY_QF') or level<=0 or not all(t in action for t in ('SL','TP')):
            return None
        return 'TRADINGBOT READY'
    if cert not in _APPROVED_CERT:return None
    if kind in ('PREPARAR_LIQUIDEZ','LIQUIDEZ_PREPARAR','RESERVAR_USDT'):
        return 'PREPARAR LIQUIDEZ' if budget>0 and level>0 and any(t in action for t in ('PREPARAR','RESERVAR')) else None
    if kind=='COMPRA' or kind.startswith('COMPRA_') or kind=='BUY_READY':
        return 'COMPRA' if level>0 and budget>0 and any(t in action for t in ('COMPRA','COMPRAR','BUY','LIMIT')) else None
    if kind=='VENTA' or kind.startswith('VENTA_') or kind=='SELL_READY':
        return 'VENTA' if level>0 and any(t in action for t in ('VENDER','VENTA','SELL')) and any(ch.isdigit() for ch in action) else None
    return None


def alert_inbox(blocks, limit=150, *, bsi_enabled=False):
    """ONLY certified 1H actions; unread + deduplicated by material instruction.

    Historical WATCH/PRECONFIRMADO are preserved by GPT but never visible here.
    Mark-all acts on this same filtered set, not on unshown historical WATCH.
    """
    runs={r.get('corrida_id'):r for r in _header_records(blocks['runs']) if str(r.get('marco','')).upper()=='1H'}
    seen={str(r.get('evento_id','')) for r in _header_records(blocks['receipts']) if r.get('leido_utc')}
    gathered=[]
    for x in _header_records(blocks['events']):
        eid=str(x.get('evento_id') or '')
        if not eid or x.get('corrida_id') not in runs:continue
        category=alert_category(x,bsi_enabled=bsi_enabled)
        if category is None:continue
        try:dt=datetime.fromisoformat(str(x['creado_utc']).replace('Z','+00:00'))
        except (KeyError,ValueError,TypeError):continue
        if dt.tzinfo is None:continue
        token=str(x.get('token') or '').strip()
        action=str(x.get('accion_sugerida') or '').strip()
        if not token:continue
        key=(category,token,action.upper().strip(),str(x.get('nivel_usdt') or ''),str(x.get('usdt_preparar') or ''))
        gathered.append((key, {'id':eid,'token':token,'created_utc':dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                       'action':action,'state':str(x.get('estado_evento')),
                       'certification':str(x.get('certificacion')),'category':category,
                       'kind':str(x.get('tipo_alerta') or ''),'timeframe':str(x.get('marco') or '1H'),
                       'spot_usdt':x.get('spot_usdt'),'level_usdt':x.get('nivel_usdt'),
                       'usdt_prepare':x.get('usdt_preparar'), 'run_id':str(x.get('corrida_id') or ''),
                       'source':'KAIROSGPT_GOOGLE_SHEETS','is_trade_ready':category=='TRADINGBOT READY'}))
    gathered.sort(key=lambda x:(x[1]['created_utc'],x[1]['id']),reverse=True)
    records=[];dedupe=set()
    for key, record in gathered:
        if key in dedupe:continue
        dedupe.add(key)
        # A newer read signal suppresses stale unreads with the same action.
        if record['id'] in seen:continue
        records.append(record)
    return {'status':'OK','source':'KAIROSGPT_GOOGLE_SHEETS','scope':'UNREAD_ACTIONABLE_1H_ONLY',
            'unread_count':len(records),'records':records[:limit] if limit is not None else records,
            'limited':limit is not None and len(records)>limit}


def _bsi_selling_approved():
    """BSI SELL is gated by BOTH approved policies and 12/12 reconciled data.

    A policy flag alone cannot certify legacy anchors or unmonetized HWM.
    The full 4H baseline UTC must be aligned for all twelve instruments.
    """
    try:
        blocks=read_ranges({
          'parameters':"'12_PARAMETROS_KAIROS'!A4:J180",
          'bsi':"'09_BSI'!A4:K16",
        })
        rows=blocks['parameters']
        pairs={str(r[1]):str(r[5]) for r in rows[1:] if len(r)>5 and r[1] in ('BASELINE_STATUS','HISTORICAL_ANCHOR_MIGRATION')}
        if len(pairs)!=2 or not all(v=='APROBADO' for v in pairs.values()):return False
        bsi=blocks['bsi']
        if len(bsi)!=13:return False
        dates=set();tokens=set()
        for row in bsi[1:]:
            if len(row)<10 or not row[0] or row[5] in (None,'') or row[6] in (None,'') or row[7] in (None,''):
                return False
            if str(row[9]).upper() not in ('CERTIFICADO','OPERATIVO_CERTIFICADO','HOMOLOGADO'):
                return False
            if not math.isfinite(float(row[5])) or not math.isfinite(float(row[7])):
                return False
            dates.add(str(row[6]));tokens.add(str(row[0]))
        return len(dates)==1 and len(tokens)==12 and len(bsi)==13
    except Exception:
        return False

def unread_alerts():
    result=alert_inbox(read_ranges(INBOX_SHEETS),bsi_enabled=_bsi_selling_approved())
    result['can_mark_read']=bool(os.getenv('KAIROS_GOOGLE_WRITER_JSON'))
    return result


def mark_alert_read(event_id):
    if not isinstance(event_id,str) or not event_id or len(event_id)>180:
        raise SettingsError('evento_id no válido')
    with WRITE_LOCK:
        blocks=read_ranges(INBOX_SHEETS)
        run_ids={r.get('corrida_id') for r in _header_records(blocks['runs']) if str(r.get('marco','')).upper()=='1H'}
        event_ids={str(x.get('evento_id')) for x in _header_records(blocks['events']) if x.get('corrida_id') in run_ids}
        if event_id not in event_ids:raise SettingsError('Evento 1H no encontrado')
        existing={str(x.get('evento_id')) for x in _header_records(blocks['receipts'])}
        if event_id in existing:return {'status':'OK','already_read':True}
        now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        # Append-only receipt; one event ID per notification. Account-wide read status.
        sheet_ids=_sheet_ids()
        request={'appendCells':{'sheetId':sheet_ids['17_ALERTAS_LECTURAS'],
                                'rows':[{'values':[{'userEnteredValue':{'stringValue':v}} for v in [event_id,now,'KairosWeb','LEIDO','1H']]}],
                                'fields':'userEnteredValue'}}
        _api('POST',':batchUpdate',write=True,payload={'requests':[request]})
        return {'status':'OK','id':event_id,'read_utc':now}



def mark_all_alerts_read():
    """One idempotent receipt batch for all historical unread 1H events, never 4H."""
    with WRITE_LOCK:
        blocks=read_ranges(INBOX_SHEETS)
        unread=alert_inbox(blocks,limit=None,bsi_enabled=_bsi_selling_approved())['records']
        if not unread:
            return {'status':'OK','marked':0,'already_read':True}
        if len(unread)>1800:
            raise SettingsError('Demasiados eventos; revisar el rango histórico antes de confirmar lectura')
        now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        sheet_ids=_sheet_ids()
        if '17_ALERTAS_LECTURAS' not in sheet_ids:raise SettingsError('Falta hoja de lecturas')
        rows=[]
        for e in unread:
            row=[e['id'],now,'KairosWeb','LEIDO','1H']
            rows.append({'values':[{'userEnteredValue':{'stringValue':v}} for v in row]})
        _api('POST',':batchUpdate',write=True,payload={'requests':[{'appendCells':{
            'sheetId':sheet_ids['17_ALERTAS_LECTURAS'],'rows':rows,'fields':'userEnteredValue'}}]})
        return {'status':'OK','marked':len(rows),'read_utc':now}

def _sheet_ids():
    response=_api('GET','',params={'fields':'sheets(properties(sheetId,title))'})
    return {s['properties']['title']:s['properties']['sheetId'] for s in response.get('sheets',[]) if s.get('properties')}


def _numeric(value, label):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise SettingsError(f'{label}: ingresar un número >= 0')
    return float(value)


def _a1num(v):
    if v==int(v):return int(v)
    return v


def _set(blocks,name,row,col,value):
    k=SHEETS[name];rows=blocks[k]
    while len(rows)<=row:rows.append([])
    while len(rows[row])<=col:rows[row].append(None)
    rows[row][col]=value


def _find_row(blocks,name,key,*,column=0):
    for index,row in enumerate(blocks[SHEETS[name]]):
        if len(row)>column and row[column]==key:return index
    raise SettingsError(f'{name}: fila {key} no encontrada')


def _get(blocks,name,row,col):
    a=blocks[SHEETS[name]]
    return a[row][col] if len(a)>row and len(a[row])>col else None


def _sval(value):
    if value is None:return {}
    if type(value)==bool:return {'userEnteredValue':{'boolValue':value}}
    if type(value) in (int,float):return {'userEnteredValue':{'numberValue':value}}
    return {'userEnteredValue':{'stringValue':str(value)}}


def _ensure_one(value, prefix):
    if not isinstance(value,list) or not value or len(value)>36 or any(not isinstance(r,dict) for r in value):
        raise SettingsError(f'{prefix}: cambios inválidos o demasiados')


def prepare_changes(raw, category, entries, *, evidence, as_of_date=None):
    """Preview against complete source copy, then return address/value writes.
    User cannot send arbitrary A1 ranges or mark a pivot certified.
    """
    if category not in VALID_CATEGORIES:raise SettingsError('Sección no permitida')
    _ensure_one(entries,category)
    if not isinstance(evidence,str) or len(evidence.strip())<8 or len(evidence)>400:
        raise SettingsError('Se requiere justificación/evidencia de al menos 8 caracteres')
    if as_of_date is not None:
        try:datetime.strptime(as_of_date,'%Y-%m-%d')
        except (ValueError,TypeError):raise SettingsError('fecha de corte YYYY-MM-DD inválida')
    if category in ('units','liquidity') and not as_of_date:
        raise SettingsError('Las actualizaciones de unidades o liquidez requieren fecha de corte')
    b=deepcopy(raw)
    updates=[]
    seen=set()
    def change(name,row,col,value):
        k=(name,row,col)
        if k in seen:raise SettingsError('Campo duplicado')
        seen.add(k);_set(b,name,row,col,value);updates.append((name,row,col,value))
    positions={r[0]:i for i,r in enumerate(b[SHEETS['positions']]) if r and r[0] in ('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE')}
    if category in ('units','targets','pivots'):
        for x in entries:
            token=x.get('token')
            if token not in positions:raise SettingsError('Token no permitido')
            row=positions[token]
            if category=='units':
                vals=[_numeric(x.get(k),k) for k in ('hodl','core','exchange','investment_total')]
                units=sum(vals[:3]);cost=vals[3]
                if units<=0:raise SettingsError('No puede quedar un activo con unidades totales cero; conservar integridad de costo medio')
                for col,val in [(4,vals[0]),(5,vals[1]),(6,vals[2]),(9,cost),(13,units),(10,as_of_date),(11,'KairosWeb Settings · '+evidence.strip()[:95])]:
                    change('positions',row,col,val)
                # For the preview only: formulas recompute asynchronously in Sheets.
                _set(b,'positions',row,7,units);_set(b,'positions',row,8,cost/units if units else 0);_set(b,'positions',row,12,'OK')
            elif category=='targets':
                tier=x.get('tier');target=_numeric(x.get('target'), 'target')
                if tier not in ('T1','T2','T3') or target>1:raise SettingsError('Tier o target inválido')
                change('positions',row,2,tier);change('positions',row,3,target)
            else:
                for field,col in [('cycle_low',1),('o1',3),('o2',5),('o3',7),('o4',8),('o5',9),('c1_reference',11),('c2_reference',12)]:
                    if field in x and x[field] is not None:
                        change('pivots',_find_row(b,'pivots',token),col,_numeric(x[field],field))
                prow=_find_row(b,'pivots',token)
                change('pivots',prow,14,'PENDIENTE_CERTIFICACION')
                change('pivots',prow,15,'KairosWeb Settings · EVIDENCIA NO CERTIFICADA: '+evidence.strip()[:90])
    elif category=='tier_custody':
        for x in entries:
            tier=x.get('tier')
            if tier not in ('T1','T2','T3'):raise SettingsError('Tier inválido')
            row=_find_row(b,'custody',tier)
            a=[_numeric(x.get(k),k) for k in ('hodl','core','exchange')]
            if abs(sum(a)-1)>1e-8:raise SettingsError(tier+': custodia debe sumar 100%')
            for c,val in zip((1,2,3),a):change('custody',row,c,val)
    elif category=='liquidity':
        for x in entries:
            venue=x.get('venue');row=_find_row(b,'liquidity',venue)
            if _get(b,'liquidity',row,2) not in ('OPERATIVO','TRADING_QF'):
                raise SettingsError('Venue no permitido')
            change('liquidity',row,1,_numeric(x.get('usdt'),'USDT'))
            change('liquidity',row,3,as_of_date)
            change('liquidity',row,4,'KairosWeb Settings · '+evidence.strip()[:90])
    elif category=='parameters':
        for x in entries:
            key=x.get('key')
            if key not in EDITABLE_PARAM_KEYS:raise SettingsError('Parámetro protegido o no implementado: '+str(key))
            row=_find_row(b,'parameters',key,column=1)
            old=_get(b,'parameters',row,2);ptype=_get(b,'parameters',row,3)
            if _get(b,'parameters',row,5) not in ('APROBADO','APROBADO_CONDICIONAL'):
                raise SettingsError('Parámetro no aprobado')
            value=x.get('value')
            if ptype in ('number','integer'):
                value=_numeric(value,key)
                if ptype=='integer':
                    if not value.is_integer():raise SettingsError(key+': entero requerido')
                    value=int(value)
                if 'FRACTION' in key or key.endswith('_TARGET') or key.endswith('_BAND') or key=='PROXIMITY_BAND':
                    if value>1:raise SettingsError(key+': debe estar entre 0 y 1')
            elif key=='O5_STAGED_TRANCHES':
                if not isinstance(value,str):raise SettingsError('Tramos deben ser texto coma-separado')
                try:tranches=[int(x.strip()) for x in value.split(',')]
                except ValueError:raise SettingsError('Tramos inválidos')
                if len(tranches)!=4 or any(x<0 for x in tranches) or sum(tranches)!=100:raise SettingsError('4 tramos deben sumar 100')
                value=','.join(str(x) for x in tranches)
            else:raise SettingsError('Tipo de parámetro no editable')
            change('parameters',row,2,value)
            change('parameters',row,7,'Aprobación administrativa KairosWeb · '+evidence.strip()[:95])
    # Repair derived preview fields without modifying the Google Sheets formulas.
    if category=='liquidity':
        rows=b[SHEETS['liquidity']]
        venue=[r for r in rows[1:] if len(r)>2 and r[2] in ('OPERATIVO','TRADING_QF')]
        liq=sum(r[1] for r in venue);qf=sum(r[1] for r in venue if r[2]=='TRADING_QF')
        for key,val in [('TOTAL LIQUIDEZ',liq),('RESERVA TRADING QF',qf),('USDT OPERATIVO',liq-qf),('Total informado por usuario',liq),('Diferencia de conciliación',0)]:
            row=_find_row(b,'liquidity',key);_set(b,'liquidity',row,1,val)
        change('liquidity',_find_row(b,'liquidity','Total informado por usuario'),1,liq)
    if category in ('units','liquidity'):
        change('control',_find_row(b,'control','fecha_corte'),1,as_of_date)
        if category=='units':
            cost=sum(float(r[9]) for r in b[SHEETS['positions']][1:] if r and r[0] in positions)
            _set(b,'control',_find_row(b,'control','Costo abierto cripto'),1,cost)
        if category=='liquidity':
            liq=float(_get(b,'liquidity',_find_row(b,'liquidity','TOTAL LIQUIDEZ'),1))
            for n,v in [('Liquidez física',liq),('Reserva QF',qf),('USDT operativo',liq-qf)]:_set(b,'control',_find_row(b,'control',n),1,v)
    if category in ('units','liquidity'):
        _set(b,'control',_find_row(b,'control','Capital contable estimado'),1,
             _get(b,'control',_find_row(b,'control','Costo abierto cripto'),1)+_get(b,'control',_find_row(b,'control','Liquidez física'),1))
    if category=='parameters':
        pm={r[1]:r[2] for r in b[SHEETS['parameters']][1:] if len(r)>2 and r[1]}
        for base in ('O5','O3'):
            if abs(float(pm[f'{base}_BTC_PROCEEDS_FRACTION'])+float(pm[f'{base}_USDT_PROCEEDS_FRACTION'])-1)>1e-9:
                raise SettingsError(base+': BTC + USDT debe sumar 100%')
        if float(pm['C1_BAG_FRACTION_P'])+float(pm['C2_BAG_FRACTION_P'])>1:
            raise SettingsError('Presupuesto C1+C2 supera 100% del patrimonio')
    # Update parameter parse_master O5 policy contract handled by validator.
    try:state=parse_master(b)
    except SheetDataError as exc:raise SettingsError('Validación del Master falló: '+str(exc)) from exc
    return updates, state


def settings_data():
    raw=_remote_data();state=parse_master(raw)
    def rows(name):return raw[SHEETS[name]]
    positions=[{'token':r[0],'tier':r[2],'target':r[3],'hodl':r[4],
                'core':r[5],'exchange':r[6],'investment_total':r[9],'total_units':r[7], 'average_cost':r[8]} for r in rows('positions')[1:] if r and r[0] in state['tokens']]
    liquidity=[{'venue':r[0],'usdt':r[1],'classification':r[2]} for r in rows('liquidity')[1:] if len(r)>2 and r[2] in ('OPERATIVO','TRADING_QF')]
    custody=[{'tier':r[0],'hodl':r[1],'core':r[2],'exchange':r[3]} for r in rows('custody')[1:] if r and r[0] in ('T1','T2','T3')]
    params=[{'key':r[1],'module':r[0],'value':r[2],'unit':r[4], 'type':r[3], 'status':r[5], 'module_name':r[0], 'description':r[8] if len(r)>8 else '', 'source':r[7] if len(r)>7 else ''} for r in rows('parameters')[1:] if len(r)>5 and r[1] in EDITABLE_PARAM_KEYS]
    pivots=[{'token':r[0],'cycle_low':r[1] if len(r)>1 else None,
             'o1':r[3] if len(r)>3 else None,'o2':r[5] if len(r)>5 else None,
             'o3':r[7] if len(r)>7 else None,'o4':r[8] if len(r)>8 else None,'o5':r[9] if len(r)>9 else None,
             'c1_reference':r[11] if len(r)>11 else None,'c2_reference':r[12] if len(r)>12 else None,
             'status':r[14] if len(r)>14 else None}
             for r in rows('pivots')[1:] if r and r[0] in state['tokens']]
    return {'status':'OK','snapshot_id':state['control']['snapshot_id'], 'fecha_corte':state['control']['fecha_corte'],
            'schema_version':'5.0.0','write_configured':bool(os.getenv('KAIROS_GOOGLE_WRITER_JSON')),
            'sections':{'units':positions,'targets':positions,'tier_custody':custody,'liquidity':liquidity,'parameters':params,'pivots':pivots},
            'blocked':{'BSI_SELL':'No homologado','TRADINGBOT':'WATCH', 'PIVOTS':'Certificación manual pendiente'}}


def save_changes(data):
    """One atomic Sheets batch. Preview again under lock, reject stale snapshot ID."""
    expected=data.get('expected_snapshot_id');category=data.get('section');entries=data.get('entries')
    evidence=data.get('evidence');as_of_date=(datetime.now(timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('America/Lima')).date().isoformat() if category in ('units','liquidity') else None)
    with WRITE_LOCK:
        raw=_remote_data();current=parse_master(raw)
        if expected!=current['control']['snapshot_id']:
            raise SettingsError('CONFLICTO: snapshot cambió desde la carga del formulario; recarga Configuración')
        writes,newstate=prepare_changes(raw,category,entries,evidence=evidence,as_of_date=as_of_date)
        now=datetime.now(timezone.utc)
        if not writes:raise SettingsError('No hay cambios')
        new_snapshot='KAIROS-'+now.strftime('%Y%m%dT%H%M%SZ')+'-WEB'
        oldid=current['control']['snapshot_id']
        sheetids=_sheet_ids()
        needed={SHEETS[k].split('!')[0].strip("'") for k,_,_,_ in writes}
        needed.update(('01_CONTROL','10_HISTORIAL','18_SETTINGS_AUDITORIA'))
        if not needed.issubset(sheetids):raise SettingsError('Falta una pestaña obligatoria')
        requests=[]
        audit_entries=[]
        for name,row,col,value in writes:
            previous=_get(raw,name,row,col)
            audit_entries.append([new_snapshot,now.isoformat().replace('+00:00','Z'),category,
                                  SHEETS[name].split('!')[0].strip("'"),str(row+4),str(col+1),
                                  str(previous) if previous is not None else '',str(value),str(evidence).strip()[:250]])
        for name,row,col,value in writes:
            tab=SHEETS[name].split('!')[0].strip("'")
            requests.append({'updateCells':{'start':{'sheetId':sheetids[tab],'rowIndex':row+3,'columnIndex':col},
                                            'rows':[{'values':[_sval(value)]}], 'fields':'userEnteredValue'}})
        def ctrl(key,value):
            i=_find_row(raw,'control',key)
            requests.append({'updateCells':{'start':{'sheetId':sheetids['01_CONTROL'],'rowIndex':i+3,'columnIndex':1},
                                            'rows':[{'values':[_sval(value)]}], 'fields':'userEnteredValue'}})
        ctrl('snapshot_id',new_snapshot)
        ctrl('publicado_utc',now.isoformat().replace('+00:00','Z'))
        ctrl('estado_publicacion','PUBLICADO')
        ctrl('aprobado_por','KairosWeb · autenticación administrativa')
        ctrl('reemplaza_snapshot',oldid)
        ctrl('origen','KairosWeb Settings / '+category)
        ctrl('comentario',str(evidence).strip()[:250])
        # Versioned history: write new entry. Source current counter state is not mutated.
        snapshot_row=[new_snapshot,newstate['control']['fecha_corte'],now.isoformat().replace('+00:00','Z'),
                      'PUBLICADO',12,newstate['snapshot']['physical_total_USDT'],
                      None,
                      'KairosWeb Settings / '+category,oldid,str(evidence).strip()[:250]]
        # Compute declared cost from the validated 02_POSICIONES buffer.
        cost=sum(newstate['snapshot']['holdings_total'][t]*newstate['cost_basis']['PUMP' if t=='PUMPFUN' else t] for t in newstate['tokens'])
        snapshot_row[6]=cost
        requests.append({'appendCells':{'sheetId':sheetids['10_HISTORIAL'],
                         'rows':[{'values':[_sval(v) for v in snapshot_row]}], 'fields':'userEnteredValue'}})
        requests.append({'appendCells':{'sheetId':sheetids['18_SETTINGS_AUDITORIA'],
                         'rows':[{'values':[_sval(v) for v in record]} for record in audit_entries],
                         'fields':'userEnteredValue'}})
        _api('POST',':batchUpdate',write=True,payload={'requests':requests})
        from google_sheets_master import invalidate_cache, get_state
        invalidate_cache()
        # Publication is not claimed successful until the canonical reader validates it.
        verified=get_state(force=True)
        if verified['control']['snapshot_id']!=new_snapshot:
            raise SettingsError('Publicación enviada pero nueva versión NO verificada; revisar Google Sheets')
        return {'status':'OK','snapshot_id':new_snapshot,'previous_snapshot_id':oldid,'section':category,
                'written_fields':len(writes),'published_utc':snapshot_row[2],
                'warning':'Cambios publicados; datos externos/fills no inferidos. Revisar nueva conciliación del snapshot.'}
