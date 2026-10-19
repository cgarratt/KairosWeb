import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hype_weekly import aggregate_weeks,HypeHistoryError

def days(n=7):
    a=datetime(2026,10,5,tzinfo=timezone.utc)
    return {'status':'OK','source':'Hyperliquid Spot','pair':'HYPE/USDC','interval':'1d','closed_only':True,
            'records':[{'open_utc':(a+timedelta(days=i)).isoformat(),'close_utc':(a+timedelta(days=i+1)).isoformat(),
                        'open':'100','high':str(101+i),'low':'99','close':'100','volume_base':'15'} for i in range(n)]}
class MacroWeeks(unittest.TestCase):
    def test_mon_sun_utc_full_week(self):
        a=aggregate_weeks(days())
        self.assertEqual(a['full_weeks'],1)
        self.assertEqual(a['weeks'][0]['high'],107)
        self.assertEqual(a['weeks'][0]['volume_base'],105)
        self.assertEqual(a['approved_elliott_pivots'],False)
    def test_no_partial_week(self):
        with self.assertRaises(HypeHistoryError):aggregate_weeks(days(6))
    def test_wrong_venue_rejected(self):
        a=days();a['source']='Binance Spot'
        with self.assertRaises(HypeHistoryError):aggregate_weeks(a)
    def test_gap_rejected(self):
        a=days();del a['records'][2]
        with self.assertRaises(HypeHistoryError):aggregate_weeks(a)
if __name__=='__main__':unittest.main()

def test_hype_validated_o2_can_simulate_with_later_proposed_high():
    """HYPE/USDC spot macro remains separate from Binance USDT spot."""
    from wave_macro_context import resolve_long_term_buy
    from pytest import approx
    from datetime import date
    start=date(2026,7,27); end=date(2026,10,18)
    records=[]
    for n in range((end-start).days+1):
        d=start+timedelta(days=n)
        lo=51.11 if d==date(2026,8,2) else 60.0
        hi=97.885 if d==date(2026,9,23) else 85.0
        records.append({'open_utc':d.isoformat()+'T00:00:00+00:00',
            'close_utc':(d+timedelta(days=1)).isoformat()+'T00:00:00+00:00',
            'low':str(lo),'high':str(hi),'close':'70'})
    published={'cycle_low':20.5,'cl_date':'2026-01-21','cl_status':'CONFIRMADO',
        'waves':{'o1':{'price':76.9,'date':'2026-06-16','status':'VALIDADO'},
                 'o2':{'price':51.11,'date':'2026-08-02','status':'VALIDADO'}}}
    data={'status':'OK','source':'Hyperliquid Spot','pair':'HYPE/USDC',
          'interval':'1d','closed_only':True,'records':records}
    result=resolve_long_term_buy('HYPE',published,data)
    assert result['eligible'],result
    assert result['anchors']['low']['status']=='VALIDADO'
    assert result['quote_currency']=='USDC'
    assert result['anchors']['high']['price']==97.885
    assert result['levels']['ref382']==approx(80.01695)
    assert result['levels']['c1']==approx(74.4975)
    assert result['operational_blocked']
