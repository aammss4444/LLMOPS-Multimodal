# Multimodal LLMOps - Project Documentation

## 1. Project Overview

`Multimodal LLMOps` is a Python-based platform for auditing video content (e.g., advertisements, brand videos) against compliance and policy requirements. It leverages multimodal inputs (audio, visual text, and reference documents) to provide structured reports.

The current video pipeline is fully local for media extraction:
- Download source video (YouTube)
- Extract audio via `ffmpeg` for speech processing
- Run speech recognition with `Whisper` to generate transcript
- Extract frames via `ffmpeg` for OCR
- Run OCR over frames and perform compliance checks

---

## 2. Tools & Technologies

### 2.1 AI & Orchestration
| Tool | Purpose |
| :--- | :--- |
| **LangGraph** | Workflow orchestration and state management via directed graphs. |
| **LangChain** | Framework for developing LLM applications and vector store integrations. |
| **Qdrant** | High-performance vector database for storing and retrieving semantic information. |
| **PaddleOCR** | OCR on extracted video frames and embedded images in PDFs. |
| **PyMuPDF (fitz)** | Efficient parsing of the digital text layer in PDF documents. |
| **FFmpeg** | Local extraction of audio and frames from videos for speech and OCR processing. |
| **Whisper** | Local speech-to-text transcription from extracted WAV audio. |
| **Gemini Embeddings** | Vectorization of content using `models/embedding-001`. |
| **Azure OpenAI** | LLM reasoning for compliance analysis. |

### 2.2 Platform & Infrastructure
| Tool | Purpose |
| :--- | :--- |
| **FastAPI** | Backend API framework. |
| **uv** | Python dependency and environment management. |
| **Azure Monitor OpenTelemetry** | Observability and tracing. |

---

## 3. Methodologies

### 3.1 Hybrid PDF Extraction
To maximize policy coverage from guideline documents:
1. **Digital Layer**: `PyMuPDF` extracts searchable text.
2. **Image Layer**: `PaddleOCR` extracts text from embedded images.

### 3.2 Retrieval-Augmented Generation (RAG)
Relevant policy chunks are indexed in **Qdrant**. During audit:
- Whisper transcript is used as the retrieval query.
- Qdrant returns relevant policy context.
- LLM audits content against retrieved rules.

### 3.3 State-Based Orchestration
The pipeline runs as a **LangGraph State Machine**:
- Graceful failure handling in each node.
- Persistent, typed workflow state through `VideoAuditState`.

---

## 4. High-Level System Architecture

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
   |---> [FFmpeg + Whisper Video Processing Service]
   |---> [Hybrid PDF Extractor]
   |          |
   |          v
   |      [Gemini Embeddings]
   |          |
   |          v
   +------> [Qdrant Vector DB]
   |
   +------> [Azure OpenAI]
```

---

## 5. Component Diagram

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
| - Nodes: index_video, audio_content_audit,    |
|          visual_compliance_audit              |
+-----------------------------------------------+
      |                          |
      | Index_Video_Node         | Audio_Auditor_Node
      v                          v
+---------------------+    +----------------------+
| VideoProcessor      |    | VectorStore (Qdrant) |
| - download_youtube()|    | - similarity_search()|
| - extract_audio()   |    +----------------------+
| - transcribe_audio()|
| - extract_frames()  |
| - extract_ocr_text()|
+---------------------+

+------------------------------+
| DocumentProcessor            |
| - extract_digital_text()     |
| - extract_image_ocr()        |
| - generate_chunks()          |
+------------------------------+
              |
              | Indexing Script
              v
         [Qdrant VectorStore]
```

---

## 6. Data Flow Pipeline (Audit Workflow)

```text
+----------------------------------------------------------+
| DATA FLOW PIPELINE (AUDIT WORKFLOW)                      |
+----------------------------------------------------------+

[User]
  |
  | POST /audit (video_url, video_id)
  v
[FastAPI Server]
  |
  | Start Workflow (VideoAuditState)
  v
[LangGraph Orchestrator]
  |\
  | \--> [VideoProcessor]
  |         |
  |         +--> Download MP4
  |         +--> Extract WAV audio (ffmpeg)
  |         +--> Speech recognition (Whisper)
  |         +--> Transcript
  |         +--> Extract JPG frames (ffmpeg)
  |         +--> OCR text (PaddleOCR)
  |
  +--> [Qdrant Vector Store]
  |       |
  |       +--> Policy Context (RAG retrieval)
  |
  +--> [LLM: Azure OpenAI]
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

## 7. Storage Schema (Qdrant Metadata + Video Insights)

```text
+----------------------------------------------------------+
| STORAGE SCHEMA (QDRANT METADATA + VIDEO INSIGHTS)        |
+----------------------------------------------------------+

[VECTOR_LOGS]
   |
   | contains (1-to-many)
   v
[CHUNK]
   |- page_content      : text payload
   |- source            : original PDF filename
   |- page              : document page number
   |- extraction_method : digital OR ocr
   |- image_index       : optional image index on page

[VIDEO_INSIGHTS]
   |- video_id         : local workflow video ID
   |- local_file_path  : downloaded video path
   |- audio_file_path  : extracted WAV path
   |- frame_paths      : extracted frame file paths
   |- transcript       : Whisper transcript output
   |- ocr_elements     : visual text from extracted frames
```

---

## 8. Workflow State Schema (VideoAuditState)

- `video_url`: input video URL.
- `video_id`: caller-provided or default ID.
- `local_file_path`: downloaded video path.
- `audio_file_path`: extracted audio path (WAV).
- `frame_paths`: list of extracted frame image paths.
- `video_metadata`: platform and extraction metadata.
- `transcript`: transcript text from Whisper speech recognition.
- `ocr_text`: OCR lines extracted from frames.
- `compliance_issues`: accumulated structured issues.
- `final_status`: `PASS` or `FAIL`.
- `final_report`: summary report string.
- `errors`: accumulated system/process errors.

---

## 9. Project Structure

- `backend/scripts/index_document.py`: Indexes guideline docs into Qdrant.
- `backend/src/api/server.py`: FastAPI entrypoint.
- `backend/src/graph/state.py`: Workflow state schema.
- `backend/src/graph/nodes.py`: Graph node implementations.
- `backend/src/graph/workflow.py`: Node orchestration.
- `backend/src/services/video_processor.py`: YouTube download + ffmpeg extraction + Whisper transcription + OCR.
- `backend/data/`: Local data assets.

---

## 10. Setup and Usage

### 10.1 Environment Setup
1. Install `uv`.
2. Run `uv sync`.
3. Configure `.env` with required keys for Gemini, Azure OpenAI, Qdrant, and optional local path settings.
4. Ensure `ffmpeg` is installed and available on system `PATH`.
5. Configure Whisper runtime options (optional):
   - `WHISPER_MODEL` (default: `base`)
   - `WHISPER_LANGUAGE` (default: `en`)

### 10.2 Run
```bash
# Index guideline documents
uv run python backend/scripts/index_document.py

# Start API server
uv run python -m backend.src.api.server
```

### 10.3 Audit API
- `POST /audit`
- Body:
```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_id": "campaign_001"
}
```
