# FinGuard-RAG

**A Secure, Policy-Aware RAG Framework for Indian Financial Compliance**

> NLP Amrita Vishwa Vidyapeetham, Amritapuri

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Key Features](#key-features)
4. [System Architecture](#system-architecture)
5. [Pipeline Walkthrough](#pipeline-walkthrough)
6. [Technology Stack](#technology-stack)
7. [Repository Structure](#repository-structure)
8. [Module Breakdown](#module-breakdown)
9. [Team](#team)
10. [Quick Start](#quick-start)
11. [Demo Users](#demo-users-bharatfinserv-roles)
12. [Integration Contract](#integration-contract)
13. [Testing](#testing)
14. [Evaluation Metrics](#evaluation-metrics)
15. [License](#license)

---

## Overview

FinGuard-RAG is a domain-specialised Retrieval-Augmented Generation (RAG) framework built for the Indian financial and corporate compliance context. It addresses the severe limitations of generic RAG systems when deployed in regulated, multinational financial environments operating under Indian law.

Generic RAG systems lack role-based access control, temporal document versioning, compliance validation of generated answers, cross-role data leakage detection, and jurisdiction-conflict resolution. FinGuard-RAG addresses all of these in a single, integrated pipeline.

**Core Novelty:** The first framework to combine policy-aware retrieval + time-versioned indexing + neuro-symbolic compliance validation + role-inference leakage defence + jurisdiction-conflict resolution + AI agent orchestration -- all in a single pipeline, contextualised for India.

### Fictional Deployment Context

**BharatFinServ Ltd.** -- a fictional Indian financial MNC listed on BSE/NSE (Mumbai HQ, Bengaluru Tech Centre, GIFT City IFSC, Frankfurt EU subsidiary) regulated by SEBI, RBI, MCA, ICAI, IFSCA, MAS Singapore, and EU-ESMA.

---

## Problem Statement

Financial institutions in India operate under a complex web of regulators (SEBI, RBI, MCA, ICAI, IFSCA) with overlapping and sometimes conflicting requirements. A compliance officer answering a question about "related party transactions" must simultaneously consider:

- **Role-based access**: A junior analyst must NOT see executive salary data
- **Temporal versioning**: Only the latest, non-superseded regulation version should be cited
- **Jurisdiction conflicts**: An entity operating in both India (Ind AS 116) and Singapore (MAS Notice 637) may face conflicting capital adequacy requirements
- **Data leakage**: A series of seemingly innocent queries by a junior analyst could be combined to reconstruct restricted salary band information
- **Compliance validation**: The generated answer itself must not contain advice that violates SEBI, RBI, or MCA rules

FinGuard-RAG solves all five problems in a unified pipeline.

---

## Key Features

### 1. Policy-Aware Retrieval (Modules M1-M4)
- **RBAC Pre-Filtering**: Documents are tagged with `valid_roles`. A junior analyst never sees CEO-only salary documents, even if they are semantically relevant.
- **Jurisdiction Filtering**: Documents are tagged with jurisdiction codes (IN, SG, EU, GLOBAL). Users only see documents relevant to their jurisdiction.
- **Temporal Versioning**: Only documents with `effective_date <= today` and `superseded_date = None` (or future) are returned.
- **Risk-Aware Scoring**: Final document ranking uses the formula `alpha * semantic_score - beta * risk_score`, penalising high-risk documents.

### 2. LLM Generation with Structured Prompts (Module M5)
- **Gemini 2.5 Flash** as primary LLM (free via Google AI Studio, no credit card required)
- **Groq API (Llama 3 70B)** as automatic fallback if Gemini fails
- **Structured prompt** with three sections: SYSTEM (persona + rules), CONTEXT (retrieved document chunks), QUERY (user question + metadata)
- **Mandatory citation format**: Every factual claim must end with `[Source: doc_id]`
- **Token budget management**: Input capped at 8,192 tokens with automatic context trimming

### 3. Neuro-Symbolic Compliance Validation (Module M6)
- **Layer A -- Symbolic Rule Engine**: 20 hand-crafted deontic rules across SEBI, RBI, MCA, and Ind AS regulations. Each rule has a modality (MUST / MUST_NOT / PERMITTED) and regex patterns. A MUST_NOT violation triggers an automatic FAIL and the response is withheld.
- **Layer B -- Neural Safety Classifier**: Uses sentence-transformers (all-MiniLM-L6-v2) to compute cosine similarity between the generated answer and a library of known non-compliant patterns. Score >= 0.82 triggers a WARNING; score >= 0.92 triggers HIGH risk.

### 4. Role-Inference Leakage Detection (Module M8)
- **Cross-Role Salary Inference**: Detects when a restricted role (e.g., junior_analyst) asks about salary/compensation data that is restricted to CEO/CFO/HR.
- **Query-Level Sensitivity Detection**: Fires BEFORE document retrieval. Even if all salary documents are RBAC-blocked, the query intent itself is flagged.
- **Session-Level Tracking**: Tracks all queries within a session using a singleton SessionTracker. A graph-based analysis detects patterns of escalating sensitivity across multiple queries.
- **Embedding-Based Analysis**: Uses sentence-transformers to compute query embeddings and build a sensitivity graph for cross-query inference detection.

### 5. Jurisdiction-Conflict Resolution (Module M9)
- **Ontology-Based Detection**: A jurisdiction ontology defines known conflict patterns (e.g., Ind AS 116 vs IFRS 16 lease treatment, IN vs SG capital adequacy ratios).
- **Conservative Recommendation**: When a conflict is detected, the system provides a conservative recommendation (e.g., "apply the stricter of the two requirements").
- **Automatic Status Escalation**: If a conflict is detected and compliance_status is PASS, it is automatically escalated to WARNING.

### 6. FastAPI Backend + React Frontend (Module M11)
- **FastAPI** with full Swagger/OpenAPI documentation at `/docs`
- **React** frontend with role-based login, compliance query interface, and admin session dashboard
- **Real-time compliance badges**: PASS (green), WARNING (amber), FAIL (red)
- **Source citations, conflict notices, and leakage alerts** displayed inline

---

## System Architecture

FinGuard-RAG is built as a six-stage layered pipeline:

```
USER INPUT (query + role + jurisdiction + session_id)
    |
    v
Stage 0 -- Defence Pre-Check (M8 Leakage Detection)
    |   Query blocked if HIGH leakage risk detected
    v
Stage 1 -- Policy-Aware Pre-Filter (M2: RBAC + jurisdiction + temporal)
    |   Documents filtered by role, jurisdiction, and effective date
    v
Stage 2 -- Time-Versioned Retrieval (M3: ChromaDB metadata filtering)
    |   ChromaDB vector search with metadata constraints
    v
Stage 3 -- Risk-Aware Retrieval Scorer (M4: alpha*semantic - beta*risk)
    |   Documents re-ranked by combined relevance and risk score
    v
Stage 4 -- LLM Generation (M5: Gemini 2.5 Flash + structured prompt)
    |   Prompt assembled with SYSTEM, CONTEXT, QUERY sections
    v
Stage 5 -- Compliance Validation (M6: Layer A symbolic + Layer B neural)
    |   FAIL -> response withheld; WARNING -> flagged; PASS -> approved
    v
Stage 6 -- Defence Post-Check (M8 + M9: leakage + conflict resolution)
    |   Final leakage check on generated answer + conflict detection
    v
FINAL RESPONSE
    -> answer + citations + compliance_status
    -> conflict_notices + leakage_risk + confidence_score
```

---

## Pipeline Walkthrough

### Step-by-Step Flow for a Single Query

1. **User submits a query** through the React frontend (e.g., "What are SEBI LODR disclosure requirements?") with their role (e.g., `compliance_officer`) and jurisdiction (e.g., `IN`).

2. **Defence Pre-Check (M8)**: Before any document retrieval, the leakage detector checks the raw query text against sensitive patterns (salary, ESOP, bonus, compensation). If the user's role is restricted and the query targets sensitive data, the query is blocked with HTTP 403 immediately.

3. **Document Retrieval**: The `_select_docs()` function filters the document corpus by:
   - Role access: Only documents where the user's role is in `valid_roles`
   - Jurisdiction: Documents matching the user's jurisdiction (plus GLOBAL)
   - Temporal: Only non-superseded documents with `effective_date <= today`
   - Keyword relevance: Substring matching with scope-specific boosting

4. **LLM Generation (M5)**: The `prompt_builder.build_prompt()` assembles a structured prompt with the top 5 documents as context. `gemini_client.call_llm()` sends this to Gemini 2.5 Flash. If Gemini fails, it falls back to Groq (Llama 3 70B).

5. **Compliance Validation (M6)**: The generated answer is validated through:
   - **Layer A (Symbolic)**: 20 deontic rules check for violations (e.g., "recommend insider trading" matches SEBI_001 MUST_NOT rule)
   - **Layer B (Neural)**: Cosine similarity against known non-compliant patterns
   - If FAIL: The answer is replaced with a safe refusal message

6. **Defence Post-Check (M8 + M9)**: After generation:
   - M8 re-checks the full (query + response + source_docs) for leakage
   - M9 checks for jurisdiction conflicts in the cited documents
   - If HIGH leakage is detected, the response is blocked
   - If a conflict is detected, compliance_status is escalated to WARNING

7. **Response returned** to the frontend with: answer, sources, compliance_status, violations, leakage_risk, conflict_detected, conflicting_rules, conservative_recommendation, and confidence_score.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.11+ | Backend logic |
| **LLM (Primary)** | Google Gemini 2.5 Flash | Answer generation (free via AI Studio) |
| **LLM (Fallback)** | Groq API (Llama 3 70B) | Automatic fallback if Gemini fails |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 | Document + query embeddings (local, 384-dim) |
| **Vector DB** | ChromaDB (persistent local) | Vector storage and similarity search |
| **RAG Framework** | LangChain + LangChain-Community | Document loading, text splitting |
| **Rule Engine** | Pure Python (custom deontic DSL) | 20 compliance rules (SEBI, RBI, MCA, Ind AS) |
| **Neural Safety** | sentence-transformers cosine similarity | Non-compliant pattern detection |
| **API** | FastAPI + Uvicorn | REST API with auto-generated docs |
| **Frontend** | React (Create React App) | User interface |
| **Agent** | LangChain AgentExecutor (ReAct) | Multi-step reasoning orchestration |
| **Testing** | pytest (179 tests) | Unit, integration, API, and role tests |
| **Evaluation** | RAGAS + custom metrics | RAG quality evaluation |

> **Why not OpenAI?** OpenAI requires billing information. Gemini 2.5 Flash via Google AI Studio is genuinely free -- just sign in at [aistudio.google.com](https://aistudio.google.com).

---

## Repository Structure

```
Finguard2/
|-- README.md                          # This file
|-- DEMO_GUIDELINES.md                 # Demo walkthrough and test cases
|-- requirements.txt                   # Python dependencies
|-- config.yaml                        # Runtime configuration
|-- .env.example                       # Environment variable template
|-- .gitignore
|-- start.bat                          # One-click Windows startup script
|
|-- Finguard_rag/                      # Main Python package
|   |-- __init__.py
|   |-- schemas/
|   |   |-- document_schema.py         # Shared data contracts (6 dataclasses)
|   |   +-- response_schema.py         # Response type re-exports
|   |-- ingestion/                     # M1: Document Ingestion
|   |   |-- ingestor.py                # ChromaDB ingestion pipeline
|   |   |-- chunker.py                 # Text splitting (512 tokens, 50 overlap)
|   |   |-- embedder.py                # Sentence-transformer embeddings
|   |   +-- metadata_extractor.py      # Metadata JSON loader
|   |-- retrieval/                     # M2-M4: Retrieval Pipeline
|   |   |-- interface.py               # Public API: retrieve()
|   |   |-- pre_filter.py              # RBAC + jurisdiction + temporal filter
|   |   |-- versioned_retriever.py     # ChromaDB time-versioned search
|   |   +-- risk_scorer.py             # Risk-aware document re-ranking
|   |-- generation/                    # M5-M6: Generation + Validation
|   |   |-- interface.py               # Public API: generate()
|   |   |-- generator.py               # LLM answer generation
|   |   |-- prompt_builder.py          # Structured prompt assembly
|   |   |-- gemini_client.py           # Gemini API + Groq fallback
|   |   |-- compliance_validator.py    # M6 orchestrator (Layer A + B)
|   |   |-- rule_engine.py             # Layer A: 20 deontic rules
|   |   +-- safety_classifier.py       # Layer B: neural safety classifier
|   |-- agent/                         # M7: AI Agent
|   |   |-- interface.py               # Public API: agent_run()
|   |   |-- finguard_agent.py          # ReAct agent logic
|   |   |-- tool_registry.py           # LangChain tool definitions
|   |   +-- agent_prompt.py            # Agent system prompt
|   |-- defense/                       # M8-M9: Defence Layer
|   |   |-- interface.py               # Public API: defend()
|   |   |-- leakage_detector.py        # M8: Role-inference leakage detection
|   |   |-- session_tracker.py         # In-memory session store (singleton)
|   |   |-- sensitivity_graph.py       # Graph-based leakage analysis
|   |   |-- conflict_resolver.py       # M9: Jurisdiction-conflict resolver
|   |   +-- jurisdiction_ontology.py   # Conflict pattern definitions
|   +-- api/                           # M11: FastAPI Service
|       |-- main.py                    # App entry point
|       |-- routes.py                  # Route handlers + mock corpus
|       +-- models.py                  # Pydantic request/response models
|
|-- frontend/                          # React Frontend (M11)
|   |-- package.json
|   +-- src/
|       |-- App.js                     # Shell with navigation
|       |-- index.js                   # React entry point
|       |-- context/AuthContext.js      # Authentication context + demo users
|       |-- pages/
|       |   |-- LoginPage.js           # Demo user selection
|       |   |-- QueryPage.js           # Compliance query interface
|       |   +-- AdminPage.js           # Session monitoring dashboard
|       |-- components/index.js        # Shared UI components
|       +-- api/client.js              # HTTP client for backend API
|
|-- tests/                             # Comprehensive test suite (179 tests)
|   |-- unit/                          # 122 unit tests
|   |   |-- test_schemas.py
|   |   |-- test_chunker.py
|   |   |-- test_pre_filter.py
|   |   |-- test_risk_scorer.py
|   |   |-- test_rule_engine.py
|   |   |-- test_leakage_detector.py
|   |   |-- test_session_tracker.py
|   |   |-- test_prompt_builder.py
|   |   |-- test_jurisdiction_ontology.py
|   |   |-- test_conflict_resolver.py
|   |   +-- test_metadata_extractor.py
|   |-- integration/                   # 30 integration tests
|   |   |-- test_pipelines.py
|   |   +-- test_pipeline_mock.py
|   |-- api/                           # 7 API tests
|   |   +-- test_endpoints.py
|   +-- roles/                         # 19 role + edge case tests
|       +-- test_all_roles.py
|
|-- evaluation/                        # M10: Evaluation Harness
|   |-- run_eval.py
|   |-- metrics.py
|   +-- baselines.py
|
+-- data/                              # Document Corpus
    |-- corpus/
    |   |-- sebi/                      # SEBI regulatory PDFs
    |   |-- rbi/                       # RBI master directions
    |   |-- mca/                       # Companies Act documents
    |   |-- icai/                      # Ind AS standards
    |   |-- ifsca_mas/                 # IFSCA/MAS Singapore docs
    |   +-- synthetic/                 # Synthetic BharatFinServ policies
    |       |-- internal_policies/
    |       +-- synthetic_metadata.json
    |-- regulators_metadata.json
    |-- generate_synthetic_corpus.py
    +-- chroma_db/                     # Auto-created, gitignored
```

---

## Module Breakdown

### Retrieval Pipeline (Devna Thunnan)

| Module | Name | Key Files | Description |
|--------|------|-----------|-------------|
| **M1** | Document Ingestion | `ingestion/ingestor.py`, `chunker.py`, `embedder.py` | Reads PDFs and TXTs, chunks them (512 tokens, 50 overlap), generates embeddings via all-MiniLM-L6-v2, and stores in ChromaDB with metadata. |
| **M2** | Policy-Aware Pre-Filter | `retrieval/pre_filter.py` | Filters documents by RBAC role, jurisdiction code, and temporal validity before vector search. |
| **M3** | Time-Versioned Retrieval | `retrieval/versioned_retriever.py` | Queries ChromaDB with metadata filters for `effective_date` and `superseded_date`. |
| **M4** | Risk-Aware Scorer | `retrieval/risk_scorer.py` | Re-ranks results using `alpha * semantic_score - beta * risk_score`. High-risk documents are penalised. |

### Generation Pipeline (Amala P Ansalem)

| Module | Name | Key Files | Description |
|--------|------|-----------|-------------|
| **M5** | LLM Generation | `generation/generator.py`, `prompt_builder.py`, `gemini_client.py` | Builds structured prompts with context injection and calls Gemini 2.5 Flash (or Groq fallback). |
| **M6** | Compliance Validation | `generation/compliance_validator.py`, `rule_engine.py`, `safety_classifier.py` | Two-layer validation: Layer A (20 symbolic deontic rules) + Layer B (neural cosine similarity). |
| **M7** | FinGuard AI Agent | `agent/finguard_agent.py`, `tool_registry.py` | LangChain ReAct agent for multi-step compliance reasoning. |

### Defence Pipeline (Ardra M A)

| Module | Name | Key Files | Description |
|--------|------|-----------|-------------|
| **M8** | Leakage Detector | `defense/leakage_detector.py`, `session_tracker.py`, `sensitivity_graph.py` | Detects cross-role salary inference attacks and query-level sensitivity. |
| **M9** | Conflict Resolver | `defense/conflict_resolver.py`, `jurisdiction_ontology.py` | Detects jurisdiction conflicts and provides conservative recommendations. |
| **M10** | Evaluation Harness | `evaluation/run_eval.py`, `metrics.py`, `baselines.py` | RAGAS-based evaluation with custom compliance metrics. |
| **M11** | FastAPI + React | `api/main.py`, `api/routes.py`, `frontend/` | REST API and web frontend with role-based login. |

---

## Team

| Member | Role | Student ID |
|--------|------|------------|
| **Devna Thunnan** | Secure Retrieval and Indexing (M1-M4) | AM.SC.U4AIE23031 |
| **Amala P Ansalem** | Generation, Validation and Agent (M5-M7) | AM.SC.U4AIE23015 |
| **Ardra M A** | Defense, Resolution and Evaluation (M8-M11) | AM.SC.U4AIE23021 |

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/your-org/finguard-rag.git && cd finguard-rag

# Create Python virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
# Free key at: aistudio.google.com (no credit card required)
```

### 3. Build Corpus and Index (Optional)

```bash
# The synthetic corpus (27 policy/regulation files) is pre-built in
# data/corpus/synthetic/internal_policies/. No generation step needed.

# Ingest all documents into ChromaDB
python Finguard_rag/ingestion/ingestor.py

# Verify chunk count
python -c "import chromadb; c=chromadb.PersistentClient(path='data/chroma_db'); print(f'Chunks: {c.get_collection(\"finguard_docs\").count()}')"
```

> Note: The app includes a built-in mock corpus in `routes.py` that works
> without ChromaDB ingestion. You can skip this step for demo purposes.

### 4. Run the Application

```bash
# Terminal 1 -- Backend (FastAPI)
uvicorn Finguard_rag.api.main:app --reload --port 8000
# Open http://localhost:8000/docs for Swagger UI

# Terminal 2 -- Frontend (React)
cd frontend && npm ci --ignore-scripts && npm start
# Open http://localhost:3000
# Login with any demo user
```

### 5. Run Tests

```bash
# Full test suite (179 tests)
python -m pytest tests/unit/ tests/integration/ tests/api/ tests/roles/ -v --tb=short

# Unit tests only
python -m pytest tests/unit/ -v

# Role-based tests only
python -m pytest tests/roles/ -v
```

---

## Demo Users (BharatFinServ Roles)

| # | Name | Role | Jurisdiction | Email | Access Level |
|---|------|------|-------------|-------|-------------|
| 1 | Arjun Kumar | `junior_analyst` | IN | arjun.kumar@bharatfinserv.in | SEBI public docs only. No salary/compensation data. |
| 2 | Priya Sharma | `senior_analyst` | IN | priya.sharma@bharatfinserv.in | SEBI + some RBI/MCA docs. No salary data. |
| 3 | Rajesh Patel | `compliance_officer` | IN | rajesh.patel@bharatfinserv.in | Full regulatory access. No salary data. |
| 4 | Aisha Nair | `legal_counsel` | IN | aisha.nair@bharatfinserv.in | Full regulatory access. No salary data. |
| 5 | Vikram Singh | `cfo` | IN | vikram.singh@bharatfinserv.in | Full access including salary/compensation. |
| 6 | Sunita Rao | `ceo` | IN | sunita.rao@bharatfinserv.in | Full access including salary/compensation. |
| 7 | Li Wei | `senior_analyst` | SG | li.wei@bharatfinserv.sg | IN + SG jurisdiction documents. |
| 8 | Hans Mueller | `compliance_officer` | EU | hans.mueller@bharatfinserv.eu | IN + EU jurisdiction documents. |

---

## Integration Contract

All inter-module communication uses the typed schemas defined in `Finguard_rag/schemas/document_schema.py`. Each module exposes an `interface.py` with `mock_mode=True` support for independent development and testing.

### Public APIs

```python
# Retrieval (M1-M4)
from Finguard_rag.retrieval.interface import retrieve
docs = retrieve(query, user_context, top_k=5, mock_mode=False)
# Returns: List[RankedDocument]

# Generation (M5-M6)
from Finguard_rag.generation.interface import generate
response = generate(query, docs, user_context, mock_mode=False)
# Returns: ComplianceResponse

# Agent (M7)
from Finguard_rag.agent.interface import agent_run
result = agent_run(query, user_context, mock_mode=False)
# Returns: AgentResponse

# Defense (M8-M9)
from Finguard_rag.defense.interface import defend
defense_result = defend(session_id, user_id, role, query, response, source_docs, user_context)
# Returns: dict with leakage_risk, conflict_detected, etc.
```

### Shared Data Contracts

| Dataclass | Fields | Used By |
|-----------|--------|---------|
| `FinancialDocument` | doc_id, content, jurisdiction, regulatory_scope, valid_roles, effective_date, superseded_date, version, risk_level, risk_score, source_file | All modules |
| `UserContext` | user_id, role, jurisdiction, reference_date, session_id | All modules |
| `RankedDocument` | document, semantic_score, risk_score, final_score | Retrieval -> Generation |
| `ComplianceResponse` | answer, sources, compliance_status, violations, conflicts, leakage_risk, confidence_score, agent_trace | Generation -> API |
| `DefenseResult` | leakage_risk, leakage_details, conflict_detected, conflicting_rules, conservative_recommendation | Defense -> API |
| `AgentResponse` | final_response, agent_trace, total_iterations | Agent -> API |

---

## Testing

The project includes a comprehensive test suite with **179 tests** across 4 categories:

| Category | Directory | Tests | Coverage |
|----------|-----------|-------|----------|
| **Unit** | `tests/unit/` | 122 | All individual functions: schemas, chunker, pre_filter, risk_scorer, rule_engine, leakage_detector, session_tracker, prompt_builder, jurisdiction_ontology, conflict_resolver, metadata_extractor |
| **Integration** | `tests/integration/` | 30 | End-to-end pipeline flows: retrieval, generation, defense, cross-module integration |
| **API** | `tests/api/` | 7 | FastAPI endpoints: /health, /query, /sessions, validation errors, salary blocking |
| **Roles** | `tests/roles/` | 19 | All 8 demo users + edge cases: empty query, long query, special characters, SQL injection, prompt injection |

### Running Tests

```bash
# Full suite
python -m pytest tests/unit/ tests/integration/ tests/api/ tests/roles/ -v --tb=short

# Expected output: 178 passed, 1 skipped (the /sessions endpoint skip is expected)
```

---

## Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Jurisdictional Correctness | >= 90% | Answers cite correct jurisdiction regulations |
| Compliance Violation Rate | <= 5% | Percentage of answers flagged by rule engine |
| Temporal Accuracy | >= 95% | Only current (non-superseded) documents cited |
| Leakage Detection Rate | >= 80% | Cross-role inference attacks detected |
| Conflict Detection Rate | 100% | Known jurisdiction conflicts flagged |
| Answer Faithfulness (RAGAS) | >= 0.80 | Answer grounded in retrieved context |
| End-to-End Latency (P95) | <= 8 sec | 95th percentile response time |

---

## Branching Strategy

```
main                              <-- protected; reviewed PRs only
+-- dev                           <-- integration branch
    |-- feature/shared/schemas
    |-- feature/devna/ingestion
    |-- feature/devna/retrieval
    |-- feature/amala/generation
    |-- feature/amala/agent
    |-- feature/ardra/defense
    |-- feature/ardra/evaluation
    +-- feature/ardra/frontend
```

---

## License

Academic project -- Amrita Vishwa Vidyapeetham, Amritapuri. For educational purposes only.
