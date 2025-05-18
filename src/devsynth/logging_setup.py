
"""
Structured logging setup for the DevSynth system.

This module provides a centralized logging configuration with structured logging
capabilities, ensuring consistent error reporting across the application.
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

# We'll import DevSynthError later to avoid circular imports

# Configure default logging format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO

# Configure log directory
LOG_DIR = os.environ.get("DEVSYNTH_LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure log file
LOG_FILE = os.path.join(LOG_DIR, "devsynth.log")

# Configure JSON formatter
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, 'caller_module', record.module),
            "function": getattr(record, 'caller_function', record.funcName),
            "line": getattr(record, 'caller_line', record.lineno),
            "actual_module": record.module,
            "actual_function": record.funcName,
            "actual_line": record.lineno
        }

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from record
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        if hasattr(record, "error_details"):
            log_data["error_details"] = record.error_details

        # Add any other custom attributes
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno", 
                          "lineno", "module", "msecs", "message", "msg", "name", 
                          "pathname", "process", "processName", "relativeCreated", 
                          "stack_info", "thread", "threadName"]:
                try:
                    # Try to serialize the value to JSON
                    json.dumps({key: value})
                    log_data[key] = value
                except (TypeError, OverflowError):
                    # If the value can't be serialized, convert it to a string
                    log_data[key] = str(value)

        return json.dumps(log_data)


# Configure root logger
def configure_logging(log_level: int = DEFAULT_LOG_LEVEL, 
                     log_to_console: bool = True,
                     log_to_file: bool = True,
                     log_file: str = LOG_FILE,
                     json_format: bool = True) -> None:
    """
    Configure the logging system.

    Args:
        log_level: The logging level (default: INFO)
        log_to_console: Whether to log to the console (default: True)
        log_to_file: Whether to log to a file (default: True)
        log_file: The log file path (default: logs/devsynth.log)
        json_format: Whether to use JSON formatting (default: True)
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if requested
    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# Create a logger class for DevSynth components
class DevSynthLogger:
    """Logger for DevSynth components with structured logging capabilities."""

    def __init__(self, component: str):
        """
        Initialize a logger for a DevSynth component.

        Args:
            component: The name of the component
        """
        self.logger = logging.getLogger(component)

    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
            exc_info: Whether to include exception info (default: False)
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """
        Log a critical message.

        Args:
            message: The message to log
            exc_info: Whether to include exception info (default: True)
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)

    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """
        Log an exception message.

        Args:
            message: The message to log
            exc_info: Whether to include exception info (default: True)
            **kwargs: Additional fields to include in the log entry
        """
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)

    def _log(self, level: int, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Log a message with the given level.

        Args:
            level: The logging level
            message: The message to log
            exc_info: Whether to include exception info
            **kwargs: Additional fields to include in the log entry
        """
        # Capture caller information
        frame = sys._getframe(2)  # Go back 2 frames to get the caller
        caller_module = frame.f_globals.get('__name__', '')
        caller_function = frame.f_code.co_name
        caller_line = frame.f_lineno

        # Create a LogRecord with extra fields
        extra = {
            'caller_module': caller_module,
            'caller_function': caller_function,
            'caller_line': caller_line
        }

        # Handle error details
        if "error" in kwargs:
            error = kwargs.pop("error")
            if hasattr(error, "to_dict"):
                error_dict = error.to_dict()
                extra["error_code"] = error_dict.get("error_code")
                extra["error_details"] = error_dict.get("details")
                extra["error_type"] = error_dict.get("error_type")
            elif isinstance(error, Exception):
                extra["error_type"] = error.__class__.__name__
                extra["error_message"] = str(error)

        # Add remaining kwargs as extra fields
        for key, value in kwargs.items():
            extra[key] = value

        # Log the message with extra fields
        self.logger.log(level, message, exc_info=exc_info, extra=extra)


# Create a default logger instance
logger = DevSynthLogger("devsynth")

# Configure logging on module import
configure_logging()
