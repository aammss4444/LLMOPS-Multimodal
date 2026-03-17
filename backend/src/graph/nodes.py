import json
import os
import re
import logging
from typing import Any, Dict, List

from langchain_openai import AzureChatOpenAI
# Qdrant Vector Store
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# import state schema 

from backend.src.graph.state import VideoAuditState, ComplianceIssue

# import services
from backend.src.services.video_indexer import VideoIndexerService

# Configure logging
logger = logging.getLogger("llmops-multimodal")
logging.basicConfig(level=logging.INFO)

# Build the first node
# Node 1: Indexer

def index_video(state: VideoAuditState) -> dict[str, Any]:
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
        raw_insights = vi_service.wait_for_processing(azure_video_id)
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

    # 2. Setup Gemini embeddings
    embed_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
   
    # 3. Setup Qdrant
    try:
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
            embedding=embed_model,
        )
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        return {"compliance_issues": state["compliance_issues"] + [f"RAG Error: {str(e)}"]}

    # 4. Perform RAG
    docs = vector_store.similarity_search(transcript, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    # 5. Audit
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Brand Compliance Auditor. Audit the transcript against the following brand guidelines:\n\n{context}"),
        ("human", "Transcript: {transcript}\n\nIdentify any compliance issues and return them in JSON format with fields: category, description, severity.")
    ])

    chain = prompt | llm
    response = chain.invoke({"context": context, "transcript": transcript})

    # Simple parsing logic
    issues = []
    try:
        content = response.content
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            issues = json.loads(match.group(0))
    except Exception as e:
        logger.error(f"Failed to parse audio audit response: {e}")

    return {
        "compliance_issues": issues,
        "final_status": "PASS" if not issues else "FAIL"
    }

def visual_compliance_node(state: VideoAuditState) -> Dict[str, Any]:
    '''
    Screens OCR text for restricted visual content
    '''
    logger.info("---[Node: Visual Auditor] Screening OCR Text")
    ocr_text = state.get("ocr_text", [])
    
    restricted_keywords = ["alcohol", "tobacco", "gambling", "adult"]
    issues = []

    for line in ocr_text:
        for word in restricted_keywords:
            if word.lower() in line.lower():
                issues.append({
                    "category": "Visual Compliance",
                    "description": f"Restricted content detected in visual text: '{line}'",
                    "severity": "CRITICAL",
                    "timestamp": None
                })

    return {
        "compliance_issues": issues,
        "final_status": "FAIL" if issues else "PASS",
        "final_report": "Visual screening complete."
    }
