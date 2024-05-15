import logging
import os
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from elasticsearch import Elasticsearch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
import yaml

import logging
log_file = os.path.join(os.path.dirname(__file__), 'ratatoskr.log') 
logging.basicConfig(
    level=logging.INFO,
    filemode='a',
    filename=log_file,
    format='%(asctime)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d'
)

class ElasticsearchIntegration:
    def __init__(self, config_file='config.yaml'):
        self.config = self.load_config(config_file)
        if self.config is None:
            raise ValueError("Invalid or missing configuration. Exiting.") 
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.es = Elasticsearch(**self.config.get("elastic"))

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as stream:
                return yaml.safe_load(stream)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logging.error(f"Error loading configuration file: {e}")
            return None
        
    def __del__(self):
        if self.es:
            self.es.close()

    def close_connection(self):
        self.es.close()

    def text_search(self, index, query):
        res = self.es.search(index=index, body=query)
        return res['hits']['hits']
    
    def store_text(self, index, document):
        res = self.es.index(index=index, body=document)
        return res['result']
    
    def extract_and_store_documents_and_vectors(self, data):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
        all_splits = text_splitter.split_documents(data)

        # Error handling (Improved)
        try:
            ElasticsearchStore.from_documents(
                all_splits,
                self.embeddings,
                es_url=self.config['elastic']['hosts'],
                index_name=self.config['rag_database']['index'],
                es_user=self.config['elastic']['http_auth'][0],
                es_password=self.config['elastic']['http_auth'][1]
            )
        except Exception as e:  # Catch more specific exceptions if possible
            logging.error(f"Failed to store documents and vectors: {e}")
            raise

    def query_vector(self, query, k=10):
        db = ElasticsearchStore(
            embedding=self.embeddings,
            es_url=self.config['elastic']['hosts'],
            index_name=self.config['rag_database']['index'],
            es_user=self.config['elastic']['http_auth'][0],
            es_password=self.config['elastic']['http_auth'][1]
        )
        results = db.similarity_search(query, k=k)
        db.client.close()
        return results
    
    def rag_retrieval_qa(self, question):
        db = ElasticsearchStore(
            embedding=self.embeddings,
            es_url=self.config['elastic']['hosts'],
            index_name=self.config['rag_database']['index'],
            es_user=self.config['elastic']['http_auth'][0],
            es_password=self.config['elastic']['http_auth'][1]
        )
        qachain = RetrievalQA.from_chain_type(self.embeddings, retriever=db.as_retriever())
        db.client.close()
        return qachain({"query": question})
    
    def query_document(self, query):
        results = self.text_search(self.config['ratatoskr']['index'], query)
        return results

    def query_rag_database_document(self, query):
        results = self.text_search(self.config['rag_database']['index'], query)
        return results
    
    def store_document(self, document):
        result = self.store_text(self.config['ratatoskr']['index'], document)
        return result
    
    def update_query(self, update_query:str):
        res = self.es.update_by_query(index=self.config['ratatoskr']['index'], body=update_query)
        return res