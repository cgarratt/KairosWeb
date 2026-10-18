"""Outlier screening for exploratory structural CL, NOT market OHLCV editing.

Master historically records explicit SUI/PUMP exceptions; VIRTUAL flash
exclusion is a development-only review rule pending publication in the Master.
Never rewrite or silently 'confirm' a historical anchor.
"""
from datetime import date

VIRTUAL_FLASH_WEEK_START = date(2025, 10, 6)
VIRTUAL_FLASH_WEEK_END = date(2025, 10, 12)
VIRTUAL_FLASH_RAW_LOW = 0.2772


def virtual_flash_cl(price, when):
    """Identify VIRTUAL raw Oct 2025 crash low, not arbitrary later lows."""
    try:
        day = date.fromisoformat(str(when)[:10]) if when else None
        if day is not None:
            return VIRTUAL_FLASH_WEEK_START <= day <= VIRTUAL_FLASH_WEEK_END
        return abs(float(price) - VIRTUAL_FLASH_RAW_LOW) < 1e-8
    except (TypeError, ValueError):
        return False
