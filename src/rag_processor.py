import os
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import (
    CSVLoader, UnstructuredHTMLLoader, JSONLoader, UnstructuredMarkdownLoader,
    PyPDFLoader, TextLoader, WebBaseLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from elasticsearch_integration import ElasticsearchIntegration

from logging_config import logger
from config_utils import load_config

class RagProcessor:
    def __init__(self, config_file='config.yaml', max_threads=4):
        self.max_threads = max_threads
        self.config = load_config(config_file)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)

    def process_file(self, file_path: str):
        try:
            loader = self._get_loader(file_path)
            documents = loader.load()
            all_splits = self.text_splitter.split_documents(documents)

            # Extract metadata (source, optional title, etc.)
            metadatas = [{ "source": file_path }] * len(all_splits)

            # Store documents and vectors in Elasticsearch
            elastic_connection = ElasticsearchIntegration(self.config)
            elastic_connection.extract_and_store_documents_and_vectors(all_splits, metadatas) 

            logger.info(f"Processed and stored file: {file_path}")
            
            # Remove file after processing
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error processing file '{file_path}': {e}")

    def process_files(self, list_of_files: list):
        """Processes multiple files concurrently."""
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(self.process_file, file_path) for file_path in list_of_files]
            for future in futures:
                future.result()

    def process_url(self, url: str):
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            all_splits = self.text_splitter.split_documents(documents)
            metadatas = [{ "source": url }] * len(all_splits)

            # Store in Elasticsearch
            elastic_connection = ElasticsearchIntegration(self.config)
            elastic_connection.extract_and_store_documents_and_vectors(all_splits, metadatas)

            logger.info(f"Processed and stored URL: {url}")
        except Exception as e:
            logger.error(f"Error processing URL '{url}': {e}")

    def _get_loader(self, file_path: str):
        ext = file_path.split('.')[-1].lower()
        loaders = {
            'csv': CSVLoader,
            'html': UnstructuredHTMLLoader,
            'json': JSONLoader,
            'md': UnstructuredMarkdownLoader,
            'pdf': PyPDFLoader,
            'txt': TextLoader,
        }
        return loaders.get(ext, TextLoader)(file_path) 
