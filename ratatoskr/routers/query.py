import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ratatoskr.utils.dependencies import get_query_processor, get_llm_handler
from ratatoskr.models import (
    QueryRequest,
    QueryStatusResponse,
    QueryRAGResponse,
    MetadataSummaryResponse,
)
from ratatoskr.utils.query_handler import (
    process_query,
    query_current_status,
    query_rag_documents,
    query_metadata_source_documents,
)
from ratatoskr.utils.llm_handler import LLMHandler  # Import the LLMHandler

router = APIRouter()
logger = logging.getLogger(__name__)


# --- Interactive Query (Improved) ---
@router.post("/api/query", response_model=QueryStatusResponse)
async def interactive_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,  # Add BackgroundTasks for asynchronous processing
    query_processor=Depends(get_query_processor),
):
    query_id = uuid.uuid4()
    # Use background task to process the query asynchronously
    background_tasks.add_task(
        query_processor.process_query,
        query_id,
        request.query,
        request.model,
        request.user,
        request.session,
        request.use_rag_database,
    )
    return QueryStatusResponse(query_id=str(query_id), status="submitted")

# --- Run LLM (Integrated) ---
@router.post("/api/run_llm")
async def run_llm(query: str, model: str, llm_handler: LLMHandler = Depends(get_llm_handler)):
    answer = await llm_handler.run_query(query, model)
    if answer is None:
        raise HTTPException(status_code=500, detail="Failed to get LLM response")
    return {"answer": answer}


# --- Query Status --- (No changes needed)
@router.get("/api/query_status", response_model=QueryStatusResponse)
def query_status(query_id: str):
    status = query_current_status(query_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Query ID not found")
    return QueryStatusResponse(query_id=query_id, status=status)


# --- Query RAG ---
@router.post("/api/query_rag", response_model=list[QueryRAGResponse])  # Update response model
def query_rag(query: str):
    retrieved_documents = query_rag_documents(query=query)
    formatted_documents = [
        QueryRAGResponse(page_content=doc.page_content, metadata_source=doc.metadata.source)
        for doc in retrieved_documents
    ]
    return formatted_documents


# --- Metadata Summary ---
@router.post("/api/metadata_summary", response_model=list[MetadataSummaryResponse])
def metadata_summary(sources: str):
    metadata_sources = sources.split(",")
    summaries = []
    for source in metadata_sources:
        documents = query_metadata_source_documents(search_string=source)
        if documents:
            summaries.append(MetadataSummaryResponse(source=source, document_summary=documents))
    return summaries
