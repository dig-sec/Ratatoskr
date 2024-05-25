# Ratatoskr

<p align="center">
    <img src="src/static/images/ratatoskr_loading.gif" alt="Loading" style="border-radius: 50%;" height="50%" width="50%">
</p>

A Comprehensive Information Retrieval and Knowledge Management Platform

## Overview

Ratatoskr is a tool designed to streamline information retrieval and knowledge management.

## Key Features

- **Interactive Querying:** Ratatoskr enables users to interact with a language model (Ollama) through a user-friendly interface to ask questions and get answers. It supports both direct querying and retrieval-augmented generation (RAG) for more contextually relevant responses.
- **Metadata Summary Generation:** The system can summarize metadata information from various sources.
- **Document Processing:** Ratatoskr can process both uploaded files (with type validation) and URLs (with RAG support) to extract information and store it for future retrieval.
- **Elasticsearch Integration:** It seamlessly integrates with Elasticsearch to store and retrieve documents and vectors, enabling powerful search capabilities and similarity-based retrieval.

## Technologies Used

- **Flask:** A lightweight web framework for building the API and user interface.
- **Ollama:** A local LLM model used for interactive querying and response generation.
- **Elasticsearch:** A distributed search and analytics engine for document and vector storage.
- **LangChain:** A framework for developing applications powered by language models.
- **Hugging Face Embeddings:** Embeddings models used for semantic search and similarity calculations.


## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
