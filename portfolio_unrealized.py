"""Read-only unrealized P&L for the published Kairos portfolio.

Market price and units must come from the already validated live dashboard;
never from a screenshot, local snapshots, LIMIT proposals or fills inferred by touch.
"""
import math


def _finite(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        return None
    return value


def summarize_unrealized(rows):
    """Build a 12-token diverging chart and total without inventing missing costs."""
    items = []
    raw_total = 0.0
    raw_cost = 0.0
    missing = []
    for row in rows:
        token = row['token']
        units = _finite(row.get('units'))
        spot = _finite(row.get('price'), positive=True)
        cost = _finite(row.get('avg_cost'), positive=True)
        if units is None or spot is None or (units > 0 and cost is None):
            missing.append(token)
            items.append({'token': token, 'status': 'N/D', 'pnl_usdt': None,
                          'pnl_pct': None, 'bar_pct': 0})
            continue
        # A genuinely empty position has zero unrealized P&L, not an invented cost.
        open_cost = units * cost if units > 0 else 0.0
        pnl = units * spot - open_cost
        raw_total += pnl
        raw_cost += open_cost
        items.append({'token': token, 'status': 'ZERO' if units == 0 else 'OK',
                      'pnl_usdt': round(pnl, 2), 'pnl_pct': (round(pnl / open_cost * 100, 2)
                          if open_cost > 0 else None), 'bar_pct': 0})
    scale = max((abs(x['pnl_usdt']) for x in items if x['pnl_usdt'] is not None), default=0.0)
    for x in items:
        if scale and x['pnl_usdt'] is not None:
            x['bar_pct'] = round(abs(x['pnl_usdt']) / scale * 100, 3)
    return {
        'status': 'OK' if not missing else 'PARCIAL',
        'items': items,
        'total_usdt': round(raw_total, 2) if not missing else None,
        'total_pct': round(raw_total / raw_cost * 100, 2) if raw_cost and not missing else None,
        'cost_open_usdt': round(raw_cost, 2) if not missing else None,
        'missing_tokens': missing,
        'count': len(items),
        'basis': 'Unidades de 02_POSICIONES × (Spot Binance MCP − costo promedio 02_POSICIONES)',
    }
