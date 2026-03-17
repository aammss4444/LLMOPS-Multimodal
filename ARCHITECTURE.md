# Technical System Architecture - Multimodal LLMOps

This document provides a detailed technical overview of the `Multimodal LLMOps` system architecture, data flows, and component interactions.

---

## 1. High-Level System Architecture

The system follows a modular, layer-based architecture designed for multimodal data processing and LLM-driven compliance auditing.

```mermaid
graph TB
    subgraph "Client Layer"
        User([User/Client])
        API_Call(REST API Request)
    end

    subgraph "Application Layer (FastAPI)"
        SVR[Server: server.py]
        ORCH[LangGraph Orchestrator]
    end

    subgraph "Processing Layer"
        AVI_SVC[Azure Video Indexer Service]
        EXT_SVC[Hybrid PDF Extractor]
    end

    subgraph "Intelligence & Storage"
        EMB[Gemini Embeddings]
        QDR[(Qdrant Vector DB)]
        LLM[Azure OpenAI / GPT-4o]
    end

    User --> API_Call
    API_Call --> SVR
    SVR --> ORCH

    ORCH <--> AVI_SVC
    ORCH <--> EXT_SVC
    
    EXT_SVC --> EMB
    EMB --> QDR
    
    ORCH <--> QDR
    ORCH <--> LLM
```

---

## 2. Component Diagram

Each functional component is isolated to ensure maintainability and scalability.

```mermaid
classDiagram
    class Server {
        +POST /audit(video_url)
        +GET /health()
    }
    class Workflow {
        +State: VideoAuditState
        +Nodes: index_vid, audit_audio, screen_visual
    }
    class VideoIndexer {
        +download_youtube()
        +upload_to_azure()
        +wait_for_processing()
        +extract_insights()
    }
    class DocumentProcessor {
        +extract_digital_text()
        +extract_image_ocr()
        +generate_chunks()
    }
    class VectorStore {
        +upsert_documents()
        +similarity_search()
    }

    Server --> Workflow : triggers
    Workflow --> VideoIndexer : "Node: Index Video"
    Workflow --> VectorStore : "Node: Audio Auditor"
    DocumentProcessor --> VectorStore : "Indexing Script"
```

---

## 3. Data Flow Pipeline (Audit Workflow)

The sequence of operations during a compliance audit request.

```mermaid
sequenceDiagram
    participant U as User
    participant A as FastAPI Server
    participant G as LangGraph Orchestrator
    participant V as Azure Video Indexer
    participant Q as Qdrant Vector Store
    participant L as LLM (GPT-4o)

    U->>A: POST /audit (video_url)
    A->>G: Start Workflow (State)
    
    G->>V: Upload & Process Video
    V-->>G: Transcript & Visual OCR
    
    G->>Q: Query relevant brand guidelines (RAG)
    Q-->>G: Policy Context
    
    G->>L: Audit Transcript vs Context
    L-->>G: Compliance Issues (JSON)
    
    G->>A: Final Audit State
    A->>U: JSON Report
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
