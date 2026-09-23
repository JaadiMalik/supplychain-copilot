from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma"

LM_STUDIO_URL = "http://127.0.0.1:1234"

LLM_MODEL = "qwen/qwen3.5-9b"

EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5@q8_0"

COLLECTION_NAME = "supplychain_documents"