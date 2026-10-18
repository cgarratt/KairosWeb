from structural_outliers import virtual_flash_cl
from pivot_candidates import candidates_binance
from pivot_preload import archive_candidates, TOKENS
from wave_macro_context import resolve, resolve_long_term_buy


def test_flash_week_excluded_but_recent_low_not_excluded():
    assert virtual_flash_cl(0.2772,'2025-10-10')
    assert virtual_flash_cl(0.5,'2025-10-06')
    assert not virtual_flash_cl(0.6291,'2025-12-19')


def test_archive_virtual_raw_cl_not_selected():
    rows=[['Token','Mercado fuente','CH bruto']]
    v=['VIRTUAL','Binance VIRTUAL/USDT','2.589','2025-05-27','0.2772','2025-10-10','1.1984','2026-01-05']
    rows.append(v)
    record=next(x for x in archive_candidates(rows) if x['token']=='VIRTUAL')
    assert record['raw_cycle_low']==0.2772
    assert record['cycle_low'] is None and record['cl_date'] is None
    assert 'excluida' in record['warning']


def test_live_mcp_virtual_is_not_an_approved_cl():
    m={'status':'OK','scope':'EXPLORATORY_ONLY','cycle_low':{'price':'0.2772','date_utc':'2025-10-10'},'cycle_high':{'price':'2.589','date_utc':'2025-05-27'},'wave_pivots':{}}
    x=candidates_binance('VIRTUAL',m)
    assert x['raw_cycle_low']==0.2772
    assert x['cycle_low'] is None and x['cl_date'] is None


def test_published_virtual_flash_cl_is_never_silently_used():
    p={'cycle_low':.2772,'cl_date':'2025-10-10','cl_status':'PROPUESTO','waves':{'o1':{'price':1.1984,'date':'2026-01-05','status':'PROPUESTO'}}}
    data={'status':'OK','source':'Binance Spot','interval':'1d','closed_only':True,'records':[]}
    assert resolve('VIRTUAL',p,{},data)['status']=='VIRTUAL_FLASH_CL_EXCLUDED'
    assert resolve_long_term_buy('VIRTUAL',p,data)['reason']=='VIRTUAL_CL_FLASH_EXCLUIDO_REQUIERE_REVISION'
