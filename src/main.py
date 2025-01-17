import os
#import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
import urllib.parse
from flask import Flask, request, render_template, send_from_directory, jsonify, abort
from werkzeug.utils import secure_filename
import logging

# Local modules
from query_handler import process_query, query_current_status, query_rag_documents, query_metadata_source_documents, process_query_safe
from rag_processor import RagProcessor
from elasticsearch_integration import ElasticsearchIntegration

from logging_config import logger
from config_utils import load_config

class Ratatoskr:
    def __init__(self, host='127.0.0.1', port=6666, debug=False):
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = '/upload'
        logging.basicConfig(filename="ratatoskr.log", level=logging.INFO)
        self.config = load_config()
        self.host = host
        self.port = port
        self.debug = debug

        # Add the executor for background tasks
        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust max_workers as needed

        # Core
        self.app.route('/', methods=['GET'])(self.index)
        self.app.route('/favicon.ico', methods=['GET'])(self.favicon)
        
        # Query
        self.app.route('/api/dialog', methods=['POST'])(self.dialog)
        self.app.route('/api/query_status', methods=['GET'])(self.query_status)
        self.app.route('/api/vector_search', methods=['POST'])(self.vector_search)
        self.app.route('/api/string_search', methods=['POST'])(self.string_search)
        self.app.route('/api/metadata_summary', methods=['POST'])(self.metadata_summary)
        
        # Ingest
        # self.app.route('/api/store_vector', methods=['POST'])(self.store_vector)
        # self.app.route('/store_document', methods=['POST'])(store_document(config=self.config))
        self.app.route('/api/submit_link', methods=['POST'])(self.submit_link)
        # self.app.route('/api/upload_file', methods=['POST'])(self.upload_file)

    def run(self):
        try:
            self.app.run(port=self.port, host=self.host, debug=self.debug)
        finally:
            self.executor.shutdown(wait=True)

    def favicon(self):
        self.app = Flask(__name__, static_url_path='/static')
        return self.app.send_static_file('favicon.ico')
    
    def dialog(self):
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Request body must be JSON'}), 400

            query = data.get('query')
            model = data.get('model')
            if not query or not model:
                return jsonify({'error': '"query" and "model" are required fields'}), 400

            user = data.get('user', 'anonymous')
            session = data.get('session', 'default_session')
            query_id = data.get('query_id', str(uuid.uuid4()))
            use_rag_database = data.get('use_rag_database', False)

            logger.info(f"Processing query: {query_id}")

            # Submit to the executor for background processing
            #self.executor.submit(process_query, query_id, query, model, user, session, use_rag_database)
            self.executor.submit(process_query_safe, query_id, query, model, user, session, use_rag_database)

            return jsonify(query_id=query_id), 200
        except Exception as e:
            logger.exception(f"Error in dialog endpoint: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def submit_link(self):
        """Processes a URL for RAG (Retrieval Augmented Generation)."""
        try:
            url = request.json.get('link')
            if not url:
                return jsonify({'error': 'Missing or invalid URL'}), 400

            # URL Validation (Improved)
            parsed_url = urllib.parse.urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return jsonify({'error': 'Invalid URL format'}), 400
            
            try:
                rag_processor = RagProcessor()
                rag_processor.process_url(url)
            except Exception as rag_error:
                logger.exception("Error within RagProcessor:", exc_info=True)
                return jsonify({'error': f'An error occurred while processing the URL: {str(rag_error)}'}), 500

            return jsonify({'message': 'URL processed successfully'}), 200
        except Exception as e:
            logger.exception("Unexpected error while processing RAG URL:", exc_info=True)
            return jsonify({'error': 'An internal server error occurred'}), 500


    def upload_file(self):  
        """Handles file uploads, including validation and saving."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part in the request'}), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            if file:
                # File Type Validation (Added)
                ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  
                if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                    return jsonify({'error': 'File type not allowed'}), 400

                filename = secure_filename(file.filename)
                filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)

                # Ensure upload directory exists (Added)
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)

                file.save(filepath)

                return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200
        except Exception as e:
            logger.exception(f"Error in upload_file: {e}") 
            return jsonify({'error': 'Internal server error'}), 500

    def store_document_in_elastic(self):
        """Stores a document in Elasticsearch."""
        try:
            document_data = request.json.get('document')
            if not document_data:
                abort(400, description="Missing document in request")

            index_name = request.json.get('index', self.config.get('ratatoskr', {}).get('index'))
            if not index_name:
                abort(400, description="Missing index name in request or config")

            elastic_connection = ElasticsearchIntegration(self.config)
            result = elastic_connection.store_text(index_name, document_data)

            return jsonify({'result': result, 'message': 'Document stored successfully'}), 201
        except Exception as e:
            logger.exception(f"Error storing document: {e}")
            return jsonify({'error': 'Failed to store document'}), 500

    def query_vector_in_elastic(self):
        """Queries Elasticsearch using a vector and returns similar documents."""
        try:
            query = request.json.get('query')
            if not query:
                abort(400, description="Missing query in request")
            k = request.json.get('k', 10) 

            index_name = request.json.get('index', self.config.get('rag_database', {}).get('index'))
            if not index_name:
                abort(400, description="Missing index name in request or config")

            elastic_connection = ElasticsearchIntegration(self.config)
            results = elastic_connection.query_vector(query, k=k, index_name=index_name)
            formatted_results = [
                {
                    'score': hit['_score'],
                    'document': hit['_source']['document'],
                } 
                for hit in results
            ]
            return jsonify({'results': formatted_results}), 200
        except Exception as e:
            logger.exception(f"Error querying vector: {e}")
            return jsonify({'error': 'Failed to query vector'}), 500

    def query_status(self):
        query_id = request.args.get('query_id')
        status = query_current_status(query_id)
        if status is None:
            abort(404, description="Query ID not found")
        else:
            return status
        
    def vector_search(self):
        if 'query' not in request.json:
            abort(400, description="Missing query in request")

        query = request.json['query']
        retrieved_documents = query_rag_documents(query=query)
        retrieved_documents_list = [doc.__dict__ for doc in retrieved_documents]

        # Extract the page_content and metadata.source to new JSON dictionary for each document
        retrieved_documents_list = [{"page_content": doc["page_content"], "metadata_source": doc["metadata"]["source"]} for doc in retrieved_documents_list]

        # If metadata.source is a file path, extract the file name
        for doc in retrieved_documents_list:
            if doc["metadata_source"].startswith("/mnt/"):
                doc["metadata_source"] = os.path.basename(doc["metadata_source"])

        return jsonify(retrieved_documents_list), 200

    def string_search(self):
            try:
                query_text = request.json.get('query')
                if not query_text:
                    abort(400, description="Missing 'query' in request")
                max_results = request.json.get('max_results')

                # Convert query_text and max_results to query dict for elasticsearch
                elastic_query = {
                    "size": max_results,
                    "query": {
                        "query_string": {  # Use query_string for flexible text search
                            "query": query_text, 
                            "default_field": "text"  # Search across all fields by default
                        }
                    }
                }
                elastic_connection = ElasticsearchIntegration()
                results = elastic_connection.raw_text_search(query=elastic_query)

                # Create a new JSON dictionary with the text and source fields from each result
                parsed_results = []
                for result in results:
                    try:
                        source_path = result["_source"]["metadata"]["source"]
                        filename = os.path.basename(source_path)
                        parsed_results.append({
                            "source": filename,
                            "text": result["_source"]["text"],
                        })
                    except KeyError:
                        logger.warning(f"Missing 'source' or 'text' field in result: {result}")
                    
                return parsed_results, 200

            except Exception as e:
                logger.error(f"Error in query_text: {e}")
                return jsonify({"error": "Internal server error"}), 500
            finally:
                elastic_connection.close_connection()
    
    def metadata_summary(self):
        if 'sources' not in request.json:
            abort(400, description="Missing metadata_source in request")

        metadata_sources = request.json['sources'].split(",")
        summaries = []

        for metadata_source in metadata_sources:
            documents = query_metadata_source_documents(search_string=metadata_source)
            if documents:
                summary = {"source": metadata_source, "document_summary": documents}
                summaries.append(summary)

        return jsonify(summaries)

    def index(self):
        return render_template('index.html', model_options=self.config['ollama']['models'])

    # def store_vector(self):
    #     try:
    #         if 'document' not in request.json:
    #             abort(400, description="Missing document in request")

    #         document = request.json['document']

    #         elastic_connection = ElasticsearchIntegration(self.config)
    #         result = elastic_connection.extract_and_store_documents_and_vectors(document)
            
    #         return jsonify({'result': result, 'message': 'Vector stored successfully'}), 201
    #     except Exception as e:
    #         logger.exception(f"Error storing vector: {e}")
    #         return jsonify({'error': 'Failed to store vector'}), 500
    #     finally:
    #         elastic_connection.close_connection()


if __name__ == '__main__':       
    ratatoskr_instance = Ratatoskr(host='0.0.0.0', port=6666, debug=False)
    ratatoskr_instance.run()