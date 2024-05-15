# Ratatoskr: A Comprehensive Information Retrieval and Knowledge Management Platform

## Overview

Ratatoskr is a powerful tool designed to streamline information retrieval and knowledge management. It leverages advanced technologies to process, store, and retrieve information from diverse sources, including uploaded documents, URLs, and Elasticsearch databases.

## Key Features

- **Interactive Querying:** Ratatoskr enables users to interact with a language model (Ollama) through a user-friendly interface to ask questions and get answers. It supports both direct querying and retrieval-augmented generation (RAG) for more contextually relevant responses.
- **Query Status Tracking:** Users can track the status of their queries to monitor progress.
- **Metadata Summary Generation:** The system can summarize metadata information from various sources.
- **Document Processing:** Ratatoskr can process both uploaded files (with type validation) and URLs (with RAG support) to extract information and store it for future retrieval.
- **Elasticsearch Integration:** It seamlessly integrates with Elasticsearch to store and retrieve documents and vectors, enabling powerful search capabilities and similarity-based retrieval.
- **Threading for Asynchronous Operations:**  Uses threading to handle long-running tasks like query processing, improving the responsiveness of the application.

## Technologies Used

- **Flask:** A lightweight web framework for building the API and user interface.
- **Ollama:** A local LLM model used for interactive querying and response generation.
- **Elasticsearch:** A distributed search and analytics engine for document and vector storage.
- **LangChain:** A framework for developing applications powered by language models.
- **Hugging Face Embeddings:** Embeddings models used for semantic search and similarity calculations.
- **YAML:** Used for storing configuration settings.

## Installation and Setup

1. **Clone the Repository:** 
   ```bash
   git clone <repository-url>
   ```
2. **Create a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure:**
   - Update `config.yaml` with your Elasticsearch connection details, Ollama model settings, and other preferences.
5. **Start the Server:**
   ```bash
   python src/main.py
   ```

## API Endpoints

- **`/api/query` (POST):** Submit an interactive query.
- **`/api/query_status` (GET):** Get the status of a query.
- **`/api/query_rag` (POST):** Query the RAG database.
- **`/api/metadata_summary` (POST):** Get metadata summaries.
- **`/api/upload_file` (POST):** Upload a file for processing.
- **`/api/process_url` (POST):** Process a URL for RAG.
- **`/store_document_in_elastic` (POST):** Store a document in Elasticsearch.
- **`/query_vector_in_elastic` (POST):** Query Elasticsearch using a vector.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
