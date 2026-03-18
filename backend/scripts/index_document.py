import sys
import os
import glob
import io
import logging

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from dotenv import load_dotenv

import langchain_core.documents
import langchain_text_splitters

# Reduce Paddle runtime incompatibilities seen with some OCR model ops on Windows.
os.environ.setdefault("FLAGS_use_mkldnn", "0")

# Shim legacy langchain paths required by PaddleX in PaddleOCR runtime.
mock_doc = type(sys)("langchain.docstore.document")
mock_doc.Document = langchain_core.documents.Document
sys.modules["langchain.docstore"] = type(sys)("langchain.docstore")
sys.modules["langchain.docstore.document"] = mock_doc
sys.modules["langchain.text_splitter"] = langchain_text_splitters

from paddleocr import PaddleOCR
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pdf-indexer")


def extract_text_from_image(ocr_engine: PaddleOCR, image_bytes: bytes) -> str:
    """Extract text from image bytes with PaddleOCR."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        result = ocr_engine.predict(img_array)

        lines: list[str] = []
        for page in result or []:
            rec_texts = page.get("rec_texts", []) if isinstance(page, dict) else []
            for text in rec_texts:
                cleaned = (text or "").strip()
                if cleaned:
                    lines.append(cleaned)
        return " ".join(lines).strip()
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def build_text_edges(text: str, edge_chars: int = 120) -> tuple[str, str]:
    """Return start/end snippets for metadata."""
    normalized = " ".join(text.split())
    if not normalized:
        return "", ""
    return normalized[:edge_chars], normalized[-edge_chars:]


def collect_pdf_documents(pdf_path: str, ocr_engine: PaddleOCR) -> list[Document]:
    """Collect both digital text and OCR text as LangChain Documents."""
    documents: list[Document] = []
    file_name = os.path.basename(pdf_path)

    doc_fitz = fitz.open(pdf_path)
    try:
        for page_num in range(len(doc_fitz)):
            page_no = page_num + 1
            page = doc_fitz[page_num]

            # A) Normal digital text from PDF text layer.
            digital_text = page.get_text("text").strip()
            if digital_text:
                start_text, end_text = build_text_edges(digital_text)
                documents.append(
                    Document(
                        page_content=digital_text,
                        metadata={
                            "source": file_name,
                            "page": page_no,
                            "extraction_method": "digital",
                            "content_type": "normal_text",
                            "image_index": None,
                            "image_start_text": start_text,
                            "image_end_text": end_text,
                        },
                    )
                )

            # B) OCR text from each image on page.
            image_list = page.get_images(full=True)
            if image_list:
                logger.info(f"{file_name} page {page_no}: found {len(image_list)} images for OCR")

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc_fitz.extract_image(xref)
                image_bytes = base_image["image"]
                ocr_text = extract_text_from_image(ocr_engine, image_bytes)
                if not ocr_text:
                    continue

                start_text, end_text = build_text_edges(ocr_text)
                documents.append(
                    Document(
                        page_content=ocr_text,
                        metadata={
                            "source": file_name,
                            "page": page_no,
                            "image_index": img_index,
                            "extraction_method": "ocr",
                            "content_type": "image_text",
                            "image_start_text": start_text,
                            "image_end_text": end_text,
                        },
                    )
                )
    finally:
        doc_fitz.close()

    return documents


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    """Create collection for Gemini embeddings."""
    if client.collection_exists(collection_name):
        return

    vector_name = os.getenv("QDRANT_VECTOR_NAME", "transcript_dense_vector")
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            vector_name: models.VectorParams(size=768, distance=models.Distance.COSINE)
        },
    )


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Chunk documents with overlap and attach chunk-level metadata."""
    if not documents:
        return []

    chunk_size = int(os.getenv("PDF_CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("PDF_CHUNK_OVERLAP", "200"))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)

    for idx, chunk in enumerate(chunks):
        chunk_text = chunk.page_content.strip()
        start_text, end_text = build_text_edges(chunk_text, edge_chars=120)
        chunk.metadata["chunk_index"] = idx
        chunk.metadata["chunk_char_count"] = len(chunk_text)
        chunk.metadata["chunk_start_text"] = start_text
        chunk.metadata["chunk_end_text"] = end_text
        chunk.metadata["chunk_text"] = chunk_text
        # Ensure requested metadata keys always exist.
        chunk.metadata.setdefault("image_start_text", "")
        chunk.metadata.setdefault("image_end_text", "")

    return chunks


def upload_embeddings(
    client: QdrantClient,
    collection_name: str,
    chunks: list[Document],
) -> None:
    """Embed chunks and store vectors + metadata in Qdrant."""
    if not chunks:
        return

    vector_name = os.getenv("QDRANT_VECTOR_NAME", "transcript_dense_vector")
    embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    embedding_dimensions = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "1536"))
    embeddings = GoogleGenerativeAIEmbeddings(
        model=embedding_model,
        google_api_key=os.getenv("GEMINI_API_KEY"),
        output_dimensionality=embedding_dimensions,
    )
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        vector_name=vector_name,
    )
    vector_store.add_documents(chunks)


def index_docs() -> None:
    """Ingest PDFs, chunk (with overlap), embed, and store in Qdrant."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.normpath(os.path.join(current_dir, "../../backend/data"))

    qdrant_url = os.getenv("QDRANT_URL")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "YTadCompilance")
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not qdrant_url or not collection_name or not gemini_api_key:
        logger.error(
            "Missing required environment variables: QDRANT_URL, QDRANT_COLLECTION_NAME, GEMINI_API_KEY"
        )
        return

    logger.info(f"Qdrant URL: {qdrant_url}")
    logger.info(f"Qdrant Collection: {collection_name}")

    client = QdrantClient(url=qdrant_url, api_key=os.getenv("QDRANT_API_KEY"))
    ensure_collection(client, collection_name)

    logger.info("Initializing PaddleOCR...")
    ocr_engine = PaddleOCR(use_textline_orientation=True, lang="en")

    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {data_folder}")
        return

    all_documents: list[Document] = []
    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        logger.info(f"Processing PDF: {file_name}")

        try:
            docs = collect_pdf_documents(pdf_path, ocr_engine)
            all_documents.extend(docs)
            logger.info(f"Collected {len(docs)} source documents from {file_name}")
        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}")

    chunks = chunk_documents(all_documents)
    upload_embeddings(client, collection_name, chunks)

    logger.info("=" * 60)
    logger.info("PDF ingestion complete with embeddings.")
    logger.info(f"Total source documents: {len(all_documents)}")
    logger.info(f"Total chunks uploaded: {len(chunks)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    index_docs()
