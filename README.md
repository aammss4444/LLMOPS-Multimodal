# Multimodal LLMOps

Backend system for multimodal video compliance auditing with FastAPI, LangGraph orchestration, local media processing, OCR, and RAG-assisted policy checks.

Project root: `D:\Projects\Multimodal_LLMOPS`

## Current Status

- End-to-end audit workflow is implemented and callable via `POST /audit`.
- Local media pipeline is active: YouTube download -> FFmpeg extraction -> Whisper transcription -> PaddleOCR frame text extraction.
- Fusion and structured-output layers are implemented before compliance audit nodes.
- Checkpoint-based execution tracking is implemented in workflow state and API response.

## Implemented Audit Flow

1. User submits YouTube URL to API.
2. FastAPI creates initial audit state and triggers LangGraph workflow.
3. Video download is executed and saved locally.
4. FFmpeg extracts WAV audio and frame images.
5. Whisper transcribes extracted audio.
6. PaddleOCR extracts text from frames.
7. Fusion layer combines transcript + OCR into multimodal JSON payload.
8. Structured output layer produces analysis-ready records.
9. Audio and visual compliance audit nodes run against extracted content.

## Architecture Diagram

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
[FastAPI Server]
   |
   v
[LangGraph Orchestrator]
   |---> [Video Processor: yt-dlp + ffmpeg + whisper + OCR]
   |---> [Fusion Layer + Structured Output Layer]
   |---> [Qdrant Retrieval]
   |---> [Gemini 2.5 Flash Audit]
   |
   v
[JSON Response + Checkpoint Status]
```

## Flow Diagram

```text
URL Input -> /audit -> index_video
         -> download video
         -> ffmpeg audio extract
         -> whisper transcript
         -> ffmpeg frame extract
         -> paddleocr text
         -> fusion_layer
         -> structured_output_layer
         -> audio_content_audit
         -> visual_compliance_audit
         -> final response
```

## Checkpoint Tracking

Workflow exposes stage-level status using:
- `checkpoint_status`
- `checkpoint_details`

Tracked checkpoints:
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

## Tech Stack

- Runtime: Python 3.12+
- API: FastAPI, Uvicorn
- Orchestration: LangGraph, LangChain
- LLM: Gemini 2.5 Flash (`langchain-google-genai`)
- Embeddings + Vector DB: Gemini embeddings + Qdrant
- Video ingestion: `yt-dlp`
- Media processing: `ffmpeg`
- Audio transcription: `openai-whisper`
- OCR: `paddleocr`, `paddlepaddle`
- Document indexing: `PyMuPDF`, `Pillow`, `numpy`, `langchain-text-splitters`
- Package management: `uv`

## Repository Structure

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

## Setup

1. Install dependencies:
   - `uv sync`
2. Configure environment variables in `.env`.
3. Ensure `ffmpeg` is installed and available on system `PATH`.

## Run

```bash
# Start API
uv run python -m backend.src.api.server
```

## API

- Health:
  - `GET /health`
- Audit:
  - `POST /audit`
  - Body:

```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_id": "campaign_001"
}
```

Response includes:
- `status`
- `checkpoint_status`
- `checkpoint_details`
- `results` (final LangGraph state)
