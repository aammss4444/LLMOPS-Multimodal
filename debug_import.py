import traceback
import sys

print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    print("\nAttempting to import paddleocr...")
    import paddleocr
    print("SUCCESS: paddleocr imported")
except Exception:
    print("\nFAILURE: paddleocr import failed")
    traceback.print_exc()

try:
    print("\nAttempting to import langchain_qdrant...")
    import langchain_qdrant
    print("SUCCESS: langchain_qdrant imported")
except Exception:
    print("\nFAILURE: langchain_qdrant import failed")
    traceback.print_exc()

try:
    print("\nAttempting to import qdrant_client...")
    import qdrant_client
    print("SUCCESS: qdrant_client imported")
except Exception:
    print("\nFAILURE: qdrant_client import failed")
    traceback.print_exc()
