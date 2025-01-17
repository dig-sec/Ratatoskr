import yaml
import logging
import os

# Centralized logging configuration
logger = logging.getLogger(__name__)

def load_config():
    """
    Loads configuration from a YAML file.
    """
    config_file = os.path.join(os.path.dirname(__file__), '../config.yaml')
    if not os.path.exists(config_file):
        config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')

    try:
        with open(config_file, 'r') as stream:
            config = yaml.safe_load(stream)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file '{config_file}' not found.")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file '{config_file}': {e}")
        return None
