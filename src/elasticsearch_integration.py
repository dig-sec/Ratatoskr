import logging
from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from langchain_elasticsearch.vectorstores import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from config_utils import load_config
from logging_config import logger

class ElasticsearchIntegration:
    """A class to handle Elasticsearch operations."""

    def __init__(self):
        """Initialize the ElasticsearchIntegration object."""
        self.config = load_config()
        if not self.config or not all(key in self.config for key in ["elastic", "rag_database", "ratatoskr"]):
            raise ValueError("Invalid or missing configuration. Exiting.")

        # Update to the new embeddings class
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Initialize Elasticsearch with retries
        try:
            self.es = Elasticsearch(
                hosts=self.config["elastic"]["hosts"],
                http_auth=tuple(self.config["elastic"]["http_auth"]),
                retry_on_timeout=True,
                max_retries=5,
            )
            if not self.es.ping():
                raise ConnectionError("Elasticsearch server is not reachable. Check the connection settings.")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}", exc_info=True)
            raise


    def __del__(self):
        """Close the Elasticsearch connection when the object is deleted."""
        self.close_connection()

    def close_connection(self):
        """Close the Elasticsearch connection."""
        if hasattr(self, "es") and self.es:
            self.es.close()

    def text_search(self, index: str, query: Dict) -> List[Dict]:
        """Perform a text search in the specified index."""
        try:
            res = self.es.search(index=index, body=query)
            return res['hits']['hits']
        except Exception as e:
            logger.error(f"Elasticsearch text search failed: {e}")
            raise

    def store_text(self, index: str, document: Dict[str, str]) -> str:
        """Store text in the specified index."""
        try:
            res = self.es.index(index=index, body=document)
            return res["result"]
        except Exception as e:
            logger.error(f"Failed to store document in index '{index}': {e}")
            raise

    def extract_and_store_documents_and_vectors(self, data: List[str]) -> None:
        """Extract and store documents and vectors."""
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
        all_splits = text_splitter.split_documents(data)

        try:
            ElasticsearchStore.from_documents(
                all_splits,
                self.embeddings,
                es_url=self.config["elastic"]["hosts"],
                index_name=self.config["rag_database"]["index"],
                es_user=self.config["elastic"]["http_auth"][0],
                es_password=self.config["elastic"]["http_auth"][1],
            )
        except Exception as e:
            logger.error(f"Failed to store documents and vectors: {e}")
            raise

    def query_vector(self, query: str, k: int = 10) -> List[Dict[str, str]]:
        """Query vector from the database."""
        try:
            db = ElasticsearchStore(
                embedding=self.embeddings,
                es_url=self.config["elastic"]["hosts"],
                index_name=self.config["rag_database"]["index"],
                es_user=self.config["elastic"]["http_auth"][0],
                es_password=self.config["elastic"]["http_auth"][1],
            )
            results = db.similarity_search(query, k=k)
            return results
        finally:
            db.client.close()

    def rag_retrieval_qa(self, question: str) -> Dict[str, str]:
        """Retrieve QA from the database."""
        try:
            db = ElasticsearchStore(
                embedding=self.embeddings,
                es_url=self.config["elastic"]["hosts"],
                index_name=self.config["rag_database"]["index"],
                es_user=self.config["elastic"]["http_auth"][0],
                es_password=self.config["elastic"]["http_auth"][1],
            )
            qachain = RetrievalQA.from_chain_type(
                self.embeddings, retriever=db.as_retriever()
            )
            return qachain({"query": question})
        finally:
            db.client.close()

    def query_document(self, query: Dict) -> List[Dict]:
        """Query a document from the Ratatoskr index."""
        return self.text_search(self.config["ratatoskr"]["index"], query)

    def query_rag_database_document(self, query: Dict) -> List[Dict]:
        """Query a document from the RAG database."""
        return self.text_search(self.config["rag_database"]["index"], query)

    def store_document(self, document: Dict[str, str], index: Optional[str] = None) -> str:
        # logg the document
        logger.info(f"Storing document: {document}")
        """Store a document in the specified index."""
        index = index or self.config["ratatoskr"]["index"]
        return self.store_text(index, document)

    def update_query(self, update_query: Dict) -> Dict:
        """Update a document in the database."""
        try:
            return self.es.update_by_query(
                index=self.config["ratatoskr"]["index"], body=update_query
            )
        except Exception as e:
            logger.error(f"Failed to update query: {e}")
            raise
