import json
import os
import re
import logging
from typing import Any, Dict

from langchain_openai import AzureChatOpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.src.graph.state import VideoAuditState
from backend.src.services.video_processor import VideoProcessingService

logger = logging.getLogger("llmops-multimodal")
logging.basicConfig(level=logging.INFO)


def index_video(state: VideoAuditState) -> dict[str, Any]:
    """
    Downloads the video from the provided URL and runs local ffmpeg processing:
    - audio extraction (speech pipeline input)
    - frame extraction + OCR
    """
    video_url = state.get("video_url")
    video_id_input = state.get("video_id", "vid_demo")

    logger.info(f"---[Node: Indexer] Processing: {video_url}")

    local_storage_dir = os.getenv("LOCAL_VIDEO_STORAGE_DIR", "backend/data/videos")
    safe_video_name = re.sub(r"[^a-zA-Z0-9._-]", "_", video_id_input)
    local_filename = os.path.join(local_storage_dir, f"{safe_video_name}.mp4")

    try:
        processing_service = VideoProcessingService()

        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path = processing_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise Exception("Please provide a valid YouTube URL for indexing")

        logger.info(f"Video retained in local storage: {local_path}")

        processed_data = processing_service.process_video(local_path, video_id_input)
        logger.info("---[NODE: Indexer] ffmpeg extraction complete------")
        return processed_data

    except Exception as e:
        logger.error(f"Error in indexing video: {e}")
        return {
            "final_status": "Fail",
            "transcript": "",
            "ocr_text": [],
            "errors": [str(e)],
        }


def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    logger.info("---[Node: Auditor] querying Knowledge Base & LLM")

    transcript = state.get("transcript", "")

    if not transcript:
        logger.warning("No transcript available. Skipping Audit.")
        return {
            "final_status": "FAIL",
            "final_report": "Audit skipped because transcript is not available from the speech pipeline.",
        }

    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.0,
    )

    embed_model = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

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

    docs = vector_store.similarity_search(transcript, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Brand Compliance Auditor. Audit the transcript against the following brand guidelines:\n\n{context}"),
        ("human", "Transcript: {transcript}\n\nIdentify any compliance issues and return them in JSON format with fields: category, description, severity."),
    ])

    chain = prompt | llm
    response = chain.invoke({"context": context, "transcript": transcript})

    issues = []
    try:
        content = response.content
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            issues = json.loads(match.group(0))
    except Exception as e:
        logger.error(f"Failed to parse audio audit response: {e}")

    return {
        "compliance_issues": issues,
        "final_status": "PASS" if not issues else "FAIL",
    }


def visual_compliance_node(state: VideoAuditState) -> Dict[str, Any]:
    logger.info("---[Node: Visual Auditor] Screening OCR Text")
    ocr_text = state.get("ocr_text", [])

    restricted_keywords = ["alcohol", "tobacco", "gambling", "adult"]
    issues = []

    for line in ocr_text:
        for word in restricted_keywords:
            if word.lower() in line.lower():
                issues.append(
                    {
                        "category": "Visual Compliance",
                        "description": f"Restricted content detected in visual text: '{line}'",
                        "severity": "CRITICAL",
                        "timestamp": None,
                    }
                )

    return {
        "compliance_issues": issues,
        "final_status": "FAIL" if issues else "PASS",
        "final_report": "Visual screening complete.",
    }
