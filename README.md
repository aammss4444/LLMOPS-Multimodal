# Multimodal LLMOps

Python backend project for multimodal video compliance auditing with LangGraph-based orchestration, Azure services, and LLM-driven analysis.

Project root: `D:\Projects\Multimodal_LLMOPS`

## Current Status

- Project scaffold is in place and dependencies are configured with `uv`.
- Graph state schema is implemented in `backend/src/graph/state.py`.
- Graph nodes and workflow are partially implemented in `backend/src/graph/nodes.py` and `backend/src/graph/workflow.py`.
- API, service, and indexing script modules still need implementation work.

## Tech Stack

- Runtime: Python 3.12+
- Package management: `uv` (`pyproject.toml`, `uv.lock`)
- API framework: FastAPI + Uvicorn
- Orchestration: LangGraph, LangChain
- LLM integrations: Azure OpenAI, LangChain OpenAI, LangChain Google GenAI
- Cloud/services: Azure Identity, Azure Storage Blob, Azure AI Search, Azure Monitor OpenTelemetry
- Data/document tooling: pandas, pypdf, yt-dlp, firecrawl-py
- Storage/cache/db clients: SQLAlchemy, psycopg2-binary, Redis
- App/UI dependency present: Streamlit

## Repository Structure

```text
D:\Projects\Multimodal_LLMOPS
|-- README.md
|-- PROJECT_DOCUMENTATION.md
|-- pyproject.toml
|-- uv.lock
|-- .env.example
|-- main.py
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

## Setup

1. Create/install environment and dependencies:
   - `uv sync`
2. Copy env template and fill values:
   - `copy .env.example .env`
3. Run the starter entrypoint:
   - `uv run python main.py`

## Environment Variables

Key variables currently referenced in project config/files:

- Azure OpenAI:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_VERSION`
  - `AZURE_OPENAI_CHAT_DEPLOYMENT`
  - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- Azure AI Search:
  - `AZURE_SEARCH_ENDPOINT`
  - `AZURE_SEARCH_API_KEY`
  - `AZURE_SEARCH_INDEX_NAME`
- Azure Video Indexer / storage:
  - `AZURE_STORAGE_CONNECTION_STRING`
  - `AZURE_VI_NAME`
  - `AZURE_VI_LOCATION`
  - `AZURE_VI_ACCOUNT_ID`
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_RESOURCE_GROUP`
- Tracing/observability:
  - `APPLICATIONSINIGHTS_CONNECTION_STRING`
  - `LANGCHAIN_TRACING_V2`
  - `LANGCHAIN_ENDPOINT`
  - `LANGCHAIN_API_KEY`
  - `LANCHAIN_PROJECT_NAME`
- Gemini:
  - `GEMINI_API_KEY`

## Notes

- The canonical implementation target for workflow logic is under `backend/src/graph/`.
- For full architecture and module-level implementation details, see `PROJECT_DOCUMENTATION.md`.
