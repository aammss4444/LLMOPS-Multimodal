import sys
import langchain_core.documents
import langchain_text_splitters

# Shim legacy langchain paths for PaddleOCR
mock_doc = type(sys)('langchain.docstore.document')
mock_doc.Document = langchain_core.documents.Document
sys.modules['langchain.docstore'] = type(sys)('langchain.docstore')
sys.modules['langchain.docstore.document'] = mock_doc
sys.modules['langchain.text_splitter'] = langchain_text_splitters

import os
import glob
import logging
import fitz  # PyMuPDF
import io
from PIL import Image
import numpy as np
from dotenv import load_dotenv

load_dotenv(override=True)

# PaddleOCR and OCR Logic
from paddleocr import PaddleOCR
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Qdrant Vector Store
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Gemini Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("indexer")

def extract_text_from_image(ocr_engine, image_bytes):
    """
    Uses PaddleOCR to extract text from image bytes.
    """
    try:
        # Convert bytes to numpy array for PaddleOCR
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        
        # PaddleOCR expects BGR format if using opencv, but PIL uses RGB
        # However, PaddleOCR's ocr function can take a numpy array directly
        result = ocr_engine.ocr(img_array, cls=True)
        
        text = ""
        if result and result[0]:
            for line in result[0]:
                text += line[1][0] + " "
        return text.strip()
    except Exception as e:
        logger.error(f"Error in OCR extraction: {e}")
        return ""

def index_docs():
    """
    Reads PDFs from backend/data, extracts text via MuPDF (digital) 
    and PaddleOCR (images), chunks them, and uploads vectors to Qdrant.
    """
    # 2. Define Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.normpath(os.path.join(current_dir, "../../backend/data"))
    
    # 3. Debug: Check Environment Variables
    logger.info("=" * 60)
    logger.info("Environment Configuration Check:")
    logger.info(f"GEMINI_API_KEY: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
    logger.info(f"QDRANT_URL: {os.getenv('QDRANT_URL')}")
    logger.info(f"QDRANT_COLLECTION: {os.getenv('QDRANT_COLLECTION_NAME')}")
    logger.info("=" * 60)
    
    # 4. Validate Required Environment Variables
    required_vars = [
        "GEMINI_API_KEY",
        "QDRANT_URL",
        "QDRANT_COLLECTION_NAME"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # 5. Initialize Embedding Model
    try:
        logger.info("Initializing Gemini Embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {e}")
        return
    
    # 6. Initialize Qdrant Client & Vector Store
    try:
        logger.info(f"Connecting to Qdrant at {os.getenv('QDRANT_URL')}...")
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        
        collection_name = os.getenv("QDRANT_COLLECTION_NAME")
        
        # Check if collection exists, create if not
        if not client.collection_exists(collection_name):
            logger.info(f"Creating collection: {collection_name}")
            from qdrant_client.http import models
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
            )
            
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings,
        )
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
        return
    
    # 7. Initialize PaddleOCR once
    logger.info("Initializing PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    # 8. Find PDF Files
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {data_folder}.")
        return
    
    all_docs = []
    
    # 9. Process Each PDF
    for pdf_path in pdf_files:
        logger.info(f"Processing {os.path.basename(pdf_path)} with hybrid method...")
        try:
            doc_fitz = fitz.open(pdf_path)
            file_name = os.path.basename(pdf_path)
            
            for page_num in range(len(doc_fitz)):
                page = doc_fitz[page_num]
                
                # --- Step A: Extract Digital Text ---
                digital_text = page.get_text().strip()
                if digital_text:
                    all_docs.append(Document(
                        page_content=digital_text,
                        metadata={
                            "source": file_name,
                            "page": page_num + 1,
                            "extraction_method": "digital"
                        }
                    ))
                
                # --- Step B: Extract Text from Images ---
                image_list = page.get_images(full=True)
                if image_list:
                    logger.info(f"  -> Page {page_num+1}: Found {len(image_list)} images. Running OCR...")
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc_fitz.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    ocr_text = extract_text_from_image(ocr, image_bytes)
                    if ocr_text:
                        all_docs.append(Document(
                            page_content=ocr_text,
                            metadata={
                                "source": file_name,
                                "page": page_num + 1,
                                "image_index": img_index,
                                "extraction_method": "ocr"
                            }
                        ))
            
            doc_fitz.close()
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")
    
    # 10. Chunking and Upload
    if all_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(all_docs)
        
        logger.info(f"Uploading {len(splits)} chunks to Qdrant collection '{collection_name}'...")
        try:
            vector_store.add_documents(documents=splits)
            logger.info("=" * 60)
            logger.info("✅ Hybrid Indexing to Qdrant Complete!")
            logger.info(f"Total chunks indexed: {len(splits)}")
            logger.info("=" * 60)
        except Exception as e:
            logger.error(f"Failed to upload documents to Qdrant: {e}")
    else:
        logger.warning("No documents were processed.")

if __name__ == "__main__":
    index_docs()