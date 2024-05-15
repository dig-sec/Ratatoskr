from langchain_community.llms import Ollama
import yaml
import logging
import os

log_file = os.path.join(os.path.dirname(__file__), 'ratatoskr.log')
logging.basicConfig(level=logging.INFO, filemode='a', filename=log_file,
                    format='%(asctime)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d')

class LLMHandler:
    def __init__(self, config_file='config.yaml'):
        self.config = self.load_config(config_file)
        self.ollama_session = None
        
    @staticmethod
    def load_config(config_file):
        try:
            with open(config_file, 'r') as stream:
                return yaml.safe_load(stream)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logging.error(f"Error loading config: {e}")
            return None
    
    def init_ollama_session(self, model):
        if self.config is None:
            logging.error("Configuration not loaded. Cannot initialize Ollama session.")
            return None

        base_url = self.config.get('ollama', {}).get('base_url')
        if not base_url:
            logging.error("Missing or invalid 'ollama.base_url' in config.yaml")
            return None
        
        self.ollama_session = Ollama(
            model=model,
            verbose=False,
            base_url=base_url
        )
    
    def run_query(self, query: str, model: str):
        if self.ollama_session is None or self.ollama_session.model != model:
            self.init_ollama_session(model)

        if self.ollama_session is None:
            return None

        try:
            answer = self.ollama_session.invoke(query).strip()
            return answer
        except Exception as e:
            logging.error(f'Error while processing query: {e}', exc_info=True)
            return None
