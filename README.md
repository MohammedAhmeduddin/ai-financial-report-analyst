# AI Financial Report Analyst (RAG + Variance Drivers)

An AI-powered platform that ingests quarterly financial PDFs, extracts key metrics, compares periods (base vs compare), and answers questions with numbers-first variance explanations and citations.

## What this does

- Upload a PDF (e.g., FY24 Q4)
- Extract pages into text chunks
- Extract core financial metrics (revenue, gross profit, operating income, net income, taxes, etc.)
- Compare two periods and explain net income changes via drivers:
  - revenue impact
  - margin impact
  - opex impact
  - other (below-the-line) + breakdown (tax vs other income/expense)
- Ask questions in single-doc mode or compare mode with citations

## Tech Stack

- Backend: FastAPI, Pydantic, Uvicorn
- PDF parsing: pdfplumber / pdfminer.six
- Testing: pytest
- Linting: ruff

---

# Backend Setup (Local)

## 1) Create and activate venv

```bash
cd backend
python -m venv .venv
source .venv/bin/activate

## Install deps

pip install -r requirements.txt
pip install -r requirements-dev.txt


## Run tests

pytest -q


## Start API

uvicorn app.main:app --reload

Open Swagger:

http://127.0.0.1:8000/docs




End-to-End Demo (FY24 as base, FY25 as compare)

Rule:

base = older period (FY24)

compare = newer period (FY25)

A) Upload both PDFs

Use POST /upload twice:

Upload FY24 → copy upload_id → BASE_ID

Upload FY25 → copy upload_id → COMPARE_ID

B) Run pipeline (extract → metrics) for each upload

POST /extract/{upload_id}

POST /metrics/{upload_id}

C) Compare them

POST /variance/{base_upload_id}/{compare_upload_id}

D) Ask in compare mode

Call:

POST /ask/{upload_id} with upload_id = BASE_ID

Body:

{
  "question": "Why did net income change?",
  "compare_upload_id": "COMPARE_ID"
}
```
