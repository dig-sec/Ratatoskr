import logging
import os
import datetime

from flask import abort, jsonify, request
from elasticsearch_integration import ElasticsearchIntegration
from llm_handler import LLMHandler

# Logging (Improved)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filemode='a',
    filename='ratatoskr.log',
    format='%(asctime)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d'
)

def process_query(query_id: str, user_query: str, model: str, user: str, session=None, use_rag_database=False):
    elastic_connection = ElasticsearchIntegration()
    try:
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

        # Setup the query to be sent to the LLM
        rag_summary = None
        session_summary = None

        # Get context from the RAG database if use_rag_database is True
        if use_rag_database:
            try:
                rag_results = elastic_connection.query_vector(user_query)
                # Remove rag_results with doc.page_content lower than 100 characters
                rag_results = [x for x in rag_results if len(x.page_content) > 200]

                # Turn the retrieved documents into a list of JSON dictionaries
                retrieved_documents_list = [doc.__dict__ for doc in rag_results]

                # Extract the page_content and metadata.source to new JSON dictionary for each document
                retrieved_documents_list = [{"page_content": doc["page_content"], "metadata_source": doc["metadata"]["source"]} for doc in retrieved_documents_list]

                # If metadata.source is a file path, extract the file name
                for doc in retrieved_documents_list:
                    if doc["metadata_source"].startswith("/mnt/"):
                        doc["metadata_source"] = os.path.basename(doc["metadata_source"])

                # Check if rag_results is empty
                if len(retrieved_documents_list) == 0:
                    rag_results = None
                else:
                    rag_query = f"Create a bullet point summary of the following documents found related to the user query. Page_content is the content found and metadata_source is the source document: {str(retrieved_documents_list)}"
                    llm_handler = LLMHandler()  
                    rag_summary = llm_handler.run_query(query=rag_query, model=model)
            except Exception as e:
                rag_results = None
                logging.exception("Exception occurred while processing query", exc_info=True)

        # Get context based on session value
        if session is not None:
            try:
                session_documents = elastic_connection.query_document({
                    "query": {
                        "match": {
                            "session": session
                        }
                    }
                })
                # Parse query and reponse from session_documents
                session_documents = [x['_source'] for x in session_documents]
                session_documents = [x for x in session_documents if x['query'] != user_query]
                session_documents = [x for x in session_documents if x['response'] != ""]
                # Check if session_documents is empty
                if len(session_documents) == 0:
                    session_documents = None
                else:
                    # Convert session_documents to a string
                    session_documents = str(session_documents)
                    session_query = f"Summarize: {session_documents}"
                    llm_handler = LLMHandler()  
                    session_summary = llm_handler.run_query(query=session_query, model=model)
                    
            except Exception as e:
                session_documents = None
                logging.exception("Exception occurred while processing query", exc_info=True)
        
        # Generate response based on context
        if rag_summary is not None and session_summary is not None:
            combined_query = f"User query: {user_query}. \\n Summarized content from documents found related to the user query: {rag_summary} \\n Context from the current chat session: {session_summary}"
        elif rag_summary is not None:
            combined_query = f"User query: {user_query}. \\n Summarized content from documents found related to the user query: {rag_summary}"
        elif session_summary is not None:
            combined_query = f"User query: {user_query}. \\n Context from the current chat session: {session_summary}"
        elif rag_summary is None and session_summary is None:
            combined_query = user_query

        # Run the query through the LLM
        llm_handler = LLMHandler()  
        response = llm_handler.run_query(query=combined_query, model=model)

        # Update the document in the database with the response and status completed
        update_query = {
        "script": {
            "source": "ctx._source.status = 'completed'; ctx._source.response = params.response",
            "params": {
                "response": response
            }
        },
        "query": {
            "match": {
            "query_id": query_id
            }
        }
        }

        elastic_connection.update_query(update_query)

    except Exception as e:
        logger.exception("Exception occurred while processing query:", exc_info=True)  # Logging improved
    finally:
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
            hit = response[0]  # Assuming there's only one hit in the list
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
            # Fix typo in summary prompt
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