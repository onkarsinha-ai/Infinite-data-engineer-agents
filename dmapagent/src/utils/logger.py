"""Logging utility module."""
import logging
import sys
from config import get_settings

settings = get_settings()


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the given name."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(settings.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    return logger
