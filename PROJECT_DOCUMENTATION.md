# Multimodal LLMOps - Project Documentation

## 1. Overview

`Multimodal LLMOps` is a FastAPI backend that audits YouTube video content against policy/guideline knowledge using multimodal extraction (speech + visual text) and RAG-based LLM analysis.

The implementation is workflow-driven using LangGraph and currently supports:
- Video download from YouTube
- Audio/frame extraction via FFmpeg
- Whisper transcription
- PaddleOCR text extraction from frames
- Text fusion and analysis-ready structuring
- Compliance checks using Gemini + Qdrant hybrid context retrieval (keyword + dense vectors)
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
| Vector Store | Qdrant (Hybrid retrieval: Dense + Sparse keyword) |

## 2.4 System Architecture Diagram

```text
+----------------------------------------------------------+
| HIGH-LEVEL SYSTEM ARCHITECTURE (MULTIMODAL LLMOPS)      |
+----------------------------------------------------------+

[User/Client]
   |
   v
[REST API Request: video_url, video_id]
   |
   v
[Server: backend/src/api/server.py]
  - validates payload
  - initializes checkpoint_status/checkpoint_details
  - invokes workflow and returns final state
   |
   v
[LangGraph Orchestrator]
   |---> [Video Processor Service]
   |         +--> yt-dlp download -> local .mp4
   |         +--> ffmpeg audio extract -> .wav
   |         +--> whisper transcription -> transcript text
   |         +--> ffmpeg frame extract -> frame_*.jpg
   |         +--> paddleocr extraction -> OCR text lines
   |
   |---> [Fusion + Structured Output]
   |         +--> fused_payload JSON
   |         +--> structured_output (analysis-ready records)
   |
   |---> [Qdrant Knowledge Base]
   |         +--> dense embeddings search
   |         +--> sparse keyword search
   |         +--> hybrid retrieval context for audit
   |
   +----> [Gemini 2.5 Flash]
             +--> compliance issues JSON
             +--> final pass/fail status
```

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
  - Initializes reusable LLM/Qdrant clients (cached)
  - Retrieves relevant policy context from Qdrant hybrid retrieval
  - Audits multimodal text with Gemini
  - Returns structured compliance issues

- `visual_compliance_audit`:
  - Runs keyword-based visual risk checks on OCR text

### 3.2 Node Input/Output Contracts

| Node | Reads from state | Writes to state | Why it exists |
| :--- | :--- | :--- | :--- |
| `index_video` | `video_url`, `video_id` | `local_file_path`, `audio_file_path`, `frame_paths`, `transcript`, `ocr_text`, `video_metadata`, `checkpoint_*`, `errors` | Converts raw URL input into machine-usable multimodal artifacts. |
| `fusion_layer` | `transcript`, `ocr_text`, `video_id` | `fused_text`, `fused_payload`, `checkpoint_*`, `video_metadata.fusion` | Creates one combined representation that downstream audit can consume consistently. |
| `structured_output_layer` | `fused_text`, `fused_payload`, `transcript`, `ocr_text`, `video_id`, `video_url` | `structured_output`, `checkpoint_*` | Normalizes extracted content into analysis-ready records for later analytics/reporting use. |
| `audio_content_audit` | `fused_text` (fallback `transcript`), `ocr_text`, Qdrant collection | `compliance_issues`, `final_status`, `final_report`, `checkpoint_*`, `errors` | Performs hybrid RAG + LLM policy audit over extracted content. |
| `visual_compliance_audit` | `ocr_text` | `compliance_issues`, `final_status`, `final_report`, `checkpoint_*` | Adds deterministic keyword safety checks from visual text. |

### 3.4 RAG Client Initialization in `nodes.py`

`audio_content_audit` now uses cached initialization helpers to avoid rebuilding heavy clients on every request:
- `get_llm_client()`
- `get_dense_embeddings()`
- `get_qdrant_client()`
- `get_vector_store()`

Initialization behavior:
- Primary mode: `RetrievalMode.HYBRID` with dense embeddings + sparse keyword retrieval.
- Fallback mode: `RetrievalMode.DENSE` if sparse/hybrid setup is unavailable.
- This keeps the node resilient while preserving Qdrant as the knowledge base query source.

### 3.5 Prompting Format Used in `audio_content_audit`

System prompt structure:
- Declares role: senior brand compliance auditor.
- Injects retrieved policy chunks as `OFFICIAL REGULATORY RULES`.
- Enforces strict JSON schema:
  - `compliance_results`
  - `status`
  - `final_report`

User message structure:
- `VIDEO_METADATA`
- `TRANSCRIPT`
- `ON-SCREEN TEXT (OCR)`

The LLM output is parsed into normalized workflow fields:
- `compliance_issues`
- `final_status`
- `final_report`

### 3.3 Video Processing Service Responsibilities (`backend/src/services/video_processor.py`)

`VideoProcessingService` is the core media ETL component. It owns local media extraction and conversion from binary video into textual content.

Method-by-method behavior:
- `download_youtube_video(url, output_path)`:
  - Uses `yt-dlp` to fetch YouTube media.
  - Saves output to deterministic local path from `video_id`.
  - Fails fast on invalid URL/download errors.
- `extract_audio(video_path, output_path)`:
  - Uses `ffmpeg` to generate mono 16k WAV.
  - Output is designed for Whisper compatibility.
- `transcribe_audio(audio_path)`:
  - Lazily loads Whisper model (`WHISPER_MODEL`) once.
  - Produces transcript string.
- `extract_frames(video_path, output_dir, interval_seconds)`:
  - Uses `ffmpeg` fps filter (`fps=1/N`) to sample frames.
  - Returns ordered frame file list.
- `extract_ocr_text(frame_paths)`:
  - Runs PaddleOCR over each extracted frame.
  - Deduplicates case-insensitive text lines.
- `process_video(video_path, video_id)`:
  - Runs entire extraction pipeline in sequence.
  - Tracks each checkpoint (`ffmpeg_audio_extract`, `whisper_transcription`, etc.).
  - Raises `VideoProcessingError` with partial checkpoint progress if any stage fails.

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

## 6.1 Detailed Flow Diagram

```text
[User]
  |
  | POST /audit (video_url, video_id)
  v
[FastAPI Server]
  |
  | initialize checkpoint state
  v
[LangGraph]
  |
  +--> [index_video]
  |      +--> Download MP4
  |      +--> Extract WAV audio (ffmpeg)
  |      +--> Transcribe (whisper)
  |      +--> Extract JPG frames (ffmpeg)
  |      +--> OCR text (paddleocr)
  |
  +--> [fusion_layer]
  |      +--> merged transcript + OCR JSON
  |
  +--> [structured_output_layer]
  |      +--> analysis-ready records
  |
  +--> [audio_content_audit]
  |      +--> retrieve hybrid context from Qdrant knowledge base
  |      +--> apply strict JSON compliance prompt
  |      +--> audit with Gemini and parse structured output
  |
  +--> [visual_compliance_audit]
  |
  v
[Final Response]
```

## 6.2 Artifact Flow Diagram (What is produced at each stage)

```text
[Input]
video_url + video_id
   |
   v
[index_video]
   |- local_file_path: backend/data/videos/<video_id>.mp4
   |- audio_file_path: backend/data/audio/<video_id>.wav
   |- frame_paths: backend/data/frames/<video_id>/frame_*.jpg
   |- transcript: whisper output text
   |- ocr_text: ["line1", "line2", ...]
   v
[fusion_layer]
   |- fused_text: joined transcript + OCR block text
   |- fused_payload:
      {
        "video_id": "...",
        "transcript": "...",
        "ocr_text": [...],
        "fusion_stats": {...}
      }
   v
[structured_output_layer]
   |- structured_output:
      {
        "records": [
          {"source_type": "transcript", ...},
          {"source_type": "ocr", ...}
        ],
        "combined_text": "...",
        "fused_payload": {...}
      }
   v
[auditors]
   |- compliance_issues: [{category, description, severity, timestamp}]
   |- final_status: PASS/FAIL
   |- final_report: summary from LLM audit
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

### 7.4 Response Field Meanings (Practical)

- `status`:
  - API invocation status (`success` or HTTP error response).
- `checkpoint_status`:
  - Stage-wise health of entire pipeline; fastest way to identify failed checkpoint.
- `checkpoint_details`:
  - Helpful metadata for debugging (`local_file_path`, `audio_file_path`, counts, etc.).
- `results`:
  - Full final LangGraph state including extracted artifacts, structured output, and compliance issues.

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
  - `QDRANT_ENABLE_HYBRID_SEARCH`
  - `QDRANT_SPARSE_VECTOR_NAME`
  - `QDRANT_SPARSE_MODEL`
  - `QDRANT_TOP_K`

## 9. Repository Files

- `backend/src/api/server.py`: API server and workflow trigger
- `backend/src/graph/workflow.py`: graph definition and node order
- `backend/src/graph/nodes.py`: node logic (indexing, fusion, audit)
- `backend/src/graph/state.py`: typed state schema
- `backend/src/services/video_processor.py`: local media processing
- `backend/scripts/index_document.py`: PDF ingestion and Qdrant indexing

## 9.1 Directory Diagram

```text
D:\Projects\Multimodal_LLMOPS
|-- README.md
|-- PROJECT_DOCUMENTATION.md
|-- pyproject.toml
|-- uv.lock
|-- main.py
`-- backend/
    |-- data/
    |-- scripts/
    |   `-- index_document.py
    `-- src/
        |-- api/
        |   |-- server.py
        |   `-- telementry.py
        |-- graph/
        |   |-- nodes.py
        |   |-- state.py
        |   `-- workflow.py
        `-- services/
            `-- video_processor.py
```

### 9.2 File-by-File Responsibilities (Detailed)

- `backend/src/api/server.py`:
  - Defines `POST /audit` and `GET /health`.
  - Builds initial state and initial checkpoints.
  - Calls workflow synchronously and returns final JSON.

- `backend/src/graph/state.py`:
  - Declares `VideoAuditState` typed schema.
  - Defines shared contract for all nodes (keys and expected shapes).

- `backend/src/graph/workflow.py`:
  - Registers nodes and exact execution order.
  - Controls graph entry point and terminal edge.

- `backend/src/graph/nodes.py`:
  - Implements node business logic.
  - Merges checkpoint updates across nodes.
  - Initializes cached RAG clients.
  - Executes Qdrant hybrid retrieval and strict JSON audit prompting/parsing.

- `backend/src/services/video_processor.py`:
  - Encapsulates media extraction primitives and OCR/STT sequence.
  - Provides detailed checkpoint-aware failure propagation via `VideoProcessingError`.

- `backend/scripts/index_document.py`:
  - Extracts guideline text from PDFs (digital layer + image OCR).
  - Splits/chunks content and uploads embeddings into Qdrant.
  - Enables retrieval context used by `audio_content_audit`.

## 10. Runbook

```bash
# Install deps
uv sync

# Index guideline documents into Qdrant
uv run python backend/scripts/index_document.py

# Start API
uv run python -m backend.src.api.server
```

## 11. Failure Handling and Debug Guide

Common failures and where to inspect:
- YouTube download fails:
  - Check `video_download` checkpoint and `errors`.
  - Verify URL is valid and network access exists.
- FFmpeg extraction fails:
  - Check `ffmpeg_audio_extract`/`ffmpeg_frame_extract`.
  - Confirm `ffmpeg` is installed and on `PATH`.
- Whisper fails:
  - Check `whisper_transcription`.
  - Verify model availability and audio file generation.
- OCR fails:
  - Check `paddleocr_extract` and `ocr_line_count` in details.
- Qdrant/Gemini audit fails:
  - Check `audio_content_audit` and `errors`.
  - Verify `QDRANT_*` and `GEMINI_API_KEY`.
  - If hybrid init fails, verify sparse settings and whether dense fallback is being used.

Recommended triage order:
1. Inspect `checkpoint_status`.
2. Inspect `checkpoint_details`.
3. Inspect `results.errors`.
4. Re-run with same `video_id` to compare artifact paths and counts.
