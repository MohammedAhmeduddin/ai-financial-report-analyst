# backend/app/services/qa.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.services.chunking import chunk_pages
from app.services.single_doc_narrative import build_single_doc_narrative


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    page_start: int
    page_end: int
    text_preview: str


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _pick_metric(
    question: str, metrics: Dict[str, Any]
) -> Tuple[Optional[str], Optional[float], List[str]]:
    """
    Returns: (metric_key, metric_value, keywords_to_find_in_text)
    """
    q = _normalize(question)

    # Add more mappings over time (EPS, cash flow, etc.)
    mapping = [
        (["net income", "profit", "net earnings"], "net_income", ["net income", "net earnings"]),
        (["revenue", "sales"], "revenue", ["revenue", "net sales", "total net sales"]),
        (["gross profit", "gross margin"], "gross_profit", ["gross profit", "gross margin"]),
        (["operating income", "operating profit"], "operating_income", ["operating income"]),

        # ✅ NEW
        (["income taxes", "tax expense", "provision for income taxes", "tax"], "income_taxes",
         ["provision for income taxes", "income taxes"]),
        (["other income", "other expense", "other income/expense"], "other_income_expense_net",
         ["other income/(expense), net", "other income/(expense)"]),
        (["income before taxes", "pre tax", "pretax", "pre-tax"], "pre_tax_income",
         ["income before provision for income taxes", "income before income taxes"]),
    ]


    for triggers, key, keywords in mapping:
        if any(t in q for t in triggers):
            val = metrics.get(key)
            if isinstance(val, (int, float)):
                return key, float(val), keywords
            # If metric exists but not numeric, treat as missing
            return key, None, keywords

    return None, None, []


def _rank_chunks_by_keywords(chunks, keywords: List[str], top_k: int = 3):
    """
    Simple lexical ranking:
      score = sum(keyword occurrences) + small bonus if keyword appears early
    """
    if not keywords:
        return chunks[:top_k]

    kws = [_normalize(k) for k in keywords]

    scored = []
    for c in chunks:
        text = _normalize(c.text)
        score = 0.0
        for kw in kws:
            count = text.count(kw)
            if count:
                score += count * 10
                first = text.find(kw)
                if first >= 0:
                    score += max(0, 5 - (first / 500))  # small early-appearance bonus
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [c for _, c in scored[:top_k]]
    return chunks[:top_k]


def answer_numbers_first(
    *,
    upload_id: str,
    question: str,
    metrics: Dict[str, Any],
    pages: List[Dict[str, Any]],
    max_tokens: int = 700,
    overlap_tokens: int = 120,
) -> Dict[str, Any]:
    """
    Returns an answer payload with:
      - computed values (numbers-first)
      - citations from best-matching chunks
      - narrative answer (Step 12B)
    """
    metric_key, metric_value, keywords = _pick_metric(question, metrics)

    chunks = chunk_pages(
        upload_id=upload_id,
        pages=pages,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        meta={"source": "10q_pdf"},
    )

    best = _rank_chunks_by_keywords(chunks, keywords, top_k=3)

    citations: List[Dict[str, Any]] = [
        {
            "chunk_id": c.chunk_id,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "text_preview": c.text[:300],
        }
        for c in best
    ]

    computed: Dict[str, Any] = {}
    if metric_key is not None:
        computed[metric_key] = metric_value

    # ✅ Step 12B: replace old if/elif/else with narrative builder
    narrative = build_single_doc_narrative(
         question=question,
        metrics=metrics,
    metric_key=metric_key,
    metric_value=metric_value,
    )

    # ✅ Keep old contract + new fields
    return {
        "upload_id": upload_id,
        "question": question,

        # old contract (tests/earlier steps expect this)
        "numbers_first": {"metrics": metrics},

        # old alias (some earlier steps used this)
        "evidence": citations,

        # new fields (keep)
        "answer": narrative,
        "computed": computed,
        "citations": citations,
    }


def build_citations_for_keywords(
    *,
    upload_id: str,
    pages: List[Dict[str, Any]],
    keywords: List[str],
    max_tokens: int = 700,
    overlap_tokens: int = 120,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Utility helper for other services/endpoints to fetch top citations
    given a set of keywords (lexical ranking over chunks).
    """
    chunks = chunk_pages(
        upload_id=upload_id,
        pages=pages,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        meta={"source": "10q_pdf"},
    )
    best = _rank_chunks_by_keywords(chunks, keywords, top_k=top_k)

    return [
        {
            "upload_id": upload_id,
            "chunk_id": c.chunk_id,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "text_preview": c.text[:300],
        }
        for c in best
    ]

