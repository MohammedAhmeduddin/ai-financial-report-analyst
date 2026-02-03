from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Chunk:
    chunk_id: str
    upload_id: str
    page_start: int
    page_end: int
    token_count: int
    text: str
    meta: Dict[str, Any]


def _approx_token_count(text: str) -> int:
    # simple, deterministic approximation (good enough for now)
    return max(1, len(text.split()))


def chunk_pages(
    upload_id: str,
    pages: List[Dict[str, Any]],
    max_tokens: int = 700,
    overlap_tokens: int = 120,
    meta: Dict[str, Any] | None = None,
) -> List[Chunk]:
    meta = meta or {}

    chunks: List[Chunk] = []
    buf_parts: List[str] = []
    buf_tokens = 0
    start_page = None
    chunk_idx = 0

    def flush(end_page: int):
        nonlocal chunk_idx, buf_parts, buf_tokens, start_page
        if not buf_parts or start_page is None:
            return
        text = "\n".join(buf_parts).strip()
        chunks.append(
            Chunk(
                chunk_id=f"{upload_id}::chunk::{chunk_idx}",
                upload_id=upload_id,
                page_start=start_page,
                page_end=end_page,
                token_count=_approx_token_count(text),
                text=text,
                meta=meta,
            )
        )
        chunk_idx += 1

        # overlap: keep last overlap_tokens words
        words = text.split()
        keep = words[-overlap_tokens:] if overlap_tokens > 0 else []
        buf_parts = [" ".join(keep)] if keep else []
        buf_tokens = _approx_token_count(buf_parts[0]) if buf_parts else 0
        start_page = end_page  # overlap starts at end_page (good enough)

    for p in pages:
        page_num = int(p["page"])
        page_text = (p.get("text") or "").strip()
        if start_page is None:
            start_page = page_num

        page_tokens = _approx_token_count(page_text)

        # if adding would exceed, flush first
        if buf_tokens + page_tokens > max_tokens and buf_parts:
            flush(page_num)

        buf_parts.append(page_text)
        buf_tokens += page_tokens

    # final flush
    if start_page is not None:
        flush(int(pages[-1]["page"]))

    return chunks
