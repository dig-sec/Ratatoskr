import os
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import (
    CSVLoader, UnstructuredHTMLLoader, JSONLoader, UnstructuredMarkdownLoader,
    PyPDFLoader, TextLoader, AsyncChromiumLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from elasticsearch_integration import ElasticsearchIntegration
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain.schema import Document
from logging_config import logger
from config_utils import load_config

class RagProcessor:
    def __init__(self, config_file='config.yaml', max_threads=4):
        self.max_threads = max_threads
        self.config = load_config(config_file)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)

    def process_string_to_vector_db(self, text: str):
        try:
            string_document = Document(page_content=text)
            all_splits = self.text_splitter.split_documents([string_document])
            elastic_connection = ElasticsearchIntegration()
            elastic_connection.extract_and_store_documents_and_vectors(all_splits)
        except Exception as e:
            logger.error(f"Error processing string: {e}")
        finally:
            elastic_connection.close_connection()

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
            loader = AsyncChromiumLoader([url])
            html = loader.load()

            bs_transformer = BeautifulSoupTransformer()
            docs_transformed = bs_transformer.transform_documents(html, tags_to_extract=["p", "h1", "h2", "h3", "h4", "h5", "h6", "span"])

            elastic_connection = ElasticsearchIntegration()
            elastic_connection.extract_and_store_documents_and_vectors(docs_transformed)

            logger.info(f"Processed and stored URL: {url}")
        except Exception as e:
            logger.error(f"Error processing URL '{url}': {e}")
        finally:
            elastic_connection.close_connection()

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
