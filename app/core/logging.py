import logging
import sys

# Configure a central structured logger for Portalitics
logger = logging.getLogger("portalitics")
logger.setLevel(logging.INFO)

# Avoid adding duplicate handlers if the logger is already initialized
if not logger.handlers:
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
