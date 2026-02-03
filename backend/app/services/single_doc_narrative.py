# backend/app/services/single_doc_narrative.py
from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.formatting import format_currency, format_percent


def _num(metrics: Dict[str, Any], key: str) -> Optional[float]:
    v = metrics.get(key)
    return float(v) if isinstance(v, (int, float)) else None


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def build_single_doc_narrative(
    *,
    question: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
    metric_key: Optional[str] = None,
    metric_value: Optional[float] = None,
) -> str:
    """
    v1 narrative builder:
    - Accepts question/metric_key/metric_value (to satisfy tests)
    - Optionally accepts metrics dict to create a richer snapshot (used by qa.py)
    """

    lines = []

    # Include question (nice for debugging / clarity, tests won't mind)
    if question:
        lines.append(f"Question: {question}")

    # If metrics are provided, add a mini snapshot
    metrics = metrics or {}
    revenue = _num(metrics, "revenue")
    gross_profit = _num(metrics, "gross_profit")
    operating_income = _num(metrics, "operating_income")
    net_income = _num(metrics, "net_income")

    gross_margin = _safe_div(gross_profit, revenue)
    op_margin = _safe_div(operating_income, revenue)
    net_margin = _safe_div(net_income, revenue)

    if metrics:
        lines.append("Numbers-first snapshot (from stored metrics):")

        if revenue is not None:
            lines.append(f"- Revenue: {format_currency(revenue)}")
        if gross_profit is not None:
            lines.append(f"- Gross profit: {format_currency(gross_profit)}")
        if gross_margin is not None:
            lines.append(f"- Gross margin: {format_percent(gross_margin)}")

        if operating_income is not None:
            lines.append(f"- Operating income: {format_currency(operating_income)}")
        if op_margin is not None:
            lines.append(f"- Operating margin: {format_percent(op_margin)}")

        if net_income is not None:
            lines.append(f"- Net income: {format_currency(net_income)}")
        if net_margin is not None:
            lines.append(f"- Net margin: {format_percent(net_margin)}")

    # Direct “metric answer” (this is what your tests are validating)
    if metric_key:
        pretty = metric_key.replace("_", " ").title()
        if metric_value is not None:
            lines.append(f"Direct answer: {pretty} is {format_currency(metric_value)}.")
        else:
            lines.append(f"Direct answer: I couldn’t find a numeric value for {pretty}.")

    # Fallback if nothing got added
    if not lines:
        return "No narrative available yet."

    return "\n".join(lines)
