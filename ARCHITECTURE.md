# Technical System Architecture - Multimodal LLMOps

This document provides a detailed technical overview of the `Multimodal LLMOps` system architecture, data flows, and component interactions.

---

## 1. High-Level System Architecture

The system follows a modular, layer-based architecture designed for multimodal data processing and LLM-driven compliance auditing.

```text
+----------------------------------------------------------+
| HIGH-LEVEL SYSTEM ARCHITECTURE (MULTIMODAL LLMOPS)      |
+----------------------------------------------------------+

[User/Client]
   |
   v
[REST API Request]
   |
   v
[Server: backend/src/api/server.py]
   |
   v
[LangGraph Orchestrator]
   |---> [Azure Video Indexer Service]
   |---> [Hybrid PDF Extractor]
   |          |
   |          v
   |      [Gemini Embeddings]
   |          |
   |          v
   +------> [Qdrant Vector DB]
   |
   +------> [Azure OpenAI (GPT-4o)]
```

---

## 2. Component Diagram

Each functional component is isolated to ensure maintainability and scalability.

```text
+----------------------------------------------------------+
| COMPONENT VIEW                                           |
+----------------------------------------------------------+

+-----------------------------------------------+
| Server (backend/src/api/server.py)            |
| - POST /audit(video_url)                      |
| - GET /health()                               |
+-----------------------------------------------+
                  |
                  | triggers
                  v
+-----------------------------------------------+
| Workflow (LangGraph State Machine)            |
| - State: VideoAuditState                      |
| - Nodes: index_vid, audit_audio, screen_visual|
+-----------------------------------------------+
      |                          |
      | Index_Video_Node         | Audio_Auditor_Node
      v                          v
+---------------------+    +----------------------+
| VideoIndexer        |    | VectorStore          |
| - download_youtube()|    | - upsert_documents() |
| - upload_video()    |    | - similarity_search()|
| - wait_for_processing()   +----------------------+
| - extract_insights()|
+---------------------+

+------------------------------+
| DocumentProcessor            |
| - extract_digital_text()     |
| - extract_image_ocr()        |
| - generate_chunks()          |
+------------------------------+
              |
              | Indexing_Script
              v
         [VectorStore]
```

---

## 3. Data Flow Pipeline (Audit Workflow)

The sequence of operations during a compliance audit request.

```text
+----------------------------------------------------------+
| DATA FLOW PIPELINE (AUDIT WORKFLOW)                      |
+----------------------------------------------------------+

[User]
  |
  | POST /audit (video_url)
  v
[FastAPI Server]
  |
  | Start Workflow (VideoAuditState)
  v
[LangGraph Orchestrator]
  |\
  | \--> [Azure Video Indexer]
  |         |
  |         +--> Transcript + Visual OCR
  |
  +--> [Qdrant Vector Store]
  |       |
  |       +--> Policy Context (RAG retrieval)
  |
  +--> [LLM: Azure OpenAI GPT-4o]
          |
          +--> Compliance Issues (JSON)

[LangGraph Orchestrator]
  |
  | Final Audit State
  v
[FastAPI Server]
  |
  | JSON Report
  v
[User]
```

---

## 4. Technology Stack Summary

- **Orchestration**: LangGraph (State Machine).
- **LLM / Reasoning**: Azure OpenAI GPT-4o.
- **Embeddings**: Google Gemini (`embedding-001`).
- **Vector DB**: Qdrant.
- **OCR Engine**: PaddleOCR (v5).
- **PDF Parser**: PyMuPDF (fitz).
- **Backend Framework**: FastAPI.
- **Dependency Management**: uv.
