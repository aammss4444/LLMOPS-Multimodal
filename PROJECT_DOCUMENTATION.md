# Multimodal LLMOps - Project Documentation

## 1. Overview

`Multimodal LLMOps` is a FastAPI backend that audits YouTube video content against policy/guideline knowledge using multimodal extraction (speech + visual text) and RAG-based LLM analysis.

The implementation is workflow-driven using LangGraph and currently supports:
- Video download from YouTube
- Audio/frame extraction via FFmpeg
- Whisper transcription
- PaddleOCR text extraction from frames
- Text fusion and analysis-ready structuring
- Compliance checks using Gemini + Qdrant context retrieval
- Checkpoint-level pipeline observability

## 2. Core Technologies

### 2.1 Orchestration, API, and Runtime
| Component | Technology |
| :--- | :--- |
| Runtime | Python 3.12+ |
| API | FastAPI, Uvicorn |
| Workflow | LangGraph |
| App Framework | LangChain |
| Dependency Manager | uv |

### 2.2 Multimodal Processing
| Component | Technology |
| :--- | :--- |
| Video Download | yt-dlp |
| Media Extraction | FFmpeg |
| Speech-to-Text | openai-whisper |
| OCR | PaddleOCR, PaddlePaddle |
| PDF Text + OCR Indexing | PyMuPDF, Pillow, numpy |

### 2.3 LLM and Retrieval
| Component | Technology |
| :--- | :--- |
| Generation/Audit Model | Gemini 2.5 Flash |
| Embeddings | Gemini Embeddings |
| Vector Store | Qdrant |

## 3. Implemented Workflow

Workflow entrypoint: `index_video`  
Execution order:
1. `index_video`
2. `fusion_layer`
3. `structured_output_layer`
4. `audio_content_audit`
5. `visual_compliance_audit`
6. `END`

### 3.1 Node Responsibilities

- `index_video`:
  - Validates YouTube URL
  - Downloads MP4 locally
  - Runs FFmpeg extraction
  - Runs Whisper transcription
  - Runs PaddleOCR on extracted frames
  - Returns extracted media/text artifacts

- `fusion_layer`:
  - Combines transcript text and OCR text
  - Produces `fused_text`
  - Produces JSON `fused_payload`

- `structured_output_layer`:
  - Converts extracted content into analysis-ready records
  - Generates normalized `structured_output`

- `audio_content_audit`:
  - Retrieves relevant policy context from Qdrant
  - Audits multimodal text with Gemini
  - Returns structured compliance issues

- `visual_compliance_audit`:
  - Runs keyword-based visual risk checks on OCR text

## 4. Checkpoint Model

The API and workflow maintain explicit stage checkpoints.

### 4.1 Checkpoint Fields
- `checkpoint_status: Dict[str, str]`
- `checkpoint_details: Dict[str, Any]`

### 4.2 Tracked Checkpoints
- `url_received`
- `audit_triggered`
- `video_download`
- `ffmpeg_audio_extract`
- `whisper_transcription`
- `ffmpeg_frame_extract`
- `paddleocr_extract`
- `text_fusion`
- `structured_output`
- `audio_content_audit`
- `visual_compliance_audit`

Checkpoint values are updated during execution (`pending`, `completed`, `failed`, or `skipped`).

## 5. State Schema (`VideoAuditState`)

Main keys in workflow state:
- Request/context:
  - `video_url`
  - `video_id`
- Extracted artifacts:
  - `local_file_path`
  - `audio_file_path`
  - `frame_paths`
  - `transcript`
  - `ocr_text`
- Fusion and normalized outputs:
  - `fused_text`
  - `fused_payload`
  - `structured_output`
- Audit outputs:
  - `compliance_issues`
  - `final_status`
  - `final_report`
  - `errors`
- Observability:
  - `checkpoint_status`
  - `checkpoint_details`

## 6. Data Flow

```text
Client -> FastAPI /audit -> LangGraph Workflow
       -> index_video (download + ffmpeg + whisper + OCR)
       -> fusion_layer (transcript + OCR fusion JSON)
       -> structured_output_layer (analysis-ready records)
       -> audio_content_audit (RAG + Gemini)
       -> visual_compliance_audit
       -> API response (results + checkpoint maps)
```

## 7. API Contract

### 7.1 Endpoint
- `POST /audit`

### 7.2 Request
```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_id": "campaign_001"
}
```

### 7.3 Response (high-level)
```json
{
  "status": "success",
  "checkpoint_status": {},
  "checkpoint_details": {},
  "results": {}
}
```

## 8. Environment Variables

- Storage and extraction:
  - `LOCAL_VIDEO_STORAGE_DIR`
  - `LOCAL_AUDIO_STORAGE_DIR`
  - `LOCAL_FRAMES_STORAGE_DIR`
  - `FRAME_INTERVAL_SECONDS`
- Whisper:
  - `WHISPER_MODEL`
  - `WHISPER_LANGUAGE`
- Gemini:
  - `GEMINI_API_KEY`
- Qdrant:
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `QDRANT_COLLECTION_NAME`
  - `QDRANT_VECTOR_NAME`

## 9. Repository Files

- `backend/src/api/server.py`: API server and workflow trigger
- `backend/src/graph/workflow.py`: graph definition and node order
- `backend/src/graph/nodes.py`: node logic (indexing, fusion, audit)
- `backend/src/graph/state.py`: typed state schema
- `backend/src/services/video_processor.py`: local media processing
- `backend/scripts/index_document.py`: PDF ingestion and Qdrant indexing

## 10. Runbook

```bash
# Install deps
uv sync

# Index guideline documents into Qdrant
uv run python backend/scripts/index_document.py

# Start API
uv run python -m backend.src.api.server
```
