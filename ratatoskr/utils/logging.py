import logging
import sys
from logging.handlers import RotatingFileHandler
from ratatoskr.utils.config import config


def setup_logging(config):
    """Configures the logging system based on settings from config.yaml."""

    log_level = config["logging"]["level"].upper()
    log_file = config["logging"]["file"]
    max_bytes = config["logging"]["max_bytes"]
    backup_count = config["logging"]["backup_count"]

    # Create a custom formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d"
    )

    # Create a rotating file handler (optional)
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

    # Create a stream handler for console output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)

    # Get the root logger and add handlers
    logger = logging.getLogger()
    logger.setLevel(log_level)  

    if log_file:
        logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
