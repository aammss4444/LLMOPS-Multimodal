import sys
import traceback

print("--- Detailed Import Trace ---")

def try_import(module_name):
    print(f"Trying to import {module_name}...")
    try:
        __import__(module_name)
        print(f"  SUCCESS: {module_name} imported.")
    except Exception:
        print(f"  FAILURE: {module_name} failed.")
        traceback.print_exc()
        print("-" * 40)

# Check basic langchain first
try_import("langchain_core")
try_import("langchain")

# Check if docstore actually exists anywhere
print("\nChecking for docstore...")
try:
    import langchain.docstore
    print("  langchain.docstore exists")
except ImportError:
    print("  langchain.docstore NOT found (expected in recent versions)")

# Now check paddleocr
print("\nChecking paddleocr...")
try_import("paddleocr")

print("\n--- Diagnostic End ---")
