from pathlib import Path
import shutil
from app.analytics.supplier_service import (
    add_supplier_alias,
    list_supplier_aliases,
    delete_supplier_alias,
    resolve_supplier,
)
from app.dashboard.service import get_dashboard_summary
from fastapi.middleware.cors import CORSMiddleware
from app.health.service import get_system_health
from app.errors.handlers import (
    register_exception_handlers,
)

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.ingestion.indexer import index_pdf

from app.rag.service import ask_rag
from app.rag.vector_store import (
    delete_document_chunks,
    get_document_records,
)

from app.analytics.service import ask_data
from app.analytics.dataset_service import (
    ingest_structured_file,
    list_datasets,
    get_dataset_preview,
)

from app.routing.service import ask_supplychain_copilot


# ==================================================
# FastAPI app
# ==================================================

app = FastAPI(
    title="SupplyChain Copilot API",
    version="0.4.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# Storage folders
# ==================================================

DOCUMENT_DIR = Path("data/documents")

DOCUMENT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


STRUCTURED_DIR = Path("data/structured")

STRUCTURED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ==================================================
# Request models
# ==================================================

class ChatRequest(BaseModel):
    question: str


class DataQueryRequest(BaseModel):
    question: str


class AskRequest(BaseModel):
    question: str

class SupplierAliasRequest(BaseModel):
    alias_name: str
    canonical_name: str


# ==================================================
# Health
# ==================================================

@app.get("/health")
def health():
    return get_system_health()

@app.get("/dashboard")
def dashboard():
    try:
        return get_dashboard_summary()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

@app.get("/suppliers/aliases")
def get_supplier_aliases():
    return {
        "count": len(
            list_supplier_aliases()
        ),
        "aliases": list_supplier_aliases(),
    }


@app.post("/suppliers/aliases")
def create_supplier_alias(
    request: SupplierAliasRequest,
):
    try:
        result = add_supplier_alias(
            alias_name=request.alias_name,
            canonical_name=request.canonical_name,
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.delete(
    "/suppliers/aliases/{alias_name}"
)
def remove_supplier_alias(
    alias_name: str,
):
    result = delete_supplier_alias(
        alias_name
    )

    if not result["deleted"]:
        raise HTTPException(
            status_code=404,
            detail="Supplier alias not found.",
        )

    return result


@app.get(
    "/suppliers/resolve/{supplier_name}"
)
def resolve_supplier_api(
    supplier_name: str,
):
    return resolve_supplier(
        supplier_name
    )
@app.get("/suppliers/aliases")
def get_supplier_aliases():
    aliases = list_supplier_aliases()

    return {
        "count": len(aliases),
        "aliases": aliases,
    }
# ==================================================
# DOCUMENTS
# ==================================================

# --------------------------------------------------
# Upload PDF
# --------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Missing filename",
        )

    safe_filename = Path(
        file.filename
    ).name

    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are currently supported",
        )

    file_path = (
        DOCUMENT_DIR
        / safe_filename
    )

    # Remove old embeddings if same document
    # is uploaded again
    delete_document_chunks(
        safe_filename
    )

    # Save file
    with file_path.open(
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )

    # Automatically index PDF
    try:
        result = index_pdf(
            file_path
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return {
        "status": "indexed",
        **result,
    }


# --------------------------------------------------
# List PDF documents
# --------------------------------------------------

@app.get("/documents")
def list_documents():

    documents = []

    for file_path in DOCUMENT_DIR.glob(
        "*.pdf"
    ):
        records = get_document_records(
            file_path.name
        )

        metadatas = records.get(
            "metadatas",
            []
        )

        pages = set()

        for metadata in metadatas:
            if metadata:
                page = metadata.get(
                    "page"
                )

                if page is not None:
                    pages.add(page)

        documents.append(
            {
                "filename": file_path.name,

                "pages": len(
                    pages
                ),

                "chunks": len(
                    records.get(
                        "ids",
                        []
                    )
                ),

                "size_bytes":
                    file_path.stat().st_size,
            }
        )

    return {
        "count": len(
            documents
        ),
        "documents": documents,
    }


# --------------------------------------------------
# Delete PDF
# --------------------------------------------------

@app.delete(
    "/documents/{filename}"
)
def delete_document(
    filename: str
):

    safe_filename = Path(
        filename
    ).name

    # Prevent path traversal
    if safe_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    file_path = (
        DOCUMENT_DIR
        / safe_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    # Delete chunks from ChromaDB
    delete_document_chunks(
        safe_filename
    )

    # Delete PDF from disk
    file_path.unlink()

    return {
        "status": "deleted",
        "document": safe_filename,
    }


# ==================================================
# DOCUMENT RAG
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest
):

    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    return ask_rag(
        question
    )


# ==================================================
# STRUCTURED DATA
# ==================================================

# --------------------------------------------------
# Upload CSV / XLSX
# --------------------------------------------------

@app.post("/data/upload")
async def upload_data(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Missing filename",
        )

    safe_filename = Path(
        file.filename
    ).name

    extension = Path(
        safe_filename
    ).suffix.lower()

    allowed_extensions = {
        ".csv",
        ".xlsx",
    }

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only CSV and XLSX files "
                "are currently supported"
            ),
        )

    file_path = (
        STRUCTURED_DIR
        / safe_filename
    )

    # Save file
    with file_path.open(
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer,
        )

    # Import into DuckDB
    try:
        result = ingest_structured_file(
            file_path
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    return {
        "status": "loaded",
        **result,
    }


# --------------------------------------------------
# List structured datasets
# --------------------------------------------------

@app.get("/data/datasets")
def datasets():

    items = list_datasets()

    return {
        "count": len(
            items
        ),
        "datasets": items,
    }


# --------------------------------------------------
# Preview dataset
# --------------------------------------------------

@app.get(
    "/data/datasets/{table_name}"
)
def dataset_details(
    table_name: str
):

    dataset = get_dataset_preview(
        table_name
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    return dataset


# --------------------------------------------------
# Direct structured-data question
# --------------------------------------------------

@app.post("/data/query")
def query_data(
    request: DataQueryRequest
):

    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    return ask_data(
        question
    )


# ==================================================
# MAIN COPILOT ROUTER
# ==================================================

@app.post("/ask")
def ask(
    request: AskRequest
):

    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    return ask_supplychain_copilot(
        question
    )
