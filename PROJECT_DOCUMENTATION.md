# Multimodal_LLMOPS - Project Documentation

## 1) Project Overview

`Multimodal_LLMOPS` is a Python-based scaffold for a multimodal LLMOps backend.  
Current implementation status is early-stage: directory structure and dependencies are defined, while most backend modules are placeholders (empty files).

Primary workspace path:

`D:\Projects\Multimodal_LLMOPS`

## 2) Architecture (Current + Intended)

### Current architecture state

- Root-level Python project configured with `pyproject.toml` and `uv.lock`.
- Backend code separated under `backend/`.
- API, graph/workflow, and services layers are present as folders/files but currently unimplemented.
- Document assets (PDFs) are stored in `backend/data/`.

### Intended logical architecture (based on structure)

1. API Layer (`backend/src/api/`)
   - Hosts FastAPI server endpoints.
   - Exposes interfaces for ingestion and query workflows.
2. Workflow/Orchestration Layer (`backend/src/graph/`)
   - LangGraph/LangChain-based nodes and state transitions.
   - Coordinates multimodal processing pipeline.
3. Service Layer (`backend/src/services/`)
   - External service adapters (e.g., indexing, retrieval, storage integrations).
4. Data/Assets Layer (`backend/data/`)
   - Source documents/media used for indexing and retrieval experiments.
5. Scripts Layer (`backend/scripts/`)
   - Operational scripts (e.g., indexing jobs, ingestion utilities).
6. Tests Layer (`backend/tests/`)
   - Unit/integration tests for API, graph nodes, and services.

## 3) Frameworks & Technologies Used

From `pyproject.toml` dependencies:

### Backend framework

- `FastAPI`
- `Uvicorn`

### LLM / orchestration

- `langchain`
- `langchain-community`
- `langchain-openai`
- `langgraph`
- `langsmith`

### Data / document processing

- `pandas`
- `pypdf`
- `yt-dlp`
- `firecrawl-py`

### Cloud / search / storage / observability

- `azure-identity`
- `azure-search-documents`
- `azure-storage-blob`
- `azure-monitor-opentelemetry`
- `opentelemetry-instrumentation-fastapi`

### Database / caching / HTTP / config

- `sqlalchemy`
- `psycopg2-binary` (PostgreSQL driver)
- `redis`
- `requests`
- `python-dotenv`
- `pydantic`

## 4) Tooling Used in Project

### Package & environment management

- `uv` (lock file: `uv.lock`)
- Virtual environment in `.venv/`

### Python runtime

- Python `>=3.12` (from `pyproject.toml`)
- `.python-version` present

### Project metadata/config

- `pyproject.toml` as primary project/dependency config

## 5) Directory and File Map

```text
D:\Projects\Multimodal_LLMOPS
|-- .env
|-- .python-version
|-- main.py
|-- pyproject.toml
|-- README.md
|-- uv.lock
|-- PROJECT_DOCUMENTATION.md
|-- .venv\                             # local virtual environment
`-- backend\
    |-- data\
    |   |-- 1001a-influencer-guide-508_1.pdf
    |   `-- youtube-ad-specs.pdf
    |-- scripts\
    |   `-- index_document.py
    |-- src\
    |   |-- api\
    |   |   |-- server.py
    |   |   `-- telementry.py
    |   |-- graph\
    |   |   |-- __init__.py
    |   |   |-- nodes.py
    |   |   |-- state.py
    |   |   `-- workflow.py
    |   `-- services\
    |       |-- __init__.py
    |       `-- video_indexer.py
    `-- tests\
```

## 6) Module Status Notes

Current files with implementation content:

- `main.py` (simple hello-world entrypoint)

Current placeholder/empty files:

- `backend/scripts/index_document.py`
- `backend/src/api/server.py`
- `backend/src/api/telementry.py`
- `backend/src/graph/nodes.py`
- `backend/src/graph/state.py`
- `backend/src/graph/workflow.py`
- `backend/src/services/video_indexer.py`
- `backend/src/services/__init__.py`
- `backend/src/graph/__init__.py`

## 7) Suggested Next Build Steps

1. Implement `backend/src/api/server.py` with a minimal FastAPI app and health endpoint.
2. Define graph state model in `backend/src/graph/state.py` using Pydantic.
3. Add first runnable node(s) in `backend/src/graph/nodes.py` and compile graph in `workflow.py`.
4. Implement indexing pipeline in `backend/scripts/index_document.py`.
5. Add tests under `backend/tests/` for API and workflow modules.

