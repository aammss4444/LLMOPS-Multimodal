import os
from typing import Any, Dict
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
        initial_state = {
            "video_url": request.video_url,
            "video_id": request.video_id,
            "compliance_issues": [],
            "errors": []
        }
        
        # Execute the graph
        final_state = workflow.invoke(initial_state)
        
        return {
            "status": "success",
            "results": final_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
