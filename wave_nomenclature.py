"""KairosWave v1.6 canonical labels and safe legacy Fib crosswalk."""
from forecast_fibo_policy import TRANCHE_KEYS
STAGES = {
  'O2':(('O2C1','38.2%'),('O2C2','50%'),('O2C3','61.8%'),('O2C4','78.6%')),
  'O3':(('O3V1','1.618'),('O3V2','2.618'),('O3V3','3.618'),('O3V4','4.618')),
  'O4':(('O4C1','38.2%'),('O4C2','50%'),('O4C3','61.8%'),('O4C4','78.6%')),
  'O5':(('O5V1','1.618'),('O5V2','2.618'),('O5V3','3.618'),('O5V4','4.618')),
}
LEGACY_O2 = {'C1_FIB50':'O2C2', 'C2_FIB61_8':'O2C3', 'FIB38_2':'O2C1', 'FIB78_2_HISTORICAL':'O2C4'}
def canonical(stage,index):
    if stage not in STAGES or not isinstance(index,int) or index not in range(4):
        raise ValueError('Invalid stage/index')
    return STAGES[stage][index][0]
def validate_crosswalk():
    assert LEGACY_O2['C1_FIB50']=='O2C2'
    assert LEGACY_O2['C2_FIB61_8']=='O2C3'
    assert len({x[0] for stage in STAGES.values() for x in stage})==16
    assert len({k for keys in TRANCHE_KEYS.values() for k in keys})==16
validate_crosswalk()
