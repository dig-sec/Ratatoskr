import os
import datetime

from flask import abort, jsonify, request
from elasticsearch_integration import ElasticsearchIntegration
from rag_processor import RagProcessor
from llm_handler import LLMHandler

from logging_config import logger

def process_query_safe(*args, **kwargs):
    try:
        process_query(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in process_query: {e}", exc_info=True)

def process_query(query_id: str, user_query: str, model: str, user: str, session=None, use_rag_database=False):
    """
    This function processes the query, retrieves context from the RAG database and/or the session, generates a response using the LLM, and updates the query status in the database.
    """
    # logg process_query
    logger.info(f"Processing query: {query_id}")

    elastic_connection = ElasticsearchIntegration()
    llm_handler = LLMHandler()

    # Insert document of query into the database
    elastic_connection.store_document({
        "query_id": query_id,
        "user": user,
        "query": user_query,
        "status": "processing",
        "session": session,
        "response": "",
        "timestamp": datetime.datetime.now(),
        "type": "chat"
    })

    rag_summary = None
    session_summary = None

    # Get context from the RAG database if use_rag_database is True
    if use_rag_database:
        try:
            rag_results = elastic_connection.query_vector(user_query)
            # Filter out short results
            rag_results = [x for x in rag_results if len(x.page_content) > 200]

            # Extract content and source information
            retrieved_documents_list = [
                {"page_content": doc["page_content"], "metadata_source": doc["metadata"]["source"]} 
                for doc in rag_results
            ]

            # Simplify file paths in metadata_source
            for doc in retrieved_documents_list:
                if doc["metadata_source"].startswith("/mnt/"):
                    doc["metadata_source"] = os.path.basename(doc["metadata_source"])

            # Check if rag_results is empty
            if not retrieved_documents_list:
                rag_results = None
            else:
                rag_query = (
                    f"Create a bullet point summary of the following documents found "
                    f"related to the user query. Page_content is the content found and "
                    f"metadata_source is the source document: {str(retrieved_documents_list)}"
                )
                rag_summary = llm_handler.run_query(query=rag_query, model=model)
        except Exception as e:
            rag_results = None
            logger.warning(f"Error querying RAG database: {e}")

    # Get context based on session value
    if session is not None:
        try:
            session_documents = elastic_connection.query_document({
                "query": {"match": {"session": session}}
            })
            session_documents = [x['_source'] for x in session_documents]
            session_documents = [x for x in session_documents if x['query'] != user_query and x['response'] != ""]

            if not session_documents:
                session_documents = None
            else:
                session_query = f"Summarize: {session_documents}"
                session_summary = llm_handler.run_query(query=session_query, model=model)
        except Exception as e:
            session_documents = None
            logger.warning(f"Error querying session documents: {e}")

    # Generate response based on context
    combined_query = user_query
    if rag_summary and session_summary:
        combined_query += f"\nSummarized content from documents found related to the user query: {rag_summary}\nContext from the current chat session: {session_summary}"
    elif rag_summary:
        combined_query += f"\nSummarized content from documents found related to the user query: {rag_summary}"
    elif session_summary:
        combined_query += f"\nContext from the current chat session: {session_summary}"

    # Run the query through the LLM
    response = llm_handler.run_query(query=combined_query, model=model)

    # Update the document in the database
    update_query = {
        "script": {
            "source": "ctx._source.status = 'completed'; ctx._source.response = params.response",
            "params": {"response": response}
        },
        "query": {"match": {"query_id": query_id}}
    }
    elastic_connection.update_query(update_query)

    # Store response in rag_database
    rag_handler = RagProcessor()
    rag_handler.process_string_to_vector_db(response)

    elastic_connection.close_connection()

def query_current_status(query_id):
    elastic_connection = ElasticsearchIntegration()
    try:
        # Query for the document with the query_id
        elastic_query = {
            "query": {
                "match": {
                    "query_id": query_id
                }
            }
        }

        # Query the database for the document with the query_id
        response = elastic_connection.query_document(elastic_query)

        if response and isinstance(response, list) and len(response) > 0:
            hit = response[0]
            status = hit['_source'].get('status')
            
            if status == 'completed' or status == 'processing':
                return hit['_source']
        
        return None

    except Exception as e:
        logger.exception("Exception occurred while querying current status:", exc_info=True)
        return None
    finally:
        elastic_connection.close_connection()

def query_rag_documents(query):
    elastic_connection = ElasticsearchIntegration()
    try:
        # Query the database for the document with the query_id
        response = elastic_connection.query_vector(query)

        # If response is empty, return None
        if response is None:
            return None
        else:
            return response

    except Exception as e:
        logger.exception("Exception occurred while querying RAG documents:", exc_info=True)
        return None
    finally:
        elastic_connection.close_connection()

def query_metadata_source_documents(search_string: str):
    elastic_connection = ElasticsearchIntegration()
    try:
        response = elastic_connection.query_rag_database_document({
            "query": {
                "match": {
                    "metadata.source": search_string
                }
            },
            "size": 1000
        })

        logger.debug(f"Number of hits for '{search_string}': {len(response)}")  # Log number of hits

        response_text = [x['_source']['text'] for x in response if '_source' in x and 'text' in x['_source']]  # Safe extraction

        if response_text:
            llm_handler = LLMHandler()
            summary = llm_handler.run_query(query=f"Summarize the following documents: {response_text}", model="llama3")  
            return summary 
        else:
            logger.warning(f"No text content found for '{search_string}'")
            return None

    except Exception as e:
        logger.exception(f"Exception occurred while querying metadata source documents for '{search_string}':", exc_info=True)
        return None
    finally:
        elastic_connection.close_connection()

