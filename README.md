# AI Financial Report Analyst

**Numbers-First Financial Analysis with Variance Drivers, Citations, and AI Analyst Commentary**

🔗 **Live Demo (Production):**
👉 https://ai-financial-report-analyst-fawn.vercel.app

This project demonstrates **applied Generative AI**, **retrieval-augmented generation (RAG)**, and **deterministic financial variance analysis** in a production-ready system.
The architecture prioritizes **numbers-first reasoning**, **document-grounded citations**, and **explainability**, ensuring AI output remains auditable, reliable, and suitable for real financial workflows.

An end-to-end AI-powered platform that ingests quarterly financial reports (PDFs), extracts audited financial metrics, compares periods (base vs compare), and explains **why financial performance changed** — using **deterministic variance logic** and **LLM-assisted analyst narratives**, fully grounded with citations.

---

## 🚀 What This Project Does

This system answers the real question financial analysts, investors, and executives ask:

> **“Why did net income change?”**

It delivers **auditable, numbers-first explanations**, supported by:

- structured variance drivers
- deterministic calculations
- optional AI analyst commentary
- document-level citations from financial statements

---

## 🔍 Core Capabilities

### 📄 PDF Ingestion & Parsing

- Upload quarterly financial statements (e.g., FY24 Q4, FY25 Q4)
- Extract and chunk pages for downstream analysis
- Designed for audited filings (Statements of Operations)

### 📊 Metrics Extraction

Extracts key income-statement metrics:

- Revenue
- Gross profit
- Operating income
- Other income / expense (net)
- Income taxes
- Net income
- Total assets & liabilities (stored, filtered for citations)

### 📈 Variance Analysis (Compare Mode)

Compares **Base period vs Compare period** and computes:

- Revenue impact
- Margin impact
- Operating expense impact
- Other (below-the-line) impact
  - Tax impact
  - Other income / expense impact

Ensures:

- Full reconciliation (100% explained)
- Zero residuals
- Deterministic, auditable logic

### 🧠 AI Analyst Commentary (Optional)

- Uses OpenAI to generate a **concise analyst-style explanation**
- Strictly grounded in computed variance drivers
- Numbers-first, no speculation
- Automatically disabled if no API key is present (production-safe)

### 📌 Citations & Evidence

- Retrieves citations only from **Statements of Operations**
- Filters out cash flow and balance sheet noise
- Shows exact document chunks used for grounding

---

## 🧱 System Architecture

Frontend (React + Vercel)
|
| REST API
|
Backend (FastAPI + Render)
|
|-- PDF Parsing (pdfplumber / pdfminer)
|-- Metrics Store
|-- Variance Engine (Deterministic)
|-- Citation Builder
|-- Optional LLM Service (OpenAI)

---

## 🛠️ Tech Stack

### Backend

- **FastAPI** – API framework
- **Pydantic** – request / response validation
- **Uvicorn** – ASGI server
- **pdfplumber / pdfminer.six** – PDF parsing
- **pytest** – testing
- **ruff** – linting

### Frontend

- **React**
- **Vercel** – production deployment

### AI / NLP

- **OpenAI API** (optional, production-safe)
- Lazy initialization to prevent startup crashes

---

## 🧪 Local Development Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest -q
```

### Start API

```bash
uvicorn app.main:app --reload
```

### Swagger UI

    http://127.0.0.1:8000/docs

---

## 🔑 Environment Variables

### Backend (`.env`)

```env
APP_NAME="AI Financial Report Analyst"
ENV="dev"

OPENAI_API_KEY=your_openai_api_key_here

STORAGE_DIR="storage"
UPLOAD_DIR="storage/uploads"
EXTRACTED_DIR="storage/extracted"
CHUNKS_DIR="storage/chunks"

MAX_UPLOAD_MB=50
LOG_LEVEL="INFO"
```

⚠️ **Note:**\
The application runs without OpenAI.\
AI commentary is automatically disabled if `OPENAI_API_KEY` is not set.

---

## 🧠 End-to-End Usage Flow

### Rule

- **Base** = older period (e.g., FY24)\
- **Compare** = newer period (e.g., FY25)

---

### 1️⃣ Upload PDFs

    POST /upload

Upload both: - FY24 → save `BASE_ID` - FY25 → save `COMPARE_ID`

---

### 2️⃣ Extract Text

    POST /extract/{upload_id}

Run for both uploads.

---

### 3️⃣ Extract Metrics

    POST /metrics/{upload_id}

Run for both uploads.

---

### 4️⃣ Compute Variance

    POST /variance/{BASE_ID}/{COMPARE_ID}

---

### 5️⃣ Ask a Question (Compare Mode)

    POST /ask/{BASE_ID}

#### Request Body

```json
{
  "question": "Why did net income change?",
  "compare_upload_id": "COMPARE_ID"
}
```

#### Response Includes

- Variance drivers\
- Deterministic narrative\
- AI analyst commentary _(if enabled)_\
- Citations

---

## 🌐 Production Deployment

### Frontend

- Hosted on **Vercel**
- Live URL:\
  👉 https://ai-financial-report-analyst-fawn.vercel.app

### Backend

- Hosted on **Render**
- Uses environment variables for secrets
- Free tier supported _(cold-start safe)_

---

## 🎯 Why This Project Stands Out

- Not a chatbot --- a financial analysis engine\
- Deterministic + AI hybrid _(enterprise-grade pattern)_\
- Fully auditable and citation-driven\
- Designed for real financial workflows\
- Clean separation of logic, AI, and UI\
- Production-safe by default

---

## 🧠 Key Engineering Learnings

Building this system required designing and shipping a production-grade
AI application, not a prototype. The work emphasized correctness,
explainability, and operational safety --- especially important in
financial and enterprise contexts.

### Key Takeaways

#### Designing hybrid AI systems (deterministic + LLM)

Implemented a numbers-first architecture where deterministic financial
logic computes results and LLMs provide optional, constrained
interpretation --- avoiding hallucinations and preserving auditability.

#### Applying Retrieval-Augmented Generation (RAG) with strict grounding

Built document-grounded AI responses using citation-based retrieval,
including heuristic filtering to exclude non-relevant financial
statements (e.g., cash flow and balance sheet) from analytical
explanations.

#### Enterprise-safe AI integration patterns

Designed AI features that degrade gracefully: - Core functionality
remains fully operational without an API key - LLM usage is isolated
behind service boundaries - Failures never break critical analysis
workflows

#### Financial variance analysis at scale

Implemented deterministic variance decomposition aligned with real
analyst workflows, ensuring full reconciliation, zero residuals, and
traceable driver attribution.

#### Backend system design and API hygiene

Structured a FastAPI backend with clear separation of concerns across
ingestion, parsing, analytics, retrieval, and AI services --- improving
testability and maintainability.

#### Production deployment and configuration management

Deployed a multi-service architecture using environment-based
configuration, secrets management, and cold-start-safe initialization
suitable for cloud platforms.

#### Explainability as a first-class requirement

Treated explainability and traceability as core system constraints, not
optional features --- aligning the system with enterprise compliance and
review expectations.

---

## 📌 Future Enhancements

- Improve AI / deterministic toggle UX\
- Support cash flow & balance sheet variance\
- Multi-period trend analysis\
- Export analyst reports (PDF)\
- Role-based access (enterprise)

---

## 👨‍💻 Author

**Ahmeduddin Mohammed**\
Focused on AI systems, data engineering, and applied financial
intelligence.
