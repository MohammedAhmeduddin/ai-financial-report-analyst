from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Evidence:
    page: int
    snippet: str


def _clean_snippet(s: str, max_len: int = 220) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


def _parse_number(raw: str) -> Optional[float]:
    """
    Parses numbers like:
      123,456
      (1,234)   -> -1234
      123.45
    """
    if raw is None:
        return None
    raw = raw.strip()

    neg = False
    if raw.startswith("(") and raw.endswith(")"):
        neg = True
        raw = raw[1:-1].strip()

    raw = raw.replace("$", "").replace(",", "").strip()

    if not re.fullmatch(r"-?\d+(\.\d+)?", raw):
        return None

    val = float(raw)
    if neg:
        val = -val
    return val


def _find_first(pattern: re.Pattern[str], pages: List[Dict[str, Any]]) -> Optional[Tuple[float, Evidence]]:
    for p in pages:
        page_no = int(p.get("page", 0))
        text = str(p.get("text", ""))

        m = pattern.search(text)
        if not m:
            continue

        raw_num = m.group("num")
        val = _parse_number(raw_num)
        if val is None:
            continue

        snippet = _clean_snippet(text[m.start(): m.start() + 350])
        return val, Evidence(page=page_no, snippet=snippet)

    return None


def extract_basic_metrics(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic, best-effort metric extraction.

    Fixes included:
    - revenue no longer captures footnote markers like "(1)".
    - income_taxes anchored so it doesn’t match the "income before ..." line.
    - Tries multiple patterns per metric (in priority order).
    """

    NUM = r"(?P<num>\(?\$?\s*[\d,]+(?:\.\d+)?\)?)"

    patterns: Dict[str, List[re.Pattern[str]]] = {
        # --------------------------
        # Income statement
        # --------------------------

        # ✅ Revenue: try "Products $ 73,716" first (has $ so avoids cost-of-sales products line)
        # Fallback to total net sales and ignore optional footnote marker like "(1)"
        "revenue": [
            re.compile(rf"(?im)^\s*products\s*\$\s*{NUM}"),
            re.compile(rf"(?im)^\s*total net sales(?:\s*\(\d+\))?\b[^\n]*?\s{NUM}"),
            re.compile(rf"(?im)^\s*net sales(?:\s*\(\d+\))?\b[^\n]*?\s{NUM}"),
        ],

        "gross_profit": [
            re.compile(rf"(?im)^\s*(gross profit|gross margin)\b[^\n]*?{NUM}"),
        ],

        "operating_income": [
            re.compile(rf"(?im)^\s*operating income\b[^\n]*?{NUM}"),
        ],

        "other_income_expense_net": [
            re.compile(rf"(?im)^\s*other income/\(expense\),\s*net\b[^\n]*?{NUM}"),
        ],

        "pre_tax_income": [
            re.compile(rf"(?im)^\s*income before (provision for )?income taxes\b[^\n]*?{NUM}"),
        ],

        # ✅ Income taxes: match ONLY the actual tax line
        "income_taxes": [
            re.compile(rf"(?im)^\s*provision for income taxes\b[^\n]*?{NUM}"),
        ],

        "net_income": [
            re.compile(rf"(?im)^\s*net income\b[^\n]*?{NUM}"),
        ],

        # --------------------------
        # Balance sheet
        # --------------------------
        "total_assets": [
            re.compile(rf"(?im)^\s*total assets\b[^\n]*?{NUM}"),
        ],

        "total_liabilities": [
            re.compile(rf"(?im)^\s*total liabilities\b[^\n]*?{NUM}"),
        ],
    }

    metrics: Dict[str, Optional[float]] = {k: None for k in patterns.keys()}
    evidence: Dict[str, Optional[Dict[str, Any]]] = {k: None for k in patterns.keys()}

    for key, pats in patterns.items():
        for pat in pats:
            found = _find_first(pat, pages)
            if found:
                val, ev = found
                metrics[key] = val
                evidence[key] = {"page": ev.page, "snippet": ev.snippet}
                break  # stop at first successful pattern for this metric

    return {"metrics": metrics, "evidence": evidence}
