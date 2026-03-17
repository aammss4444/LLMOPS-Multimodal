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
import fitz  # PyMuPDF
import io
from PIL import Image
import numpy as np
from paddleocr import PaddleOCR
from langchain_core.documents import Document

def extract_text_from_image(ocr_engine, image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        result = ocr_engine.ocr(img_array, cls=True)
        text = ""
        if result and result[0]:
            for line in result[0]:
                text += line[1][0] + " "
        return text.strip()
    except Exception as e:
        print(f"Error in OCR extraction: {e}")
        return ""

def test_extraction():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.normpath(os.path.join(current_dir, "backend/data"))
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {data_folder}")
        return

    print(f"Initializing PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    # Just test first PDF
    pdf_path = pdf_files[0]
    print(f"\n--- Testing Extraction on: {os.path.basename(pdf_path)} ---")
    
    doc_fitz = fitz.open(pdf_path)
    # Test only first 2 pages to keep it fast
    pages_to_test = min(2, len(doc_fitz))
    
    all_results = []
    
    for page_num in range(pages_to_test):
        page = doc_fitz[page_num]
        print(f"\nProcessing Page {page_num+1}...")
        
        # Digital
        digital_text = page.get_text().strip()
        if digital_text:
            print(f" [Digital] Found {len(digital_text)} chars.")
            all_results.append(Document(page_content=digital_text[:100] + "...", metadata={"method": "digital", "page": page_num+1}))
            
        # Images
        image_list = page.get_images(full=True)
        print(f" [Images] Found {len(image_list)} images.")
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc_fitz.extract_image(xref)
            image_bytes = base_image["image"]
            
            ocr_text = extract_text_from_image(ocr, image_bytes)
            if ocr_text:
                print(f"   -> Image {img_index} OCR: Found {len(ocr_text)} chars.")
                all_results.append(Document(page_content=ocr_text[:100] + "...", metadata={"method": "ocr", "page": page_num+1, "img": img_index}))

    doc_fitz.close()
    
    print("\n--- Final Summary of Sample extractions ---")
    for doc in all_results:
        print(f"Method: {doc.metadata['method']} | Page: {doc.metadata['page']} | Snippet: {doc.page_content}")

if __name__ == "__main__":
    test_extraction()
