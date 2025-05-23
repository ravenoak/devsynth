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
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# We'll import DevSynthError later to avoid circular imports

# Configure default logging format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO

# Default log directory - but don't create it yet
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILENAME = "devsynth.log"

# Configured log path - will be set by configure_logging
_configured_log_dir = None
_configured_log_file = None
_logging_configured = False

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

        # Add custom attributes
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data:
                continue
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            ]:
                log_data[key] = value

        return json.dumps(log_data)

def get_log_dir() -> str:
    """
    Get the configured log directory or the default.

    Returns:
        str: The path to the log directory
    """
    if _configured_log_dir is not None:
        return _configured_log_dir
    return os.environ.get("DEVSYNTH_LOG_DIR", DEFAULT_LOG_DIR)

def get_log_file() -> str:
    """
    Get the configured log file path or construct the default.

    Returns:
        str: The path to the log file
    """
    if _configured_log_file is not None:
        return _configured_log_file
    log_dir = get_log_dir()
    return os.path.join(log_dir, os.environ.get("DEVSYNTH_LOG_FILENAME", DEFAULT_LOG_FILENAME))

def ensure_log_dir_exists(log_dir: Optional[str] = None) -> str:
    """
    Ensure the log directory exists, creating it if necessary.

    This function is now separated from configuration to allow deferring directory creation
    until explicitly needed, which helps with test isolation.

    Args:
        log_dir: Optional log directory path, defaults to the configured or environment-specified path

    Returns:
        str: The path to the log directory
    """
    dir_path = log_dir if log_dir is not None else get_log_dir()
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def configure_logging(log_dir: Optional[str] = None, log_file: Optional[str] = None,
                     log_level: int = None, create_dir: bool = True) -> None:
    """
    Configure the logging system with the specified parameters.

    This function must be called explicitly to set up logging. Directory creation
    is now optional and controlled by the create_dir parameter.

    Args:
        log_dir: Directory where log files will be stored
        log_file: Name of the log file
        log_level: Logging level (e.g., logging.INFO)
        create_dir: Whether to create the log directory (default True)
    """
    global _configured_log_dir, _configured_log_file, _logging_configured

    # Set configured paths
    if log_dir is not None:
        _configured_log_dir = log_dir

    if log_file is not None:
        _configured_log_file = log_file
    else:
        _configured_log_file = get_log_file()

    # Create directory if requested
    if create_dir:
        ensure_log_dir_exists(_configured_log_dir)

    # Set up root logger
    root_logger = logging.getLogger()

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Set log level
    if log_level is None:
        log_level = int(os.environ.get("DEVSYNTH_LOG_LEVEL", DEFAULT_LOG_LEVEL))
    root_logger.setLevel(log_level)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # Add file handler if create_dir is True
    if create_dir:
        try:
            file_handler = logging.FileHandler(_configured_log_file)
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)
        except (PermissionError, FileNotFoundError) as e:
            # Log to console only if file logging fails
            console_handler.setFormatter(logging.Formatter(
                "WARNING: File logging failed - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            root_logger.warning(f"Failed to set up file logging: {str(e)}")

    # Mark as configured
    _logging_configured = True

    # Log configuration info
    if create_dir:
        root_logger.info(f"Logging configured. Log file: {_configured_log_file}")
    else:
        root_logger.info("Logging configured for console output only (no file logging).")

class DevSynthLogger:
    """
    Logger wrapper that provides standardized logging for DevSynth components.

    This class no longer creates directories on instantiation, supporting better test isolation.
    Directory creation is now deferred to explicit configure_logging() calls.
    """

    def __init__(self, name: str):
        """
        Initialize a logger for the specified component.

        Args:
            name: The name of the component (typically __name__)
        """
        self.logger = logging.getLogger(name)

        # Don't create log directory here - defer until explicitly configured
        # This is important for test isolation

    def debug(self, msg: str, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(msg, **kwargs)

    def exception(self, msg: str, **kwargs) -> None:
        """Log an exception message with traceback."""
        self.logger.exception(msg, **kwargs)

# Don't configure logging on import - this is now explicit
# Instead, code must call configure_logging() when needed
