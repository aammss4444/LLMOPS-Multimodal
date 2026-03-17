# Multimodal LLMOps - Project Documentation

## 1. Project Overview

`Multimodal LLMOps` is a Python-based backend initiative for auditing video content against compliance/policy requirements using multimodal inputs.

Primary Goal:
- Ingest video input from YouTube.
- Extract transcript and OCR/text signals using Azure Video Indexer.
- Run RAG-based compliance checks using **Qdrant** and **Gemini Embeddings**.
- Extract text from brand guidelines using **PaddleOCR**.
- Produce structured compliance issues and a final report via FastAPI.

## 2. Architecture Snapshot

### 2.1 Layered Design

1. **API Layer** (`backend/src/api/`)
   - FastAPI service entrypoint (`server.py`).
   - Handles `/health` and `/audit` endpoints.

2. **Graph Orchestration Layer** (`backend/src/graph/`)
   - Core workflow orchestration using **LangGraph**.
   - `state.py`: Shared execution state (`VideoAuditState`).
   - `nodes.py`: Node logic for video indexing, audio RAG audit, and visual screening.
   - `workflow.py`: Directed graph definition.

3. **Services Layer** (`backend/src/services/`)
   - `video_indexer.py`: Integration with Azure Video Indexer for processing video files.

4. **Scripts Layer** (`backend/scripts/`)
   - `index_document.py`: Operational script to index brand guidelines into Qdrant using PaddleOCR.

5. **Data Layer** (`backend/data/`)
   - Source policy/reference documents (PDFs).

### 2.2 Workflow Definition

Pipeline as defined in `workflow.py`:
`index_video` -> `audio_content_audit` -> `visual_compliance_audit` -> `END`

## 3. Tools and Technologies

### 3.1 AI & Orchestration
- **LangGraph**: Workflow orchestration.
- **LangChain**: LLM framework.
- **Qdrant**: Vector database for RAG.
- **PyMuPDF (fitz)**: High-speed extraction of digital text from PDFs.
- **PaddleOCR**: High-accuracy OCR for extracting text from images found within PDFs.
- **Gemini Embeddings**: Vectorization of content.
- **Azure OpenAI (GPT)**: Compliance analysis.

### 3.2 Cloud & Infrastructure
- **Azure Video Indexer**: Multimedia analysis (transcript/OCR).
- **Azure CLI**: Authentication.
- **FastAPI**: Backend service.
- **uv**: Dependency management.

## 4. Configuration

Managed via `.env` file:
- `QDRANT_URL`, `QDRANT_COLLECTION_NAME`: Vector Store.
- `GEMINI_API_KEY`: Embeddings.
- `AZURE_OPENAI_*`: Chat analysis.
- `AZURE_VI_*`: Video processing.

## 5. Usage

### 5.1 Indexing Knowledge Base
```bash
uv run python backend/scripts/index_document.py
```

### 5.2 Starting the Server
```bash
python -m backend.src.api.server
```

### 5.3 Triggering Audit
```bash
curl -X POST "http://localhost:8000/audit" -H "Content-Type: application/json" -d '{"video_url": "YOUR_YOUTUBE_URL"}'
```
