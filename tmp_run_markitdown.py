
import os
os.environ["MARKITDOWN_EXTRACT_TABLES_AS_JSON"] = "true"

import sys
sys.path.append(os.path.abspath("../markitdown-server"))
import src.markitdown_server.extensions
from markitdown import MarkItDown

md = MarkItDown()
res = md.convert(r"/Users/andrea/Developer/AI/RAG/ingestion/docling-server/documents/test.docx")
if res and res.text_content:
    with open(r"/Users/andrea/Developer/AI/RAG/ingestion/docling-server/comparison/test_markitdown.md", "w") as f:
        f.write(res.text_content)
