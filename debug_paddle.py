import sys
import os

print("Python version:", sys.version)
print("CWD:", os.getcwd())
print("Files in CWD:", os.listdir())
print("sys.path:", sys.path)

try:
    print("\nAttempting import paddleocr...")
    import paddleocr
    print("SUCCESS")
except Exception:
    import traceback
    traceback.print_exc()
