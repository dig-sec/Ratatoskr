import yaml
import logging

# Centralized logging configuration
logger = logging.getLogger(__name__)

def load_config(config_file):
    """
    Loads configuration from a YAML file.
    """
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
