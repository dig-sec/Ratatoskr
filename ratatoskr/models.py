from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union

class QueryRequest(BaseModel):
    query: str
    model: str
    user: Optional[str] = None
    session: Optional[str] = None
    query_id: Optional[str] = None
    use_rag_database: bool = False

class QueryStatusResponse(BaseModel):
    query_id: str
    status: str


class DocumentMetadata(BaseModel):
    source: str

class QueryRAGResponse(BaseModel):
    page_content: str
    metadata_source: str

class MetadataSummaryResponse(BaseModel):
    source: str
    document_summary: Union[str, List[Dict]] 

class Document(BaseModel):
    page_content: str
    metadata: DocumentMetadata
