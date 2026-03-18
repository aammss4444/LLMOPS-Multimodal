import json
import os
import re
import logging
from typing import Any, Dict

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from backend.src.graph.state import VideoAuditState
from backend.src.services.video_processor import VideoProcessingError, VideoProcessingService

logger = logging.getLogger("llmops-multimodal")
logging.basicConfig(level=logging.INFO)


def merge_checkpoint_state(
    state: VideoAuditState,
    updates: Dict[str, str] | None = None,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    status = dict(state.get("checkpoint_status") or {})
    detail_map = dict(state.get("checkpoint_details") or {})
    if updates:
        status.update(updates)
    if details:
        detail_map.update(details)
    return {"checkpoint_status": status, "checkpoint_details": detail_map}


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
        processed_data.update(
            merge_checkpoint_state(
                state,
                updates=processed_data.get("checkpoint_status"),
                details=processed_data.get("checkpoint_details"),
            )
        )
        logger.info("---[NODE: Indexer] ffmpeg extraction complete------")
        return processed_data

    except VideoProcessingError as e:
        logger.error(f"Error in indexing video: {e}")
        merged = merge_checkpoint_state(
            state,
            updates=e.checkpoint_status,
            details=e.checkpoint_details,
        )
        return {
            **merged,
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
            "errors": [str(e)],
        }
    except Exception as e:
        logger.error(f"Error in indexing video: {e}")
        merged = merge_checkpoint_state(state, updates={"video_download": "failed"})
        return {
            **merged,
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
            "errors": [str(e)],
        }


def fusion_layer_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Fusion Layer:
    Combine transcript text and OCR text into a single multimodal text stream.
    """
    logger.info("---[Node: Fusion] Combining transcript + OCR text")

    transcript = (state.get("transcript") or "").strip()
    ocr_lines = state.get("ocr_text") or []
    ocr_lines = [line.strip() for line in ocr_lines if isinstance(line, str) and line.strip()]

    combined_sections = []
    if transcript:
        combined_sections.append(f"[TRANSCRIPT]\n{transcript}")
    if ocr_lines:
        combined_sections.append("[OCR_TEXT]\n" + "\n".join(ocr_lines))

    fused_content = "\n\n".join(combined_sections).strip()
    fused_payload = {
        "video_id": state.get("video_id"),
        "transcript": transcript,
        "ocr_text": ocr_lines,
        "fusion_stats": {
            "has_transcript": bool(transcript),
            "ocr_line_count": len(ocr_lines),
            "fused_char_count": len(fused_content),
        },
    }

    return {
        **merge_checkpoint_state(state, updates={"text_fusion": "completed"}),
        "fused_text": fused_content,
        "fused_payload": fused_payload,
        "video_metadata": {
            **(state.get("video_metadata") or {}),
            "fusion": fused_payload["fusion_stats"],
        },
    }


def structured_output_node(state: VideoAuditState) -> Dict[str, Any]:
    """
    Structured Output Layer:
    Convert extracted multimodal content into analysis-ready normalized records.
    """
    logger.info("---[Node: Structured Output] Building analysis-ready structure")

    transcript = (state.get("transcript") or "").strip()
    ocr_lines = state.get("ocr_text") or []
    ocr_lines = [line.strip() for line in ocr_lines if isinstance(line, str) and line.strip()]

    analysis_records = []
    if transcript:
        analysis_records.append(
            {
                "source_type": "transcript",
                "content": transcript,
                "sequence": 0,
            }
        )

    for idx, line in enumerate(ocr_lines, start=1):
        analysis_records.append(
            {
                "source_type": "ocr",
                "content": line,
                "sequence": idx,
            }
        )

    structured_output = {
        "video_id": state.get("video_id"),
        "source_url": state.get("video_url"),
        "transcript_available": bool(transcript),
        "ocr_line_count": len(ocr_lines),
        "records": analysis_records,
        "combined_text": state.get("fused_text", ""),
        "fused_payload": state.get("fused_payload") or {},
    }

    return {
        **merge_checkpoint_state(state, updates={"structured_output": "completed"}),
        "structured_output": structured_output,
    }


def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    logger.info("---[Node: Auditor] querying Knowledge Base & LLM")

    transcript = (state.get("transcript") or "").strip()
    fused_text = (state.get("fused_text") or "").strip()
    query_text = fused_text or transcript

    if not query_text:
        logger.warning("No transcript/OCR text available. Skipping Audit.")
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "skipped"}),
            "final_status": "FAIL",
            "final_report": "Audit skipped because no extracted multimodal text is available.",
        }

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
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
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "failed"}),
            "errors": [f"RAG Error: {str(e)}"],
        }

    docs = vector_store.similarity_search(query_text, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Brand Compliance Auditor. Audit the extracted multimodal content against the following brand guidelines:\n\n{context}"),
        ("human", "Extracted Content: {query_text}\n\nIdentify any compliance issues and return them in JSON format with fields: category, description, severity."),
    ])

    chain = prompt | llm
    response = chain.invoke({"context": context, "query_text": query_text})

    issues = []
    try:
        content = response.content
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            issues = json.loads(match.group(0))
    except Exception as e:
        logger.error(f"Failed to parse audio audit response: {e}")

    return {
        **merge_checkpoint_state(state, updates={"audio_content_audit": "completed"}),
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
        **merge_checkpoint_state(state, updates={"visual_compliance_audit": "completed"}),
        "compliance_issues": issues,
        "final_status": "FAIL" if issues else "PASS",
        "final_report": "Visual screening complete.",
    }
