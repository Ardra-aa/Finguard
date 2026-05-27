# FinGuard-RAG

**A Secure, Policy-Aware RAG Framework for Indian Financial Compliance**

> NLP 22AIE315 — Amrita Vishwa Vidyapeetham, Amritapuri  
> Guide: Dr. Veena G | Version 3.0 — April 2026

---

## Overview

FinGuard-RAG is a domain-specialised Retrieval-Augmented Generation (RAG) framework built for the Indian financial and corporate compliance context. It addresses the severe limitations of generic RAG systems when deployed in regulated, multinational financial environments operating under Indian law.

**Core novelty:** The first framework to combine policy-aware retrieval + time-versioned indexing + neuro-symbolic compliance validation + role-inference leakage defence + jurisdiction-conflict resolution + AI agent orchestration — all in a single pipeline, contextualised for India.

### Fictional Deployment Context

**BharatFinServ Ltd.** — a fictional Indian financial MNC listed on BSE/NSE (Mumbai HQ, Bengaluru Tech Centre, GIFT City IFSC, Frankfurt EU subsidiary) regulated by SEBI, RBI, MCA, ICAI, IFSCA, MAS Singapore, and EU-ESMA.

---

## Team

| Member | Role | Student ID |
|--------|------|------------|
| **Devna Thunnan** | Secure Retrieval & Indexing (M1–M4) | AM.SC.U4AIE23031 |
| **Amala P Ansalem** | Generation, Validation & Agent (M5–M7) | AM.SC.U4AIE23015 |
| **Ardra M A** | Defense, Resolution & Evaluation (M8–M11) | AM.SC.U4AIE23021 |

---

## Architecture

FinGuard-RAG is built as a six-stage layered pipeline:

```
USER INPUT (query + role + jurisdiction + session_id)
    ↓
Stage 0 — FinGuard AI Agent (ReAct Orchestrator)
    ↓
Stage 1 — Policy-Aware Pre-Filter (RBAC + jurisdiction + temporal)
    ↓
Stage 2 — Time-Versioned Retrieval (ChromaDB metadata filtering)
    ↓
Stage 3 — Risk-Aware Retrieval Scorer (α·semantic − β·risk)
    ↓
Stage 4 — LLM Generation (Gemini 1.5 Flash + structured prompt)
    ↓
Stage 5 — Compliance-Verified Generation (symbolic + neural)
    ↓
Stage 6 — Defence Layer (leakage detection + conflict resolution)
    ↓
FINAL RESPONSE → answer + citations + compliance_status
               + conflict_notices + leakage_risk
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **LLM** | Google Gemini 1.5 Flash (free via AI Studio) |
| **LLM Fallback** | Groq API (Llama 3 70B) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (local, 384-dim) |
| **Vector DB** | ChromaDB (persistent local) |
| **RAG Orchestration** | LangChain + LangChain-Community |
| **Rule Engine** | Pure Python (custom deontic DSL — 20 rules) |
| **API** | FastAPI + Uvicorn |
| **Frontend** | React (Create React App) |
| **Agent** | LangChain AgentExecutor (ReAct) |
| **Evaluation** | RAGAS + pytest |

> **Why not OpenAI?** OpenAI requires billing information. Gemini 1.5 Flash via Google AI Studio is genuinely free — just sign in at [aistudio.google.com](https://aistudio.google.com).

---

## Repository Structure

```
finguard-rag/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── data/
│   ├── corpus/
│   │   ├── sebi/
│   │   ├── rbi/
│   │   ├── mca/
│   │   ├── icai/
│   │   ├── ifsca_mas/
│   │   └── synthetic/
│   │       ├── internal_policies/
│   │       └── synthetic_metadata.json
│   ├── regulators_metadata.json
│   ├── generate_synthetic_corpus.py
│   └── chroma_db/                   (auto-created, gitignored)
├── Finguard_rag/
│   ├── __init__.py
│   ├── schemas/
│   │   ├── document_schema.py       (shared data contracts)
│   │   └── response_schema.py       (response type re-exports)
│   ├── ingestion/                   DEVNA (M1)
│   ├── retrieval/                   DEVNA (M2, M3, M4)
│   │   └── interface.py             → retrieve()
│   ├── generation/                  AMALA (M5, M6)
│   │   └── interface.py             → generate()
│   ├── agent/                       AMALA (M7)
│   │   └── interface.py             → agent_run()
│   ├── defense/                     ARDRA (M8, M9)
│   │   └── interface.py             → defend()
│   └── api/                         ARDRA (M11)
│       └── main.py
├── tests/
├── evaluation/                      ARDRA (M10)
└── frontend/                        ARDRA (React app)
    ├── package.json
    └── src/
        ├── App.js
        ├── context/AuthContext.js
        ├── pages/
        ├── components/
        └── api/client.js
```

---

## Module Breakdown

| Module | Name | Owner | Key Files |
|--------|------|-------|-----------|
| **M1** | Document Ingestion & Corpus Builder | Devna | `ingestion/ingestor.py`, `chunker.py`, `embedder.py` |
| **M2** | Policy-Aware Pre-Filter | Devna | `retrieval/pre_filter.py`, `access_policy.py` |
| **M3** | Time-Versioned Retrieval | Devna | `retrieval/versioned_retriever.py`, `temporal_index.py` |
| **M4** | Risk-Aware Retrieval Scorer | Devna | `retrieval/risk_scorer.py` |
| **M5** | LLM Generation Module | Amala | `generation/generator.py`, `prompt_builder.py`, `gemini_client.py` |
| **M6** | Compliance-Verified Generation | Amala | `generation/compliance_validator.py`, `rule_engine.py`, `safety_classifier.py` |
| **M7** | FinGuard AI Agent | Amala | `agent/finguard_agent.py`, `tool_registry.py`, `agent_prompt.py` |
| **M8** | Role-Inference Leakage Detector | Ardra | `defense/leakage_detector.py`, `session_tracker.py`, `sensitivity_graph.py` |
| **M9** | Jurisdiction-Conflict Resolver | Ardra | `defense/conflict_resolver.py`, `jurisdiction_ontology.py` |
| **M10** | Evaluation Harness & Baselines | Ardra | `evaluation/run_eval.py`, `metrics.py`, `baselines.py` |
| **M11** | FastAPI Service + React Frontend | Ardra | `api/main.py`, `api/routes.py`, `frontend/` |

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/finguard-rag.git && cd finguard-rag

# Python environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Python dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
# Edit .env: add your GEMINI_API_KEY
# Free key at: aistudio.google.com (no credit card required)
```

### 3. Build Corpus & Index

```bash
# Generate synthetic BharatFinServ policy documents
python data/generate_synthetic_corpus.py

# Ingest all documents into ChromaDB
python Finguard_rag/ingestion/ingestor.py

# Verify
python -c "import chromadb; c=chromadb.PersistentClient(path='data/chroma_db'); print(f'Chunks: {c.get_collection(\"finguard_docs\").count()}')"
```

### 4. Run the Application

```bash
# Terminal 1 — Backend (FastAPI)
uvicorn Finguard_rag.api.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI)

# Terminal 2 — Frontend (React)
cd frontend && npm install && npm start
# → http://localhost:3000
# Login with any demo user. Password: demo
```

---

## Demo Users (BharatFinServ Roles)

| Role | Name | Jurisdictions | Password |
|------|------|---------------|----------|
| `ceo` | Rahul Sharma | IN, SG, EU, GLOBAL | demo |
| `cfo` | Priya Menon | IN, SG, EU, GLOBAL | demo |
| `compliance_officer` | Ananya Iyer | IN, SG, EU, GLOBAL | demo |
| `legal_counsel` | Vikram Nair | IN, SG, EU, GLOBAL | demo |
| `senior_analyst` | Sneha Pillai | IN, SG | demo |
| `junior_analyst` | Arjun Kumar | IN only | demo |
| `it_admin` | Kavya Reddy | IN only | demo |
| `auditor_external` | Deepak Rao | IN, GLOBAL | demo |

---

## Evaluation Metrics

| Metric | Target |
|--------|--------|
| Jurisdictional Correctness | ≥ 90% |
| Compliance Violation Rate | ≤ 5% |
| Temporal Accuracy | ≥ 95% |
| Leakage Detection Rate | ≥ 80% |
| Conflict Detection Rate | 100% |
| Answer Faithfulness (RAGAS) | ≥ 0.80 |
| End-to-End Latency (P95) | ≤ 8 sec |

---

## Integration Contract

All inter-module communication uses the typed schemas defined in `Finguard_rag/schemas/document_schema.py`. Each module exposes an `interface.py` with `mock_mode=True` support for independent development and testing.

```python
# Retrieval → retrieve(query, user_context, top_k, mock_mode) → List[RankedDocument]
# Generation → generate(query, docs, user_context, mock_mode) → ComplianceResponse
# Agent     → agent_run(query, user_context, mock_mode) → AgentResponse
# Defense   → defend(session_id, query, response, user_context, mock_mode) → DefenseResult
```

---

## Branching Strategy

```
main                              ← protected; reviewed PRs only
└── dev                           ← integration branch
    ├── feature/shared/schemas
    ├── feature/devna/ingestion
    ├── feature/devna/retrieval
    ├── feature/amala/generation
    ├── feature/amala/agent
    ├── feature/ardra/defense
    ├── feature/ardra/evaluation
    └── feature/ardra/frontend
```

---

## License

Academic project — Amrita Vishwa Vidyapeetham, Amritapuri. For educational purposes only.
