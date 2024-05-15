"""
Start thread to load uploaded file in to rag database.
One as knowledge of thruth and one as a summary sparce index summary.
then remove the file

Same for url link
"""
from concurrent.futures import ThreadPoolExecutor
from langchain_community.document_loaders import (
    CSVLoader, 
    UnstructuredHTMLLoader, 
    JSONLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
    TextLoader,
    WebBaseLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
from pathlib import Path
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.embeddings import OllamaEmbeddings
import logging
logging.basicConfig(level=logging.ERROR, filemode='a', filename='ratatoskr.log', format='%(asctime)s - %(levelname)s - %(message)s - Source: rag_handler.py')

class RagProcessor:
    def __init__(self, config_file: dict, max_threads=4):
        self.max_threads = max_threads
        self.config = config_file
        self.ollama_embedding = OllamaEmbeddings(base_url=self.config['ollama']['base_url'], model=self.config['ollama']['model'])

    def process_file(self, file_path: str):
        try:
            # Load the file
            data = None
            if file_path.endswith('.csv'):
                loader = CSVLoader(file_path)
                data = loader.load_and_split()
            elif file_path.endswith('.html'):
                loader = UnstructuredHTMLLoader(file_path)
                data = loader.load()
            elif file_path.endswith('.json'):
                loader = JSONLoader(file_path)
                data = json.loads(Path(file_path).read_text())
            elif file_path.endswith('.md'):
                loader = UnstructuredMarkdownLoader(file_path)
                data = loader.load()
            elif file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                data = loader.load_and_split()
            elif file_path.endswith('.txt'):
                loader = TextLoader(file_path)
                data = loader.load()

            # Splitter
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
            all_splits = text_splitter.split_documents(data)

            # Parse filename from file_path
            # filename = file_path.split('/')[-1]

            db = ElasticsearchStore.from_documents(
                all_splits,
                self.ollama_embedding,
                es_url=self.config['elastic']['hosts'],
                index_name=self.config['ratatoskr']['index'],
                es_user=self.config['elastic']['http_auth'][0],
                es_password=self.config['elastic']['http_auth'][1]
            )

            db.client.indices.refresh(index=self.config['elastic']['index'])

        except Exception as e:
            print("Error processing file: " + file_path + " Error: " + str(e))

    # def process_files(self, list_of_files):
    #     threads = []
    #     with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
    #         for file_path in tqdm(list_of_files):
    #             try:
    #                 t = executor.submit(self.process_file, file_path)
    #                 threads.append(t)
    #             except Exception as e:
    #                 print("Error processing file: " + file_path + " Error: " + str(e))

    #     # Wait for all threads to finish
    #     for t in threads:
    #         t.result()


    def process_url(self, url: str):
        loader = WebBaseLoader(url)
        data = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
        all_splits = text_splitter.split_documents(data)

        db = ElasticsearchStore.from_documents(
            all_splits,
            self.ollama_embedding,
            es_url=self.config['elastic']['hosts'],
            index_name=self.config['ratatoskr']['index'],
            es_user=self.config['elastic']['http_auth'][0],
            es_password=self.config['elastic']['http_auth'][1]
        )

        db.client.indices.refresh(index=self.config['ratatoskr']['index'])

