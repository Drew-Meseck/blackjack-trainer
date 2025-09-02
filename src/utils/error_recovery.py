"""
Error recovery utilities for the blackjack simulator.

This module provides utilities for graceful error recovery and user feedback.
"""

import logging
import traceback
from typing import Any, Callable, Optional, Type, Union
from .exceptions import BlackjackSimulatorError


# Configure logging for error recovery
logger = logging.getLogger(__name__)


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    error_message: str = None,
    log_error: bool = True,
    reraise_as: Optional[Type[Exception]] = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return if function fails
        error_message: Custom error message for logging
        log_error: Whether to log the error
        reraise_as: Exception type to reraise as
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if function fails
        
    Raises:
        Exception: If reraise_as is specified and function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            error_msg = error_message or f"Error executing {func.__name__}"
            logger.error(f"{error_msg}: {e}")
            logger.debug(traceback.format_exc())
        
        if reraise_as:
            if isinstance(e, BlackjackSimulatorError):
                raise
            else:
                raise reraise_as(f"{error_message or 'Operation failed'}: {e}") from e
        
        return default_return


def retry_operation(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 0.1,
    backoff_factor: float = 2.0,
    error_message: str = None,
    *args,
    **kwargs
) -> Any:
    """
    Retry an operation with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff_factor: Factor to multiply delay by after each attempt
        error_message: Custom error message for final failure
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result
        
    Raises:
        Exception: Last exception if all attempts fail
    """
    import time
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:  # Not the last attempt
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                time.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"All {max_attempts} attempts failed. Final error: {e}")
    
    # If we get here, all attempts failed
    final_message = error_message or f"Operation failed after {max_attempts} attempts"
    if isinstance(last_exception, BlackjackSimulatorError):
        raise last_exception
    else:
        raise BlackjackSimulatorError(final_message, str(last_exception)) from last_exception


def handle_user_input_error(error: Exception, prompt: str = None) -> str:
    """
    Handle user input errors with helpful feedback.
    
    Args:
        error: The exception that occurred
        prompt: Optional prompt to show after error message
        
    Returns:
        Formatted error message for display to user
    """
    if isinstance(error, BlackjackSimulatorError):
        message = str(error)
    else:
        message = f"Invalid input: {error}"
    
    if prompt:
        return f"❌ {message}\n{prompt}"
    else:
        return f"❌ {message}"


def format_error_for_user(error: Exception, context: str = None) -> str:
    """
    Format an error message for user-friendly display.
    
    Args:
        error: The exception to format
        context: Optional context about when the error occurred
        
    Returns:
        Formatted error message
    """
    if isinstance(error, BlackjackSimulatorError):
        base_message = str(error)
    else:
        base_message = f"An unexpected error occurred: {error}"
    
    if context:
        return f"❌ Error {context}: {base_message}"
    else:
        return f"❌ {base_message}"


def log_error_with_context(
    error: Exception, 
    context: str, 
    user_action: str = None,
    additional_info: dict = None
) -> None:
    """
    Log an error with contextual information.
    
    Args:
        error: The exception that occurred
        context: Context where the error occurred
        user_action: What the user was trying to do
        additional_info: Additional information to log
    """
    log_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
    }
    
    if user_action:
        log_data['user_action'] = user_action
    
    if additional_info:
        log_data.update(additional_info)
    
    logger.error(f"Error in {context}: {error}", extra=log_data)
    logger.debug(traceback.format_exc())


class ErrorRecoveryContext:
    """Context manager for error recovery operations."""
    
    def __init__(
        self, 
        operation_name: str,
        user_message: str = None,
        log_errors: bool = True,
        reraise: bool = True
    ):
        self.operation_name = operation_name
        self.user_message = user_message or f"performing {operation_name}"
        self.log_errors = log_errors
        self.reraise = reraise
        self.error = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            
            if self.log_errors:
                log_error_with_context(
                    exc_val, 
                    self.operation_name,
                    additional_info={'reraise': self.reraise}
                )
            
            if not self.reraise:
                return True  # Suppress the exception
        
        return False  # Let exception propagate
    
    def get_user_message(self) -> str:
        """Get formatted error message for user display."""
        if self.error:
            return format_error_for_user(self.error, self.user_message)
        return ""


def validate_and_recover(
    validation_func: Callable,
    value: Any,
    recovery_value: Any = None,
    error_message: str = None
) -> Any:
    """
    Validate a value and provide recovery if validation fails.
    
    Args:
        validation_func: Function to validate the value
        value: Value to validate
        recovery_value: Value to use if validation fails
        error_message: Custom error message
        
    Returns:
        Validated value or recovery value
        
    Raises:
        ValidationError: If validation fails and no recovery value provided
    """
    try:
        return validation_func(value)
    except Exception as e:
        if recovery_value is not None:
            logger.warning(f"Validation failed, using recovery value: {e}")
            return recovery_value
        else:
            if error_message:
                raise BlackjackSimulatorError(error_message, str(e)) from e
            else:
                raise