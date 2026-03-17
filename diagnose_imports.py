import traceback
import sys
import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("--- Diagnostic Start ---")
try:
    print("Testing langchain_core.documents.Document import...")
    from langchain_core.documents import Document
    print("Success: Document imported.")
except Exception as e:
    print(f"Error importing Document: {e}")
    traceback.print_exc()

try:
    print("\nTesting paddleocr import...")
    import paddleocr
    print(f"Success: paddleocr imported. Version: {getattr(paddleocr, '__version__', 'unknown')}")
except Exception as e:
    print(f"Error importing paddleocr: {e}")
    traceback.print_exc()

try:
    print("\nTesting PaddleOCR initialization...")
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    print("Success: PaddleOCR initialized.")
except Exception as e:
    print(f"Error initializing PaddleOCR: {e}")
    traceback.print_exc()

try:
    print("\nTesting langchain_qdrant import...")
    import langchain_qdrant
    print("Success: langchain_qdrant imported.")
except Exception as e:
    print(f"Error importing langchain_qdrant: {e}")
    traceback.print_exc()

print("\n--- Diagnostic End ---")
