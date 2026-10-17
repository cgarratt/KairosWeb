"""Read-only preliminary pivot archive adapter. Values are NOT certified Elliott anchors.

Source: 07_PIVOTES rows 21-33, an MCP exploratory archive stored in Google Sheets.
Never infer an approved pivot or a filled order from this archive.
"""
from __future__ import annotations

from math import isfinite

TOKENS = ('BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','VIRTUAL','PEPE')
ARCHIVE_A1 = "'07_PIVOTES'!A21:Q33"


def _num(value):
    try:
        x = float(value)
        return x if isfinite(x) and x >= 0 else None
    except (ValueError, TypeError):
        return None


def archive_candidates(rows, params=None):
    """Convert historical MCP records to review-only frontend rows.

    Header and source metadata must be valid; do not invent missing values.
    SUI/PUMP rejected 2025-10-10 flash outliers are excluded.
    """
    params = params or {}
    if not rows or rows[0][:3] != ['Token','Mercado fuente','CH bruto']:
        raise ValueError('Archivo histórico MCP de pivotes no coincide con esquema esperado')
    result = {}
    for r in rows[1:]:
        if not r or r[0] not in TOKENS:
            continue
        token = r[0]
        if token in result:
            raise ValueError('Token duplicado en archivo de pivotes')
        def get(i):return r[i] if len(r)>i else None
        raw_low = _num(get(4))
        selected = _num(get(13))
        low = selected if token in ('SUI','PUMPFUN') and selected is not None else raw_low
        if token=='SUI' and raw_low is not None and abs(raw_low-.5597)<1e-7 and selected is None:
            low=None
        if token=='PUMPFUN' and raw_low is not None and abs(raw_low-.000411)<1e-8 and selected is None:
            low=None
        high = _num(get(2))
        o1,o2,o3 = _num(get(6)),_num(get(8)),_num(get(10))
        details = str(get(16) or '').strip()
        warnings = [details] if details else []
        if token in ('SUI','PUMPFUN') and selected is not None:
            warnings.insert(0, 'CL ajustado de política; fecha del mínimo bruto NO aplica al CL seleccionado')
        if token=='HYPE' and o3 is not None:
            warnings.insert(0, 'O3 es máximo observado sin 5R; NO es pivote confirmado')
        if not any(x is not None for x in (high,low,o1,o2,o3)):
            warnings.append('Sin niveles suficientes en archivo MCP')
        result[token] = {
            'token':token, 'market':str(get(1) or ''),
            'source':'HISTORICO_MCP_EN_GOOGLE_SHEETS', 'record_origin':'07_PIVOTES A21:Q33',
            'status':'CANDIDATO_ARCHIVADO_NO_CERTIFICADO', 'certified':False,
            'cycle_high':high,'ch_date':get(3) or None,
            'cycle_low':low,'cl_date':None if selected is not None and token in ('SUI','PUMPFUN') else get(5) or None,
            'raw_cycle_low':raw_low,
            'o1':o1,'o1_date':get(7) or None,
            'o2':o2,'o2_date':get(9) or None,
            'o3':o3, 'o3_date':get(11) or None,
            'o4':None,'o5':None,
            'o3_unconfirmed_high':o3 if token=='HYPE' else None,
            'phase_candidate':str(get(12) or ''),
            'warning':'; '.join(warnings),
            'method':'MCP histórico archivado; no confirma BOS/Elliott ni señales operativas'
        }
    return [result.get(t, {'token':t,'status':'DATA_ERROR','certified':False,
                           'warning':'No existe evidencia histórica MCP para este token',
                           'source':'GOOGLE_SHEETS'}) for t in TOKENS]


def review_result(record, source='LIVE_MCP'):
    """Convert live server scanner output to explicit non-actionable status."""
    if not isinstance(record,dict) or record.get('token') not in TOKENS:
        raise ValueError('Registro MCP no reconocido')
    item=dict(record)
    item['certified']=False
    if item.get('status') not in ('DATA_ERROR',):
        item['status']='CANDIDATO_MCP_NO_CERTIFICADO'
    item['record_origin']=source
    return item
