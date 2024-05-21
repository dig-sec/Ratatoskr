import logging
import asyncio
import time
import threading
from typing import Optional
from ratatoskr.utils.llm_handler import LLMHandler  
from ratatoskr.utils.elasticsearch_integration import ElasticsearchIntegration
from ratatoskr.utils.config import load_config
import concurrent.futures

logger = logging.getLogger(__name__)
lock = threading.Lock()

class QueryProcessor:
    def __init__(self):
        self.llm_handler = LLMHandler()
        self.es_integration = ElasticsearchIntegration()

    async def _run_llm(self, query: str, model: str) -> Optional[str]:
        """Asynchronously runs the LLM query."""
        return await self.llm_handler.run_query(query, model)

    async def _run_and_update_status(self, query_id: str, query: str, model: str, user: Optional[str] = None, session: Optional[str] = None):
        """Asynchronously runs the query and updates the status in Elasticsearch."""
        start_time = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                answer = await loop.run_in_executor(executor, self._run_llm, query, model)

            end_time = time.time()
            processing_time = round(end_time - start_time, 2)

            update_query = {
                "script": {
                    "source": f"ctx._source.answer='{answer}'; ctx._source.status='completed'; ctx._source.processing_time={processing_time}",
                },
                "query": {"term": {"query_id": query_id}},
            }
            self.es_integration.update_query(update_query)
            logger.info(f"Query {query_id} completed in {processing_time} seconds.")

        except Exception as e:
            self.es_integration.update_query(
                {
                    "script": {
                        "source": f"ctx._source.status='error'; ctx._source.error='{e}'",
                    },
                    "query": {"term": {"query_id": query_id}},
                }
            )
            logger.error(f"Error processing query {query_id}: {e}")

    def process_query(self, query_id: str, query: str, model: str, user: Optional[str] = None, session: Optional[str] = None, use_rag_database: bool = False) -> None:
        """Processes a query and initiates an asynchronous task."""
        try:
            with lock:  # Acquire lock for shared resource (Elasticsearch)
                # Create initial document in Elasticsearch
                self.es_integration.store_document({
                    "query_id": query_id,
                    "query": query,
                    "model": model,
                    "user": user,
                    "session": session,
                    "use_rag_database": use_rag_database,
                    "status": "submitted",
                })
    
            asyncio.run(self._run_and_update_status(query_id, query, model, user, session))
        except Exception as e:
            logger.error(f"Error starting query processing: {e}")
