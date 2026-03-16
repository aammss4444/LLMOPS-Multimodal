import json
import os
import re
import logging
from typing import Any, Dict, List

from Langchain_openai import AzureChatOpenAI
from langchain_community.vectorstores import AzureSearch    
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# import state schema 

from backend.src.graph.state import VideoAuditState, ComplianceIssue

# import services
from backend.src.services.video_indexer import VideoIndexerService

# Configure logging
logger = logging.getLogger("llmops-multimodal")
logging.basicConfig(level=logging.INFO)

# Build the first node
# Node 1: Indexer

def index_video_node(state: VideoAuditState) -> dict[str, Any]:
    '''
    Downlaods the video from the given URL
    Uploads to Azure video indexer
    extracts the insights
    '''
    video_url = state.get("video_url")
    video_id_input = state.get("video_id","vid_demo")

    logger.info(f"---[Node: Indexer] Processing: {video_url}")

    local_filename = "temp_audit_video.mp4"

    try: 
        vi_service = VideoIndexerService()
        # Download
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)

        else:
            raise Exception("Please provide a valid youtube URL for indexing")   

        #upload
        azure_video_id = vi_service.upload_video(local_path, video_name= video_id_input)  
        logger.info(f"Upload Success.Azure ID : {azure_video_id}")

        # clean up
        if os.path.exists(local_path): 
            os.remove(local_path)

        # wait
        raw_insights = vi_service.waitforprocessing(azure_video_id)
        # extract 
        clean_data = vi_service.extract_data(raw_insights)
        logger.info(f"---[NODE: Indexer] Extraction Complete------")
        return clean_data

    except Exception as e:
        logger.error(f"Error in indexing video: {e}")
        return {
            "final_status": "Fail",
            "transcript": "",
            "ocr_text": [],
            "errors": [str(e)] 
        }
    
# Node 2: Compliance Audit
def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    '''
    This performs RAG to audit the content - brand video 
    '''
    logger.info(f"---[Node: Auditor] quering Knowledge Base & LLM")

    transcript = state.get("transcript", "")

    if not transcript:
        logger.warning("No transcript available. Skipping Audit.")
        return {
            "final_status": "FAIL",
            "final_report": "Audit skipped because video processing failed (No Transcript)."
        }

    
    # 1. Setup LLM
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.0
    )

    # 2. Setup embeddings
    embed_model = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        chunk_size=16
    )
   
    
    

    