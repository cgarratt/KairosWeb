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

# Regression: the 19-Oct-2026 published VIRTUAL Elliott structure supersedes
# the excluded 2025-10-10 flash CL, without rewriting historical MCP archives.
def test_new_published_virtual_o2_selects_weekly_impulse_not_2025_flash():
    from datetime import date, timedelta
    from pytest import approx
    start=date(2026,6,22); end=date(2026,10,18)
    candles=[]
    for n in range((end-start).days+1):
        d=start+timedelta(days=n)
        lo=.4977 if d==date(2026,6,25) else .62
        hi=.8861 if d==date(2026,10,5) else .8
        candles.append({'open_utc':d.isoformat()+'T00:00:00+00:00',
            'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
            'high':str(hi),'low':str(lo),'close':'.7'})
    published={'cycle_low':.4593,'cl_date':'2026-02-06','cl_status':'PROPUESTO',
        'waves':{'o1':{'price':.9783,'date':'2026-05-07','status':'PROPUESTO'},
                 'o2':{'price':.4977,'date':'2026-06-25','status':'PROPUESTO'}}}
    data={'status':'OK','source':'Binance Spot','interval':'1d','closed_only':True,'records':candles}
    result=resolve_long_term_buy('VIRTUAL',published,data,archived={'cycle_low':.2772,'cl_date':'2025-10-10'})
    assert result['eligible'], result
    assert result['anchors']['low']['price']==approx(.4977)
    assert result['anchors']['low']['pivot']=='O2'
    assert result['anchors']['high']['price']==approx(.8861)
    assert result['reason']=='P1_ADMITIDO_P2_MAXIMO_SEMANAL_POSTERIOR'
    assert result['operational_blocked'] is True
