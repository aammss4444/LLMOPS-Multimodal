import os
from typing import Any, Dict
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.src.graph.workflow import build_workflow

# Load environment variables
load_dotenv(override=True)

app = FastAPI(title="Multimodal LLMOps API")

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
