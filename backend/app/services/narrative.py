from __future__ import annotations

from typing import Any, Dict, List, Tuple


# Pretty labels for driver keys
_DRIVER_LABELS = {
    "revenue_impact": "Revenue impact",
    "margin_impact": "Margin impact",
    "opex_impact": "OpEx impact",
    "other": "Other (below-the-line)",
    "residual": "Residual",
}


def _fmt(x: Any) -> str:
    """Format numbers consistently (2 decimals, with commas)."""
    if isinstance(x, (int, float)):
        return f"{float(x):,.2f}"
    return str(x)


def _fmt_signed(x: Any) -> str:
    """Format numbers with +/- sign for readability."""
    if isinstance(x, (int, float)):
        x = float(x)
        sign = "+" if x >= 0 else ""
        return f"{sign}{x:,.2f}"
    return str(x)


def _label(name: str) -> str:
    return _DRIVER_LABELS.get(name, name.replace("_", " ").title())


def build_variance_narrative(
    *,
    base_upload_id: str,
    compare_upload_id: str,
    variance: Dict[str, Any],
    top_n: int = 3,
) -> str:
    """
    Takes compute_variance_drivers output and generates a readable explanation.

    Backward-compatible with your original variance output:
      - net_income_change (float)
      - explained_pct (float)
      - drivers (dict[str, float])

    Supports enhanced output:
      - drivers_list (ranked list[{name, impact, pct_of_change}])
      - explained_total (float)
      - residual (float)
      - other_breakdown (dict with tax_impact, other_income_expense_impact, remaining_other_impact)
    """
    net_change = variance.get("net_income_change")
    explained_pct = variance.get("explained_pct")

    drivers = variance.get("drivers", {}) or {}
    drivers_list = variance.get("drivers_list") or []

    # Build ranked items for display (exclude residual)
    items: List[Tuple[str, float]] = []

    if isinstance(drivers_list, list) and drivers_list:
        for d in drivers_list:
            name = d.get("name")
            impact = d.get("impact")
            if isinstance(name, str) and isinstance(impact, (int, float)) and name != "residual":
                items.append((name, float(impact)))
    else:
        for k, v in drivers.items():
            if k == "residual":
                continue
            if not isinstance(v, (int, float)):
                continue
            items.append((k, float(v)))
        items.sort(key=lambda kv: abs(kv[1]), reverse=True)

    top = items[:top_n]

    # Direction string
    direction = "changed"
    if isinstance(net_change, (int, float)):
        if float(net_change) == 0:
            direction = "was flat"
        elif float(net_change) > 0:
            direction = "increased"
        else:
            direction = "decreased"

    lines: List[str] = []

    # Header
    if isinstance(net_change, (int, float)):
        lines.append(
            f"Net income {direction} by {_fmt(abs(float(net_change)))} when comparing {base_upload_id} vs {compare_upload_id}."
            if direction in ("increased", "decreased")
            else f"Net income {direction} ({_fmt(net_change)}) when comparing {base_upload_id} vs {compare_upload_id}."
        )
    else:
        lines.append(f"Computed variance drivers for {base_upload_id} vs {compare_upload_id}.")

    # Explained %
    if isinstance(explained_pct, (int, float)):
        lines.append(f"Drivers explain about {_fmt(explained_pct)}% of the change.")

    # Top drivers
    if top:
        lines.append("Top drivers:")
        for name, val in top:
            lines.append(f"- {_label(name)}: {_fmt_signed(val)}")

    # --- NEW: Optional breakdown for "other" ---
    other_breakdown = variance.get("other_breakdown")
    other_val = None
    if isinstance(drivers.get("other"), (int, float)):
        other_val = float(drivers["other"])
    else:
        # If drivers dict missing but drivers_list exists
        for n, v in items:
            if n == "other":
                other_val = float(v)
                break

    if isinstance(other_breakdown, dict) and other_val is not None:
        tax_impact = other_breakdown.get("tax_impact")
        other_ie_impact = other_breakdown.get("other_income_expense_impact")
        remaining = other_breakdown.get("remaining_other_impact")

        # Show breakdown only if at least one component is numeric
        if any(isinstance(x, (int, float)) for x in (tax_impact, other_ie_impact, remaining)):
            lines.append("")
            lines.append(f"Breakdown of Other (below-the-line) ({_fmt_signed(other_val)}):")

            if isinstance(tax_impact, (int, float)):
                lines.append(f"- Taxes impact: {_fmt_signed(tax_impact)}")
            if isinstance(other_ie_impact, (int, float)):
                lines.append(f"- Other income/(expense), net impact: {_fmt_signed(other_ie_impact)}")
            if isinstance(remaining, (int, float)):
                lines.append(f"- Remaining (interest/one-offs/other): {_fmt_signed(remaining)}")

    # Reconciliation (only if enhanced fields exist)
    explained_total = variance.get("explained_total")
    residual = variance.get("residual")
    if isinstance(explained_total, (int, float)) and isinstance(residual, (int, float)):
        lines.append("")
        lines.append(f"Reconciliation: explained_total={_fmt(explained_total)}, residual={_fmt(residual)}.")

    return "\n".join(lines)
