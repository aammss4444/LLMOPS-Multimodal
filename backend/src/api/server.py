import sys
import types

# ── Compatibility shim ──────────────────────────────────────────
# langchain 1.x removed legacy re-export modules like
# "langchain.docstore", "langchain.text_splitter", etc.
# langchain_qdrant and other packages still import from those paths.
# This patches sys.modules so old import paths still resolve.
import langchain_community.docstore as _cd
from langchain_core.documents import Document as _Document

if "langchain.docstore" not in sys.modules:
    sys.modules["langchain.docstore"] = _cd

if "langchain.docstore.document" not in sys.modules:
    _mock_doc = types.ModuleType("langchain.docstore.document")
    _mock_doc.Document = _Document
    sys.modules["langchain.docstore.document"] = _mock_doc

try:
    import langchain_text_splitters as _lts
    if "langchain.text_splitter" not in sys.modules:
        sys.modules["langchain.text_splitter"] = _lts
except ImportError:
    pass
# ────────────────────────────────────────────────────────────────

import os
from typing import Any, Dict
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
# Reduce startup delays caused by remote Paddle model source checks.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from backend.src.graph.workflow import build_workflow

app = FastAPI(title="Multimodal LLMOps API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the graph
workflow = build_workflow()

class AuditRequest(BaseModel):
    video_url: str
    video_id: str = "vid_demo"

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/audit")
async def run_audit(request: AuditRequest):
    """
    Triggers the video audit workflow for a given URL.
    """
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        initial_state = {
            "video_url": request.video_url,
            "video_id": request.video_id,
            "compliance_issues": [],
            "errors": [],
            "checkpoint_status": {
                "url_received": "completed",
                "audit_triggered": "completed",
                "video_download": "pending",
                "ffmpeg_audio_extract": "pending",
                "whisper_transcription": "pending",
                "ffmpeg_frame_extract": "pending",
                "paddleocr_extract": "pending",
                "text_fusion": "pending",
                "structured_output": "pending",
                "audio_content_audit": "pending",
                "visual_compliance_audit": "pending",
            },
            "checkpoint_details": {
                "request_received_at_utc": now_iso,
                "source_video_url": request.video_url,
                "video_id": request.video_id,
            },
        }
        
        # Execute the graph
        final_state = workflow.invoke(initial_state)
        
        return {
            "status": "success",
            "checkpoint_status": final_state.get("checkpoint_status", {}),
            "checkpoint_details": final_state.get("checkpoint_details", {}),
            "results": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
