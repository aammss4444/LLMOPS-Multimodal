# Multimodal LLMOps - Project Documentation

## 1. Project Overview

`Multimodal LLMOps` is a Python-based backend initiative for auditing video content against compliance/policy requirements using multimodal inputs.

Primary workspace:
`D:\Projects\Multimodal_LLMOPS`

Primary goal:
- Ingest video input
- Extract transcript and OCR/text signals
- Run LLM/RAG-based compliance checks
- Produce structured compliance issues and final report

Current phase:
- Early implementation with working state schema and partial graph-node logic.

## 2. Latest Architecture Snapshot

### 2.1 Layered design

1. API layer (`backend/src/api/`)
- Intended FastAPI service entrypoint and telemetry hooks.
- Current files exist but are not implemented yet.

2. Graph orchestration layer (`backend/src/graph/`)
- Core of the processing workflow.
- `state.py` defines shared execution state (`VideoAuditState`).
- `nodes.py` contains partial node logic for indexing and content auditing.
- `workflow.py` defines graph edges and execution order.

3. Services layer (`backend/src/services/`)
- Intended for concrete external integrations (e.g., Azure Video Indexer adapter).
- Files exist; implementation pending.

4. Scripts layer (`backend/scripts/`)
- Intended operational tasks such as indexing/ingestion scripts.
- Current script file is placeholder.

5. Data layer (`backend/data/`)
- Source policy/reference documents currently stored as PDFs.

6. Test layer (`backend/tests/`)
- Reserved for unit/integration tests.

### 2.2 Workflow intent (from current code)

Target pipeline represented in `workflow.py`:
- `index_video` -> `audio_content_audit` -> `visual_compliance_audit` -> `END`

The graph is intended to use `VideoAuditState` across all transitions.

## 3. Code Status (Latest)

### 3.1 Implemented or partially implemented

- `backend/src/graph/state.py`
  - Defines `ComplianceIssue` and `VideoAuditState` `TypedDict` schemas.
  - Uses `Annotated[List[...], operator.add]` for aggregating issues/errors across nodes.

- `backend/src/graph/nodes.py`
  - Contains partial node implementation:
    - `index_video_node(...)`: download/upload/extract flow shape with logging and error handling.
    - `audio_content_node(...)`: partial LLM and embeddings setup for compliance audit.
  - Includes references to Azure OpenAI + Azure Search style RAG setup.

- `backend/src/graph/workflow.py`
  - Declares LangGraph assembly and directed edges for the compliance flow.

### 3.2 Placeholder/empty modules

- `backend/src/api/server.py`
- `backend/src/api/telementry.py`
- `backend/src/services/video_indexer.py`
- `backend/scripts/index_document.py`
- `backend/src/services/__init__.py`
- `backend/src/graph/__init__.py`

## 4. Tools and Technologies Used

## 4.1 Core runtime/tooling

- Python `>=3.12`
- `uv` for dependency and lock management (`pyproject.toml`, `uv.lock`)
- Virtual environment in `.venv/`

### 4.2 Backend and orchestration

- `fastapi`
- `uvicorn`
- `langgraph`
- `langchain`
- `langchain-community`
- `langchain-openai`
- `langchain-google-genai`
- `langsmith`

### 4.3 Cloud, observability, and integrations

- `azure-identity`
- `azure-storage-blob`
- `azure-search-documents`
- `azure-monitor-opentelemetry`
- `opentelemetry-instrumentation-fastapi`

### 4.4 Data, retrieval, and utility stack

- `pandas`
- `pypdf`
- `yt-dlp`
- `firecrawl-py`
- `requests`
- `python-dotenv`
- `pydantic`
- `redis`
- `sqlalchemy`
- `psycopg2-binary`
- `streamlit`

## 5. Current File Map

```text
D:\Projects\Multimodal_LLMOPS
|-- .env.example
|-- .gitignore
|-- .python-version
|-- README.md
|-- PROJECT_DOCUMENTATION.md
|-- main.py
|-- pyproject.toml
|-- uv.lock
`-- backend/
    |-- data/
    |   |-- 1001a-influencer-guide-508_1.pdf
    |   `-- youtube-ad-specs.pdf
    |-- scripts/
    |   `-- index_document.py
    |-- src/
    |   |-- api/
    |   |   |-- server.py
    |   |   `-- telementry.py
    |   |-- graph/
    |   |   |-- __init__.py
    |   |   |-- nodes.py
    |   |   |-- state.py
    |   |   `-- workflow.py
    |   `-- services/
    |       |-- __init__.py
    |       `-- video_indexer.py
    `-- tests/
```

## 6. Configuration and Environment Variables

Values are defined by `.env` (template in `.env.example`).

### 6.1 LLM and embeddings

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `GEMINI_API_KEY`

### 6.2 Search and knowledge base

- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `AZURE_SEARCH_INDEX_NAME`

### 6.3 Video indexer and Azure infra

- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_VI_NAME`
- `AZURE_VI_LOCATION`
- `AZURE_VI_ACCOUNT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`

### 6.4 Tracing and monitoring

- `APPLICATIONSINIGHTS_CONNECTION_STRING`
- `LANGCHAIN_TRACING_V2`
- `LANGCHAIN_ENDPOINT`
- `LANGCHAIN_API_KEY`
- `LANCHAIN_PROJECT_NAME`

## 7. Known Gaps and Risks

- `nodes.py` currently has unresolved import/reference mismatches (for example naming/casing mismatches and missing symbols), so end-to-end execution is not yet stable.
- `workflow.py` references node function names that differ from currently implemented names in `nodes.py`.
- API/server and service adapter modules are not yet implemented.
- No automated tests are present yet.

## 8. Recommended Next Steps

1. Stabilize graph execution:
- Align function names between `nodes.py` and `workflow.py`.
- Fix imports for Azure OpenAI classes and complete node return schemas.

2. Implement service adapters:
- Build `VideoIndexerService` in `backend/src/services/video_indexer.py`.

3. Build API entrypoint:
- Implement `backend/src/api/server.py` with health and audit trigger endpoints.

4. Add observability wiring:
- Implement telemetry setup in `backend/src/api/telementry.py`.

5. Add tests:
- Unit tests for state/node behavior.
- Integration test for workflow compile/execute path.

6. Add developer docs:
- Local runbook (dev setup, env variables, troubleshooting).
- API contract examples (request/response payloads).
