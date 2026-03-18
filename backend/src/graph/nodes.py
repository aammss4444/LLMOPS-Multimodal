import json
import os
import re
import logging
from functools import lru_cache
from typing import Any, Dict

from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from langchain_core.messages import HumanMessage, SystemMessage
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


@lru_cache(maxsize=1)
def get_llm_client() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_AUDIT_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.0,
    )


@lru_cache(maxsize=1)
def get_dense_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    client = get_qdrant_client()
    dense_embeddings = get_dense_embeddings()
    collection_name = os.getenv("QDRANT_COLLECTION_NAME")
    vector_name = os.getenv("QDRANT_VECTOR_NAME", "transcript_dense_vector")
    sparse_vector_name = os.getenv("QDRANT_SPARSE_VECTOR_NAME", "transcript_sparse_vector")
    use_hybrid = os.getenv("QDRANT_ENABLE_HYBRID_SEARCH", "true").lower() == "true"

    if use_hybrid:
        try:
            sparse_embeddings = FastEmbedSparse(
                model_name=os.getenv("QDRANT_SPARSE_MODEL", "prithvida/Splade_PP_en_v1")
            )
            return QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=dense_embeddings,
                sparse_embedding=sparse_embeddings,
                retrieval_mode=RetrievalMode.HYBRID,
                vector_name=vector_name,
                sparse_vector_name=sparse_vector_name,
            )
        except Exception as e:
            logger.warning(
                "Hybrid vector store initialization failed, falling back to dense retrieval: %s",
                str(e),
            )

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=dense_embeddings,
        retrieval_mode=RetrievalMode.DENSE,
        vector_name=vector_name,
    )


def parse_json_object_from_llm(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty LLM response")

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()
    else:
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace >= 0 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]

    return json.loads(text)


def build_retrieved_rules_context(docs: list[Any]) -> tuple[str, list[dict[str, Any]]]:
    context_parts: list[str] = []
    references: list[dict[str, Any]] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source = metadata.get("source", "unknown_source")
        page = metadata.get("page", "unknown_page")
        chunk_index = metadata.get("chunk_index", "unknown_chunk")
        extraction_method = metadata.get("extraction_method", "unknown")
        text = (doc.page_content or "").strip()
        context_parts.append(
            f"[Rule {idx}] Source={source} | Page={page} | Chunk={chunk_index} | Method={extraction_method}\n{text}"
        )
        references.append(
            {
                "rank": idx,
                "source": source,
                "page": page,
                "chunk_index": chunk_index,
                "extraction_method": extraction_method,
            }
        )
    return "\n\n".join(context_parts), references


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
    ocr_text_lines = state.get("ocr_text") or []
    ocr_text = "\n".join([line for line in ocr_text_lines if isinstance(line, str)])
    query_text = fused_text or "\n".join([transcript, ocr_text]).strip()

    if not query_text:
        logger.warning("No transcript/OCR text available. Skipping Audit.")
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "skipped"}),
            "final_status": "FAIL",
            "final_report": "Audit skipped because no extracted multimodal text is available.",
        }

    try:
        llm = get_llm_client()
        vector_store = get_vector_store()
    except Exception as e:
        logger.error("Failed to initialize RAG clients: %s", str(e))
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "failed"}),
            "errors": [f"RAG initialization error: {str(e)}"],
        }

    try:
        top_k = int(os.getenv("QDRANT_TOP_K", "5"))
        docs = vector_store.similarity_search(query_text, k=top_k)
        if not docs:
            return {
                **merge_checkpoint_state(state, updates={"audio_content_audit": "failed"}),
                "errors": ["RAG retrieval returned no legal/guideline chunks from Qdrant."],
            }
        retrieved_rules, rag_rule_references = build_retrieved_rules_context(docs)
    except Exception as e:
        logger.error("Qdrant retrieval failed: %s", str(e))
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "failed"}),
            "errors": [f"RAG retrieval error: {str(e)}"],
        }

    system_prompt = f"""
You are a senior brand compliance auditor.
OFFICIAL REGULATORY RULES:
{retrieved_rules}
INSTRUCTIONS:
1. Analyze the transcript and OCR text below.
2. Compare brand statements against OFFICIAL REGULATORY RULES.
3. Identify:
   - direct rule violations
   - misleading or unverifiable brand claims
   - missing mandatory disclosures (if applicable)
4. Return strictly JSON in the following format:
{{
  "compliance_results": [
    {{
      "category": "Claim Validation",
      "severity": "CRITICAL",
      "description": "Explanation of the violation or misleading claim...",
      "misleading_claim": true,
      "evidence": "Transcript/OCR snippet that triggered this finding",
      "rule_reference": "Rule id/source/page used for this finding"
    }}
  ],
  "status": "FAIL",
  "final_report": "Summary of findings..."
}}
If no violations are found, return:
{{
  "compliance_results": [],
  "status": "PASS",
  "final_report": "No policy violations were found."
}}
""".strip()

    user_message = f"""
VIDEO_METADATA :{state.get('video_metadata', {})}
TRANSCRIPT : {transcript}
ON-SCREEN TEXT (OCR) : {ocr_text}
""".strip()

    try:
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]
        )
        parsed = parse_json_object_from_llm(str(response.content))
    except Exception as e:
        logger.error("Failed to parse audit response: %s", str(e))
        return {
            **merge_checkpoint_state(state, updates={"audio_content_audit": "failed"}),
            "errors": [f"LLM response parse error: {str(e)}"],
        }

    raw_results = parsed.get("compliance_results") or []
    issues = []
    for result in raw_results:
        if not isinstance(result, dict):
            continue
        issues.append(
            {
                "category": str(result.get("category", "Compliance")),
                "description": str(result.get("description", "")),
                "severity": str(result.get("severity", "MEDIUM")),
                "timestamp": None,
            }
        )

    final_status = str(parsed.get("status", "PASS" if not issues else "FAIL")).upper()
    if final_status not in {"PASS", "FAIL"}:
        final_status = "FAIL" if issues else "PASS"
    final_report = str(
        parsed.get(
            "final_report",
            "No policy violations were found." if final_status == "PASS" else "Policy violations found.",
        )
    )

    retrieval_mode = getattr(vector_store, "retrieval_mode", RetrievalMode.DENSE)
    checkpoint_detail_update = {
        "rag_top_k": top_k,
        "rag_retrieved_rules_count": len(docs),
        "rag_retrieval_mode": str(retrieval_mode),
        "rag_rule_references": rag_rule_references,
    }

    return {
        **merge_checkpoint_state(
            state,
            updates={"audio_content_audit": "completed"},
            details=checkpoint_detail_update,
        ),
        "compliance_issues": issues,
        "final_status": final_status,
        "final_report": final_report,
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
