import logging
from typing import Optional

from langchain_community.llms import Ollama
from ratatoskr.utils.config import load_config


logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, config_file: str = "config.yaml"):
        self.config = load_config(config_file)
        self.ollama_session: Optional[Ollama] = None  # Type hint for clarity

    def init_ollama_session(self, model: str) -> None:
        if self.config is None:
            logger.error("Configuration not loaded. Cannot initialize Ollama session.")
            return

        base_url = self.config.get("ollama", {}).get("base_url")
        if not base_url:
            logger.error("Missing or invalid 'ollama.base_url' in config.yaml")
            return

        # Check if session needs to be re-initialized
        if self.ollama_session is None or self.ollama_session.model != model:  
            self.ollama_session = Ollama(
                model=model, 
                verbose=False,
                base_url=base_url
            )
            logger.info(f"Initialized Ollama session with model: {model}")

    async def run_query(self, query: str, model: str) -> Optional[str]:
        self.init_ollama_session(model)  # Ensure session is initialized

        if self.ollama_session is None:
            return None

        try:
            answer = await self.ollama_session.ainvoke(query)  # Use ainvoke for async
            logger.info(f"LLM response: {answer}")  # Log the response for debugging
            return answer.strip()
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)  # Log the error with traceback
            return None
