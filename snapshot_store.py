# Persisted snapshot versions: validation and storage
import copy, hashlib, json, math, os
from datetime import datetime
from decimal import Decimal

SYMBOLS={'BTC','ETH','SOL','LINK','HYPE','HBAR','SUI','ONDO','PUMPFUN','PLUME','PEPE','VIRTUAL'}
VENUES={'Binance','KuCoin','Hyperliquid','Quantfury','MEXC','Metamask','Phantom'}

def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def _nonnegative(n,field):
    if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<0:
        raise ValueError('Valor inválido en '+field)
    return float(n)

def validate(data,baseline):
    if not isinstance(data,dict):raise ValueError('Se requiere JSON de objeto')
    required=('units_snapshot_as_of','holdings_total','custody_core_blocked__core_strategic__exchange','liquidity_venues_USDT','physical_total_USDT','trading_real_fixed_USDT')
    for k in required:
        if k not in data:raise ValueError('Falta campo '+k)
    try:datetime.fromisoformat(data['units_snapshot_as_of'].replace('Z','+00:00'))
    except (TypeError,AttributeError,ValueError):raise ValueError('Fecha de snapshot inválida')
    h=data['holdings_total'];c=data['custody_core_blocked__core_strategic__exchange'];v=data['liquidity_venues_USDT']
    if not all(isinstance(x,dict) for x in (h,c,v)) or set(h)!=SYMBOLS or set(c)!=SYMBOLS or set(v)!=VENUES:raise ValueError('Debe incluir exactamente los 12 tokens y 7 venues conocidos')
    for symbol in sorted(SYMBOLS):
        total=_nonnegative(h[symbol],symbol+' total')
        row=c[symbol]
        if not isinstance(row,list) or len(row)!=3:raise ValueError(symbol+' requiere [HODL, Core, Exchange]')
        amounts=[_nonnegative(n,symbol+' custodia') for n in row]
        # Small differences arise from screenshot rounding; large ones must block.
        if abs(sum(amounts)-total)>max(0.00001,total*0.0001):raise ValueError(symbol+' unidades no concilian con custodia')
    liquidity=sum(_nonnegative(amt,k) for k,amt in v.items())
    stated=_nonnegative(data['physical_total_USDT'],'USDT total')
    if abs(liquidity-stated)>0.02:raise ValueError('USDT total no concilia con venues')
    trading=_nonnegative(data['trading_real_fixed_USDT'],'Trading QF')
    if abs(trading-v['Quantfury'])>0.02:raise ValueError('Trading QF difiere de Quantfury')
    operating=stated-trading
    if operating<0:raise ValueError('Reserva trading excede USDT')
    # Whitelist only financial state; preserve existing provenance, ancillary policy fields.
    result=copy.deepcopy(baseline)
    for key in required:result[key]=copy.deepcopy(data[key])
    result['kairos_operating_USDT_before_commitments']=round(operating,8)
    result['custody_as_of']=data.get('custody_as_of',data['units_snapshot_as_of'])
    result['liquidity_snapshot_as_of']=data.get('liquidity_snapshot_as_of',data['units_snapshot_as_of'])
    result['provenance']='Uploaded and explicitly activated via Kairos Web, user-declared, not exchange-reconciled'
    result['status']='USER_UPLOADED_CONFIRMED_NOT_EXCHANGE_VERIFIED'
    return result

def connection():
    url=os.getenv('DATABASE_URL','').strip()
    if not url:raise RuntimeError('DATABASE_URL no configurada: carga deshabilitada')
    import psycopg
    return psycopg.connect(url,connect_timeout=8)

def initialize(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS kairos_snapshot_versions (
        id BIGSERIAL PRIMARY KEY, content JSONB NOT NULL, digest TEXT UNIQUE NOT NULL,
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), active BOOLEAN NOT NULL DEFAULT FALSE)''')
    conn.execute('CREATE INDEX IF NOT EXISTS kairos_snapshots_active ON kairos_snapshot_versions(active)')

def latest():
    with connection() as conn:
        initialize(conn)
        r=conn.execute('SELECT id, content, digest FROM kairos_snapshot_versions WHERE active=TRUE ORDER BY id DESC LIMIT 1').fetchone()
        return (r[0],r[1],r[2]) if r else None

def versions():
    with connection() as conn:
        initialize(conn)
        return [dict(id=r[0],date=r[1],recorded_at=r[2].isoformat(),active=r[3]) for r in conn.execute("SELECT id, content->>'units_snapshot_as_of', recorded_at, active FROM kairos_snapshot_versions ORDER BY id DESC LIMIT 25")]

def activate(data):
    d=digest(data)
    with connection() as conn:
        initialize(conn)
        with conn.transaction():
            conn.execute('SELECT pg_advisory_xact_lock(874128)')
            conn.execute('UPDATE kairos_snapshot_versions SET active=FALSE WHERE active=TRUE')
            row=conn.execute('''INSERT INTO kairos_snapshot_versions(content,digest,active)
            VALUES(%s::jsonb,%s,TRUE) ON CONFLICT(digest) DO UPDATE SET active=TRUE RETURNING id''',(json.dumps(data,allow_nan=False),d)).fetchone()
        return row[0],d

def restore(version_id):
    with connection() as conn:
        initialize(conn)
        with conn.transaction():
            conn.execute('SELECT pg_advisory_xact_lock(874128)')
            r=conn.execute('SELECT content FROM kairos_snapshot_versions WHERE id=%s',(version_id,)).fetchone()
            if not r:raise ValueError('Versión desconocida')
            conn.execute('UPDATE kairos_snapshot_versions SET active=FALSE WHERE active=TRUE')
            conn.execute('UPDATE kairos_snapshot_versions SET active=TRUE WHERE id=%s',(version_id,))
        return r[0]
