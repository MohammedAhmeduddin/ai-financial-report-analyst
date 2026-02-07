# bakcend/app/service/llm.py
from typing import Dict, Any
from openai import OpenAI
from app.core.config import settings


def _get_client() -> OpenAI:
    """
    Lazy OpenAI client.
    This prevents FastAPI from crashing at startup
    if OPENAI_API_KEY is not set (local dev).
    """
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=settings.openai_api_key)


def explain_variance(
    *,
    variance: Dict[str, Any],
    question: str,
) -> str:
    """
    Turn structured variance data into a concise analyst-style narrative.
    """

    print("🔥🔥 OPENAI LLM CALLED 🔥🔥")

    client = _get_client()

    prompt = f"""
You are a senior financial analyst.

Given the variance drivers below, write a concise,
professional explanation answering the user's question.

Question:
{question}

Variance drivers (structured data):
{variance}

Guidelines:
- Focus on material drivers
- Be factual and numbers-first
- No speculation
- 4–6 sentences max
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()
