from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.services.metrics_store import load_metrics
from app.services.parsing import load_extracted_pages
from app.services.qa import answer_numbers_first, build_citations_for_keywords
from app.services.variance import compute_variance_drivers
from app.services.narrative import build_variance_narrative

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str
    compare_upload_id: Optional[str] = None
    max_tokens: int = 700
    overlap_tokens: int = 120


def _looks_like_cashflow(text: str) -> bool:
    """
    Heuristic filter:
    Avoid cash flow citations such as "Payments for taxes related to..."
    """
    t = (text or "").lower()
    markers = [
        "cash flow",
        "cash generated",
        "cash used",
        "operating activities",
        "investing activities",
        "financing activities",
        "payments for",
        "net cash",
    ]
    return any(m in t for m in markers)


def _looks_like_balance_sheet(text: str) -> bool:
    """
    Heuristic filter:
    Avoid balance sheet citations such as "LIABILITIES AND SHAREHOLDERS’ EQUITY"
    """
    t = (text or "").lower()
    markers = [
        "liabilities and shareholders",
        "shareholders’ equity",
        "shareholders' equity",
        "total assets",
        "total liabilities",
        "current liabilities",
        "accounts payable",
        "deferred revenue",
        "commercial paper",
    ]
    return any(m in t for m in markers)


def _filter_income_statement_only(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove citations that look like cash flow or balance sheet.
    Keep ordering (ranker already sorted them).
    """
    out: List[Dict[str, Any]] = []
    for c in citations:
        preview = str(c.get("text_preview", ""))
        if _looks_like_cashflow(preview):
            continue
        if _looks_like_balance_sheet(preview):
            continue
        out.append(c)
    return out


@router.post("/ask/{upload_id}")
def ask(upload_id: str, req: AskRequest):
    # --- base metrics ---
    try:
        base_payload = load_metrics(settings.storage_dir, upload_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="metrics not found (run /metrics first)")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    base_metrics = base_payload.get("metrics", {})

    # --- base extracted pages ---
    try:
        base_pages = load_extracted_pages(settings.storage_dir, upload_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="extraction not found (run /extract first)")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ✅ single-doc mode (no compare)
    if not req.compare_upload_id:
        return answer_numbers_first(
            upload_id=upload_id,
            question=req.question,
            metrics=base_metrics,
            pages=base_pages,
            max_tokens=req.max_tokens,
            overlap_tokens=req.overlap_tokens,
        )

    # --- compare mode ---
    compare_id = req.compare_upload_id

    # compare metrics
    try:
        compare_payload = load_metrics(settings.storage_dir, compare_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="compare metrics not found (run /metrics first)")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    compare_metrics = compare_payload.get("metrics", {})

    # compare extracted pages
    try:
        compare_pages = load_extracted_pages(settings.storage_dir, compare_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="compare extraction not found (run /extract first)")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Compute variance drivers + narrative
    try:
        variance_result = compute_variance_drivers(base_metrics, compare_metrics)
        narrative = build_variance_narrative(
            base_upload_id=upload_id,
            compare_upload_id=compare_id,
            variance=variance_result,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ✅ Build citations (income-statement specific keywords)
    # Keep these tight so citations come from the Statements of Operations.
    driver_keywords = [
        # income statement line items
        "other income/(expense), net",
        "provision for income taxes",
        "income before provision for income taxes",
        "income before income taxes",
        "operating income",
        "net income",
        # header anchors to lock chunks onto the right statement
        "condensed consolidated statements of operations",
        "statements of operations",
    ]

    citations_base = build_citations_for_keywords(
        upload_id=upload_id,
        pages=base_pages,
        keywords=driver_keywords,
        max_tokens=req.max_tokens,
        overlap_tokens=req.overlap_tokens,
        top_k=10,
    )

    citations_compare = build_citations_for_keywords(
        upload_id=compare_id,
        pages=compare_pages,
        keywords=driver_keywords,
        max_tokens=req.max_tokens,
        overlap_tokens=req.overlap_tokens,
        top_k=10,
    )

    # Filter out cash flow + balance sheet citations
    citations_base = _filter_income_statement_only(citations_base)
    citations_compare = _filter_income_statement_only(citations_compare)

    # Keep a cap so the response stays compact
    citations = citations_base[:5] + citations_compare[:5]

    return {
        "upload_id": upload_id,
        "compare_upload_id": compare_id,
        "question": req.question,

        # legacy: numbers_first
        "numbers_first": {
            "base_metrics": base_metrics,
            "compare_metrics": compare_metrics,
        },

        # legacy alias
        "evidence": citations,

        # new fields
        "variance": variance_result,
        "citations": citations,
        "answer": narrative,
    }
