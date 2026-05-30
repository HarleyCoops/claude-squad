"""
Logging utilities for the social media pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import settings


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for the application.
    
    Args:
        log_file: Path to the log file (if None, uses settings.LOG_FILE)
        log_level: Log level (if None, uses settings.LOG_LEVEL)
        
    Returns:
        logging.Logger: The configured logger
    """
    # Get log file and level from settings if not provided
    if log_file is None:
        log_file = settings.LOG_FILE
    
    if log_level is None:
        log_level = settings.LOG_LEVEL
    
    # Convert log level string to constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler if log file is specified
    if log_file:
        # Create directory for log file if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if enabled
    if settings.CONSOLE_LOG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        name: Name of the module
        
    Returns:
        logging.Logger: The logger
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to log messages.
    """
    def __init__(self, logger, extra=None):
        """
        Initialize the adapter.
        
        Args:
            logger: The logger to adapt
            extra: Extra context to add to log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process the log message.
        
        Args:
            msg: The log message
            kwargs: Keyword arguments for the log method
            
        Returns:
            tuple: The processed message and kwargs
        """
        # Add context to the message
        context_str = ' '.join(f'{k}={v}' for k, v in self.extra.items())
        if context_str:
            msg = f"{msg} [{context_str}]"
        
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with context.
    
    Args:
        name: Name of the module
        **context: Context to add to log messages
        
    Returns:
        LoggerAdapter: The logger adapter
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)

