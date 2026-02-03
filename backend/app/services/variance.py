from __future__ import annotations

from typing import Any, Dict, Optional


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None


def compute_variance_drivers(
    base: Dict[str, Any],
    compare: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Numbers-first variance driver analysis.

    Required:
      net_income (both)

    Best-effort drivers:
      - revenue_impact
      - margin_impact
      - opex_impact
      - other (below-the-line bucket)

    NEW (if available in metrics):
      - tax_impact (from income_taxes)
      - other_income_expense_impact (from other_income_expense_net)
      - remaining_other_impact (what's left inside "other" after tax + other income/expense)

    Notes:
      - We keep legacy keys so earlier steps/tests won't break.
      - We add auditable fields: drivers_list, explained_total, residual.
      - other_breakdown is only returned when we can compute at least one component.
    """
    # --- core metrics ---
    base_rev = _to_float(base.get("revenue"))
    cmp_rev = _to_float(compare.get("revenue"))

    base_gp = _to_float(base.get("gross_profit"))
    cmp_gp = _to_float(compare.get("gross_profit"))

    base_oi = _to_float(base.get("operating_income"))
    cmp_oi = _to_float(compare.get("operating_income"))

    base_ni = _to_float(base.get("net_income"))
    cmp_ni = _to_float(compare.get("net_income"))

    # --- optional below-the-line components ---
    base_tax = _to_float(base.get("income_taxes"))
    cmp_tax = _to_float(compare.get("income_taxes"))

    base_other_ie = _to_float(base.get("other_income_expense_net"))
    cmp_other_ie = _to_float(compare.get("other_income_expense_net"))

    if base_ni is None or cmp_ni is None:
        raise ValueError("Both base and compare must include net_income (number)")

    net_income_change = cmp_ni - base_ni

    drivers: Dict[str, Optional[float]] = {
        "revenue_impact": None,
        "margin_impact": None,
        "opex_impact": None,
        "other": None,  # legacy below-the-line bucket
        "residual": None,
    }

    # --- Revenue & margin impacts ---
    revenue_impact = None
    margin_impact = None
    if base_rev is not None and base_gp is not None and cmp_rev is not None and cmp_gp is not None:
        if base_rev != 0:
            base_gm = base_gp / base_rev
            revenue_impact = (cmp_rev - base_rev) * base_gm
            gp_expected = base_gp + revenue_impact
            margin_impact = cmp_gp - gp_expected

    drivers["revenue_impact"] = revenue_impact
    drivers["margin_impact"] = margin_impact

    # --- Opex impact ---
    opex_impact = None
    if base_gp is not None and cmp_gp is not None and base_oi is not None and cmp_oi is not None:
        base_opex = base_gp - base_oi
        cmp_opex = cmp_gp - cmp_oi
        delta_opex = cmp_opex - base_opex
        opex_impact = -delta_opex  # more opex reduces income

    drivers["opex_impact"] = opex_impact

    # --- Legacy "other" bucket = change in (net_income - operating_income) ---
    other_bucket = None
    if base_oi is not None and cmp_oi is not None:
        base_below = base_ni - base_oi
        cmp_below = cmp_ni - cmp_oi
        other_bucket = cmp_below - base_below

    drivers["other"] = other_bucket

    # --- NEW: Break down "other" into Taxes vs Other income/(expense) if possible ---
    other_breakdown = None
    if other_bucket is not None:
        tax_impact = None
        other_income_expense_impact = None

        # Taxes: higher tax expense reduces net income => negative impact
        if base_tax is not None and cmp_tax is not None:
            tax_impact = -(cmp_tax - base_tax)

        # Other income/(expense), net: delta contributes directly to below-the-line change
        if base_other_ie is not None and cmp_other_ie is not None:
            other_income_expense_impact = (cmp_other_ie - base_other_ie)

        used = 0.0
        used_any = False
        if tax_impact is not None:
            used += float(tax_impact)
            used_any = True
        if other_income_expense_impact is not None:
            used += float(other_income_expense_impact)
            used_any = True

        remaining_other_impact = (float(other_bucket) - used) if used_any else None

        # Only include breakdown if we computed at least one component
        if used_any:
            other_breakdown = {
                "tax_impact": tax_impact,
                "other_income_expense_impact": other_income_expense_impact,
                "remaining_other_impact": remaining_other_impact,
            }

    # --- Residual reconciliation (always reconcile to net_income_change) ---
    explained_sum = 0.0
    explained_any = False
    for k in ("revenue_impact", "margin_impact", "opex_impact", "other"):
        v = drivers.get(k)
        if isinstance(v, (int, float)):
            explained_sum += float(v)
            explained_any = True

    residual = (net_income_change - explained_sum) if explained_any else net_income_change
    drivers["residual"] = residual

    # --- ranked drivers list (exclude residual from ranking) ---
    driver_rows = []
    for name in ("revenue_impact", "margin_impact", "opex_impact", "other"):
        impact = drivers.get(name)
        if isinstance(impact, (int, float)):
            pct = None
            if net_income_change != 0:
                pct = (float(impact) / float(net_income_change)) * 100.0
            driver_rows.append(
                {"name": name, "impact": float(impact), "pct_of_change": pct}
            )

    driver_rows.sort(key=lambda d: abs(d["impact"]), reverse=True)

    explained_total = sum(d["impact"] for d in driver_rows) if driver_rows else 0.0

    # Keep residual consistent with explained_total
    residual = float(net_income_change) - float(explained_total)
    drivers["residual"] = residual

    explained_pct = None
    if net_income_change != 0 and driver_rows:
        explained_pct = round((explained_total / float(net_income_change)) * 100.0, 2)

    return {
        "net_income_change": net_income_change,
        "drivers": drivers,
        "explained_pct": explained_pct,

        # auditable ranking
        "drivers_list": driver_rows,
        "explained_total": explained_total,
        "residual": residual,

        # breakdown for "other" (optional)
        "other_breakdown": other_breakdown,
    }
