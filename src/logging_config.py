import logging
import os

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    filemode='a',
    filename=os.path.join(os.path.dirname(__file__), 'ratatoskr.log'), 
    format='%(asctime)s - %(levelname)s - %(message)s - Source: %(filename)s:%(lineno)d'
)