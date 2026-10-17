"""Reference-only Fibonacci reconstruction; NEVER certifies Cycle Low or O1."""
from decimal import Decimal, InvalidOperation


def derive_reference_anchors(c1, c2):
    empty = {'status': 'NO_REFERENCE', 'cycle_low': None, 'o1': None,
             'ref382': None, 'ref782': None, 'ref786': None}
    if c1 is None or c2 is None:
        return empty
    try:
        first=Decimal(str(c1)); second=Decimal(str(c2))
        if not (first > second > 0):
            return dict(empty, status='INVALID_REFERENCE')
        movement=(first-second)/Decimal('0.118')
        high=first+Decimal('0.5')*movement
        low=high-movement
        if not (low>0 and high>low):
            return dict(empty, status='INVALID_REFERENCE')
        return {'status':'INFERRED_FROM_O2_REFERENCES',
          'cycle_low':float(low), 'o1':float(high),
          'ref382':float(high-Decimal('0.382')*movement),
          'ref782':float(high-Decimal('0.782')*movement),
          'ref786':float(high-Decimal('0.786')*movement)}
    except (InvalidOperation,TypeError,ValueError,ArithmeticError):
        return dict(empty, status='INVALID_REFERENCE')
