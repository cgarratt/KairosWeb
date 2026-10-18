"""Disabled inverse historical Fibonacci reconstruction.

Do NOT derive CL/O1 from legacy C1/C2. Real levels must flow forward
from dated weekly CL/O1 via wave_structure.fib_grid.
"""
def derive_reference_anchors(c1,c2):
    return {'status':'LEGACY_INVERSE_DISABLED','cycle_low':None,'o1':None,
            'ref382':None,'ref782':None,'ref786':None}
