from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from ratatoskr.utils.query_processor import QueryProcessor
from ratatoskr.utils.config import load_config


# API Key Authentication Dependency
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key is not None and api_key in load_config["allowed_api_keys"]:
        return api_key
    else:
        raise HTTPException(status_code=401, detail="Invalid API Key")


# Query Processor Dependency
def get_query_processor():
    # You might want to initialize the QueryProcessor with your config here
    return QueryProcessor()

AsyncQueryProcessor = Annotated[
    QueryProcessor, Depends(get_query_processor)
]
