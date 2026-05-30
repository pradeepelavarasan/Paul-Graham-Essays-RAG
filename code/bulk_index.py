import sys
import os
from pathlib import Path

# Add the code directory to path so we can import services
code_dir = Path('/Users/pradeep/Library/CloudStorage/OneDrive-Personal/ML/2026 ML Projects/EAG Session7 RAG/code')
sys.path.insert(0, str(code_dir))

import memory
from mcp_server import index_document

# Clear memory first to avoid duplicates and ensure a clean run
print("Wiping existing memory index...")
memory.clear()

essays_dir = code_dir / "sandbox" / "Paul Graham Essays"
json_files = sorted([f for f in os.listdir(essays_dir) if f.endswith('.json')])

total_essays = len(json_files)
total_chunks = 0
indexed_count = 0

print(f"Found {total_essays} JSON essay files to index.")

for idx, filename in enumerate(json_files, 1):
    path_in_sandbox = f"Paul Graham Essays/{filename}"
    try:
        res = index_document(path_in_sandbox)
        chunks = res.get("chunks_indexed", 0)
        total_chunks += chunks
        indexed_count += 1
        print(f"[{idx}/{total_essays}] Indexed '{filename}' -> {chunks} chunks.")
    except Exception as e:
        print(f"[{idx}/{total_essays}] Error indexing '{filename}': {e}")

print("\n--- Indexing Summary ---")
print(f"Successfully indexed essays: {indexed_count}/{total_essays}")
print(f"Total chunks indexed: {total_chunks}")
