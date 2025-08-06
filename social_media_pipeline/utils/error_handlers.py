"""
Error handling utilities for the social media pipeline.
"""
import logging
import time
import functools
import traceback
from typing import Callable, Any, Dict, Optional, Type, List, Union

# Configure logger
logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, 
         backoff_factor: float = 2.0, exceptions: List[Type[Exception]] = None):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay for each retry
        exceptions: List of exceptions to catch and retry
        
    Returns:
        Callable: Decorated function
    """
    if exceptions is None:
        exceptions = [Exception]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {current_delay:.2f} seconds...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise Exception(f"Failed after {max_attempts} attempts")
        
        return wrapper
    
    return decorator


def handle_exceptions(default_return: Any = None, 
                     log_level: str = 'error', 
                     reraise: bool = False):
    """
    Exception handling decorator.
    
    Args:
        default_return: Default value to return on exception
        log_level: Log level for exceptions
        reraise: Whether to reraise the exception after handling
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get the log method based on log_level
                log_method = getattr(logger, log_level.lower(), logger.error)
                
                # Log the exception
                log_method(f"Exception in {func.__name__}: {str(e)}")
                log_method(f"Traceback: {traceback.format_exc()}")
                
                # Reraise if requested
                if reraise:
                    raise
                
                # Otherwise return the default value
                return default_return
        
        return wrapper
    
    return decorator


class ErrorTracker:
    """
    Tracks errors and provides retry functionality.
    """
    def __init__(self, max_errors: int = 10, error_window: float = 3600.0):
        """
        Initialize the error tracker.
        
        Args:
            max_errors: Maximum number of errors allowed in the window
            error_window: Time window for tracking errors in seconds
        """
        self.max_errors = max_errors
        self.error_window = error_window
        self.errors = []
    
    def add_error(self, error: Union[Exception, str], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an error to the tracker.
        
        Args:
            error: The error to add
            context: Additional context for the error
            
        Returns:
            bool: True if the error was added, False if the error limit was reached
        """
        # Remove old errors
        self._clean_old_errors()
        
        # Check if we've reached the error limit
        if len(self.errors) >= self.max_errors:
            logger.error(f"Error limit reached: {len(self.errors)} errors in the last {self.error_window} seconds")
            return False
        
        # Add the error
        self.errors.append({
            'error': str(error),
            'timestamp': time.time(),
            'context': context or {}
        })
        
        return True
    
    def should_retry(self, error: Union[Exception, str], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if an operation should be retried.
        
        Args:
            error: The error that occurred
            context: Additional context for the error
            
        Returns:
            bool: True if the operation should be retried, False otherwise
        """
        # Add the error to the tracker
        return self.add_error(error, context)
    
    def get_error_count(self) -> int:
        """
        Get the number of errors in the current window.
        
        Returns:
            int: Number of errors
        """
        # Remove old errors
        self._clean_old_errors()
        
        return len(self.errors)
    
    def reset(self) -> None:
        """Reset the error tracker."""
        self.errors = []
    
    def _clean_old_errors(self) -> None:
        """Remove errors outside the time window."""
        current_time = time.time()
        self.errors = [e for e in self.errors 
                      if current_time - e['timestamp'] <= self.error_window]


def safe_execute(func: Callable, *args, default_return: Any = None, **kwargs) -> Any:
    """
    Safely execute a function and handle exceptions.
    
    Args:
        func: The function to execute
        *args: Arguments for the function
        default_return: Default value to return on exception
        **kwargs: Keyword arguments for the function
        
    Returns:
        Any: The function result or default_return on exception
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return default_return

