# Ratatoskr

A Comprehensive Information Retrieval and Knowledge Management Platform

<p align="center">
    <img src="src/static/images/ratatoskr_loading.gif" alt="Loading" style="border-radius: 50%;" height="30%" width="30%">
</p>

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

## Installation

1. **Clone the Repository:**

   ```bash
   git clone [https://github.com/](https://github.com/)<your-username>/ratatoskr.git
   cd ratatoskr
   ```
   
2. **Install Dependencies:**
   ```bash
   python3 -m venv .venv 
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **(Optional) Docker Setup:**
    If you prefer using Docker:
   ```bash
   docker build -t ratatoskr .
   docker run -it --rm \
      --name ratatoskr \
      -p 6666:6666 \
      -v $(pwd)/config.yaml:/app/config.yaml \
      ratatoskr
   ```

4. **Configuration:**
   * Rename `config_sample.yaml` to `config.yaml`.
   * Update `config.yaml` with your specific settings.

5. **Start Ratatoskr:**

    - From Source:
        ```bash
        python src/main.py
        ```
    - Using Docker:
        ```bash
        docker start ratatoskr
        ```

Now you can access Ratatoskr at `http://localhost:6666`.


## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.
