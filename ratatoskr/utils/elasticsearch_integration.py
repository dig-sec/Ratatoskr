import logging
import os
from typing import Dict, List

from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from elasticsearch import Elasticsearch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from ratatoskr.utils.config import load_config


logger = logging.getLogger(__name__)

class ElasticsearchIntegration:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = load_config(config_file)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.es = Elasticsearch(**self.config.get("elastic"))

    def __del__(self):
        if self.es:
            self.es.close()
  
    # ... your existing methods (text_search, store_text, etc.)
    
    def extract_and_store_documents_and_vectors(self, documents: List[Dict]):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
        all_splits = []
        for doc in documents:
            all_splits.extend(text_splitter.split_text(doc['page_content']))

        try:
            ElasticsearchStore.from_texts(
                all_splits,
                self.embeddings,
                es_url=self.config['elastic']['hosts'],
                index_name=self.config['rag_database']['index'],
                es_user=self.config['elastic']['http_auth'][0],
                es_password=self.config['elastic']['http_auth'][1]
            )
        except Exception as e:  # Catch more specific exceptions if possible
            logger.error(f"Failed to store documents and vectors: {e}")
            raise
