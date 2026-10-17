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
