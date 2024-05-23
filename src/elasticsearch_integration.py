import logging
from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from langchain_elasticsearch.vectorstores import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from typing import Dict, List, Optional

from logging_config import logger
from config_utils import load_config


class ElasticsearchIntegration:
    """A class to handle Elasticsearch operations."""

    def __init__(self, config_file: str = "config.yaml"):
        """Initialize the ElasticsearchIntegration object."""
        self.config = load_config(config_file)
        if self.config is None:
            raise ValueError("Invalid or missing configuration. Exiting.")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.es = Elasticsearch(**self.config.get("elastic"))

    def __del__(self):
        """Close the Elasticsearch connection when the object is deleted."""
        if hasattr(self, "es") and self.es:
            self.es.close()

    def close_connection(self):
        """Close the Elasticsearch connection."""
        self.es.close()

    def text_search(self, index, query):
        res = self.es.search(index=index, body=query)
        return res['hits']['hits']

    def store_text(self, index: str, document: Dict[str, str]) -> str:
        """Store text in the specified index."""
        res = self.es.index(index=index, body=document)
        return res["result"]

    def extract_and_store_documents_and_vectors(self, data: List[str]):
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
            logging.error(f"Failed to store documents and vectors: {e}")
            raise
    
    def query_vector(self, query: str, k: int = 10) -> List[Dict[str, str]]:
        """Query vector from the database."""
        db = ElasticsearchStore(
            embedding=self.embeddings,
            es_url=self.config["elastic"]["hosts"],
            index_name=self.config["rag_database"]["index"],
            es_user=self.config["elastic"]["http_auth"][0],
            es_password=self.config["elastic"]["http_auth"][1],
        )
        results = db.similarity_search(query, k=k)
        db.client.close()
        return results

    def rag_retrieval_qa(self, question: str) -> Dict[str, str]:
        """Retrieve QA from the database."""
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
        db.client.close()
        return qachain({"query": question})

    def query_document(self, query):
        results = self.text_search(self.config['ratatoskr']['index'], query)
        return results

    def query_rag_database_document(
        self, query: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """Query document from the RAG database."""
        results = self.text_search(self.config["rag_database"]["index"], query)
        return results

    def store_document(self, document: Dict[str, str], index: Optional[str] = None) -> str:
        """Store document in the database. Used by query status."""
        if index is None:
            index = self.config["ratatoskr"]["index"]
        result = self.store_text(index, document)
        return result

    def update_query(self, update_query: str) -> Dict[str, str]:
        """Update query in the database."""
        res = self.es.update_by_query(
            index=self.config["ratatoskr"]["index"], body=update_query
        )
        return res

    def raw_text_search(self, query, index=None):
        if index is None:
            index = self.config["rag_database"]["index"]
        res = self.es.search(body=query, index=index)
            
        return res["hits"]["hits"]