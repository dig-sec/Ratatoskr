import logging
import yaml

def load_config(self, config_file):
    try:
        with open(config_file, 'r') as stream:
            return yaml.safe_load(stream)
    except (FileNotFoundError, yaml.YAMLError) as exc:
        logging.error(f"Error loading config: {exc}")
        return None