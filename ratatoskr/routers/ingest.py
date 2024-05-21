import logging
import os
from typing import List, Dict

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.responses import JSONResponse
import validators  # For URL validation

from ratatoskr.utils.rag_processor import RagProcessor
from ratatoskr.utils.elasticsearch_integration import ElasticsearchIntegration
from ratatoskr.models import Document  # Import your Pydantic model

router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency
def get_elasticsearch_integration():
    return ElasticsearchIntegration()


def get_rag_processor():
    return RagProcessor(config)


# --- Upload and Process Documents ---
@router.post("/api/upload_documents")
async def upload_documents(
    documents: List[Document], es_integration: ElasticsearchIntegration = Depends(get_elasticsearch_integration)
):
    try:
        for doc in documents:
            if not doc.page_content:  # Check if page_content exists and is not empty
                raise HTTPException(status_code=400, detail="Missing or empty page_content in a document")

        es_integration.extract_and_store_documents_and_vectors(documents)
        return JSONResponse({"message": "Documents uploaded successfully."})
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        logger.exception(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading documents: {e}")


# --- Process URL for RAG ---
@router.post("/api/process_url")
async def process_rag_url(url: str, rag_processor: RagProcessor = Depends(get_rag_processor)):
    try:
        if not validators.url(url):  # Validate URL format
            raise HTTPException(status_code=400, detail="Invalid URL format")

        rag_processor.process_url(url)
        return JSONResponse({"message": "URL processed successfully"})
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.exception(f"Error processing RAG URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Upload and Process File ---
@router.post("/api/upload_file")
async def upload_file(
    file: UploadFile = File(...), rag_processor: RagProcessor = Depends(get_rag_processor)
):
    try:
        # Basic file type validation
        allowed_types = {".txt", ".pdf", ".csv", ".html", ".md", ".json"}
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Save the file to a temporary location
        contents = await file.read()
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        rag_processor.process_file(file_path)
        os.remove(file_path)
        return JSONResponse(
            {"message": f"File '{file.filename}' uploaded and processed successfully."}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")

# --- Store Document in Elasticsearch ---
@router.post("/api/store_document")
async def store_document_in_elastic(
    document: Document, es_integration: ElasticsearchIntegration = Depends(get_elasticsearch_integration)
):  
    try:
        index_name = config.get("ratatoskr", {}).get("index")
        if not document.page_content:  # Check if page_content exists and is not empty
            raise HTTPException(status_code=400, detail="Missing or empty page_content in the document")
        result = es_integration.store_text(index_name, document.dict())
        return JSONResponse(
            {"result": result, "message": "Document stored successfully"}
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"Error storing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to store document")
