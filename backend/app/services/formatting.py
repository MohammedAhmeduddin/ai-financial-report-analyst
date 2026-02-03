# backend/app/services/formatting.py
from __future__ import annotations

from typing import Optional, Union

Number = Union[int, float]


def _is_number(x) -> bool:
    return isinstance(x, (int, float))


def format_number(x: Optional[Number], *, decimals: int = 0) -> str:
    if x is None or not _is_number(x):
        return "N/A"
    fmt = f"{{:,.{decimals}f}}"
    return fmt.format(float(x))


def format_currency(x: Optional[Number], *, decimals: int = 0, symbol: str = "$") -> str:
    if x is None or not _is_number(x):
        return "N/A"
    v = float(x)
    s = format_number(abs(v), decimals=decimals)
    return f"-{symbol}{s}" if v < 0 else f"{symbol}{s}"


def format_percent(x: Optional[Number], *, decimals: int = 1) -> str:
    """
    Accepts either:
      - 0.345 meaning 34.5%
      - 34.5 meaning 34.5% (already in percent)
    We'll assume <= 1.5 means ratio, else already percent.
    """
    if x is None or not _is_number(x):
        return "N/A"

    v = float(x)
    if abs(v) <= 1.5:
        v *= 100.0
    return f"{v:.{decimals}f}%"
