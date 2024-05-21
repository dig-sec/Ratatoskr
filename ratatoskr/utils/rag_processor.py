import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from langchain.document_loaders import (
    CSVLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
    JSONLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import OllamaEmbeddings
from fastapi import HTTPException

from ratatoskr.utils.config import load_config


logger = logging.getLogger(__name__)

class RagProcessor:
    def __init__(self, config: dict, max_threads: int = 4):
        self.max_threads = max_threads
        self.config = config
        self.ollama_embedding = OllamaEmbeddings(
            base_url=self.config["ollama"]["base_url"],
            model=self.config["ollama"]["model"],
        )

    def _load_document(self, file_path: str) -> List[dict]:
        """Loads documents and split it into chunks."""
        loader_class = {
            ".csv": CSVLoader,
            ".html": UnstructuredHTMLLoader,
            ".json": JSONLoader,
            ".md": UnstructuredMarkdownLoader,
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
        }
        ext = os.path.splitext(file_path)[1]
        if ext in loader_class:
            loader = loader_class[ext](file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        data = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
        return text_splitter.split_documents(data)

    def process_file(self, file_path: str):
        try:
            docs = self._load_document(file_path)
            ElasticsearchStore.from_documents(
                docs,
                self.ollama_embedding,
                es_url=self.config['elastic']['hosts'],
                index_name=self.config['ratatoskr']['index'],
                es_user=self.config['elastic']['http_auth'][0],
                es_password=self.config['elastic']['http_auth'][1]
            )
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {e}")
  
    def process_url(self, url: str):
        try:
            loader = WebBaseLoader(url)
            docs = self._load_document(url)

            ElasticsearchStore.from_documents(
                docs,
                self.ollama_embedding,
                es_url=self.config["elastic"]["hosts"],
                index_name=self.config["ratatoskr"]["index"],
                es_user=self.config["elastic"]["http_auth"][0],
                es_password=self.config["elastic"]["http_auth"][1],
            )
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing URL: {e}")
