import logging
import os
import threading
import uuid
import urllib.parse

from flask import Flask, request, render_template, send_from_directory, jsonify, abort
from werkzeug.utils import secure_filename

import yaml
from query_handler import process_query, query_current_status, query_rag_documents, query_metadata_source_documents
from elasticsearch_integration import ElasticsearchIntegration
from rag_processor import RagProcessor

# Centralized Logging Configuration (Improved)
logging.basicConfig(level=logging.INFO, filemode='a', filename='ratatoskr.log', format='%(asctime)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d')
logger = logging.getLogger(__name__)

class Ratatoskr:
    def __init__(self, config_file, host='127.0.0.1', port=6666, debug=False):
        self.app = Flask(__name__)
        self.app.config['UPLOAD_FOLDER'] = '/upload'
        logging.basicConfig(filename="ratatoskr.log", level=logging.INFO)
        self.config = self.load_config(config_file)
        self.host = host
        self.port = port
        self.debug = debug

        # Core
        self.app.route('/', methods=['GET'])(self.index)
        self.app.route('/favicon.ico', methods=['GET'])(self.favicon)
        
        # Query
        self.app.route('/api/query', methods=['POST'])(self.interactive_query)
        self.app.route('/api/query_status', methods=['GET'])(self.query_status)
        self.app.route('/api/query_rag', methods=['POST'])(self.query_rag)
        # self.app.route('/query_text', methods=['POST'])(query_text(config=self.config))
        self.app.route('/api/metadata_summary', methods=['POST'])(self.metadata_summary)

        # Ingest
        # self.app.route('/store_vector', methods=['POST'])(store_vector_and_document(config=self.config))
        # self.app.route('/store_document', methods=['POST'])(store_document(config=self.config))
        # self.app.route('/api/process_url', methods=['POST'])(self.process_rag_url)
        # self.app.route('/api/upload_file', methods=['POST'])(self.upload_file)

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as stream:
                return yaml.safe_load(stream)
        except (FileNotFoundError, yaml.YAMLError) as exc:
            logging.error(f"Error loading config: {exc}")
            return None

    def run(self):
        self.app.run(port=self.port, host=self.host, debug=self.debug)

    def favicon(self):
        return send_from_directory(os.path.join(self.app.root_path, 'static'),
        'favicon.ico',mimetype='image/vnd.microsoft.icon')
    
    def interactive_query(self):
        if 'query' not in request.json:
            abort(400, description="Missing query in request")
        if 'model' not in request.json:
            abort(400, description="Missing model in request")

        # Load variables from request
        query = request.json['query']
        user = request.json['user']
        session = request.json['session']
        model = request.json['model']

        if 'query_id' not in request.json:
            query_id = uuid.uuid4()
        else:
            query_id = request.json['query_id']

        if 'use_rag_database' not in request.json:
            use_rag_database = False
        else:
            use_rag_database = request.json['use_rag_database']

        #process_query(query_id=query_id, query=query, model=model, user=user, session=session, use_rag_database=use_rag_database)
        thread = threading.Thread(target=process_query, args=(query_id, query, model, user, session, use_rag_database))
        thread.start()

        # Return the query_id
        return jsonify(query_id=query_id)

    def process_rag_url(self):
        """Processes a URL for RAG (Retrieval Augmented Generation)."""
        try:
            url = request.json.get('url')
            if not url:
                return jsonify({'error': 'Missing or invalid URL'}), 400

            if not urllib.parse.urlparse(url).scheme or not urllib.parse.urlparse(url).netloc:
                return jsonify({'error': 'Invalid URL format'}), 400

            rag_processor = RagProcessor(self.config)

            try:
                rag_processor.process_url(url)
            except Exception as rag_error:
                logger.exception("Error within RagProcessor:", exc_info=True)  # Using logger here
                return jsonify({'error': f'An error occurred while processing the URL: {str(rag_error)}'}), 500

            return jsonify({'message': 'URL processed successfully'}), 200
        except Exception as e:
            logger.exception("Unexpected error while processing RAG URL:", exc_info=True)  # Using logger
            return jsonify({'error': 'An internal server error occurred'}), 500

    def upload_file(self):  # Made it a method within the Ratatoskr class
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part in the request'}), 400

            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400

            if file:
                # File Type Validation (Added)
                ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # Customize allowed types
                if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXTENSIONS:
                    return jsonify({'error': 'File type not allowed'}), 400

                filename = secure_filename(file.filename)
                filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)

                # Ensure upload directory exists (Added)
                os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)

                file.save(filepath)

                # Additional Processing (Optional)
                # Here you can trigger further processing of the uploaded file if needed.
                # For example, you could pass 'filename' to a function that extracts text, indexes it, etc.

                return jsonify({'message': 'File uploaded successfully', 'filename': filename}), 200
        except Exception as e:
            logging.exception(f"Error in upload_file: {e}") 
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
            k = request.json.get('k', 10) # Get k from request, or default to 10

            index_name = request.json.get('index', self.config.get('rag_database', {}).get('index'))
            if not index_name:
                abort(400, description="Missing index name in request or config")

            elastic_connection = ElasticsearchIntegration(self.config)
            results = elastic_connection.query_vector(query, k=k, index_name=index_name)  # Allow specifying index
            formatted_results = [
                {
                    'score': hit['_score'],
                    'document': hit['_source']['document'],  # Customize the returned fields if needed
                    # Add more fields from the hit if needed
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
        
    def query_rag(self):
        if 'query' not in request.json:
            abort(400, description="Missing query in request")

        # Load variables from request
        query = request.json['query']

        # Run the query
        retrieved_documents = query_rag_documents(query=query)

        # Turn the retrieved documents into a list of JSON dictionaries
        retrieved_documents_list = [doc.__dict__ for doc in retrieved_documents]

        # Extract the page_content and metadata.source to new JSON dictionary for each document
        retrieved_documents_list = [{"page_content": doc["page_content"], "metadata_source": doc["metadata"]["source"]} for doc in retrieved_documents_list]

        # If metadata.source is a file path, extract the file name
        for doc in retrieved_documents_list:
            if doc["metadata_source"].startswith("/mnt/"):
                doc["metadata_source"] = os.path.basename(doc["metadata_source"])

        # Return the retrieved documents
        return jsonify(retrieved_documents_list)

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
        return render_template('index.html')

if __name__ == '__main__':
    config_file = "config.yaml"
    config = Ratatoskr.load_config(None, config_file)

    if config is None:  
        logger.error("Invalid or missing configuration. Exiting.")
        exit(1)
    
    ratatoskr_instance = Ratatoskr(host='0.0.0.0', port=6666, debug=False, config_file=config_file)
    ratatoskr_instance.run()