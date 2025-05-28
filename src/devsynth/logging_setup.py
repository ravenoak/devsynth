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

    This function respects test isolation by checking for the DEVSYNTH_NO_FILE_LOGGING
    and DEVSYNTH_PROJECT_DIR environment variables. In test environments, it will
    avoid creating directories in the real filesystem.

    Args:
        log_dir: Optional log directory path, defaults to the configured or environment-specified path

    Returns:
        str: The path to the log directory
    """
    # Check if file logging is disabled via environment variable
    no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")
    if no_file_logging:
        # Return the path without creating the directory
        return log_dir if log_dir is not None else get_log_dir()

    # Check if we're in a test environment
    in_test_env = os.environ.get("DEVSYNTH_PROJECT_DIR") is not None

    dir_path = log_dir if log_dir is not None else get_log_dir()

    # If we're in a test environment with DEVSYNTH_PROJECT_DIR set, ensure paths are within the test directory
    if in_test_env:
        test_project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
        path_obj = Path(dir_path)

        # If the path is absolute and not within the test project directory,
        # redirect it to be within the test project directory
        if path_obj.is_absolute() and not str(path_obj).startswith(test_project_dir):
            # For paths starting with home directory
            if str(path_obj).startswith(str(Path.home())):
                relative_path = str(path_obj).replace(str(Path.home()), "")
                new_path = os.path.join(test_project_dir, relative_path.lstrip("/\\"))
                print(f"Redirecting log path {dir_path} to test path {new_path}")
                dir_path = new_path
            # For other absolute paths
            else:
                # Extract the path components after the root
                relative_path = str(path_obj.relative_to(path_obj.anchor))
                new_path = os.path.join(test_project_dir, relative_path)
                print(f"Redirecting absolute log path {dir_path} to test path {new_path}")
                dir_path = new_path

    # Only create directories if not in a test environment with file operations disabled
    if not no_file_logging:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Log the error but don't fail
            print(f"Warning: Failed to create log directory {dir_path}: {e}")

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

    # Check if file logging is disabled via environment variable
    no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in ("1", "true", "yes")
    if no_file_logging:
        create_dir = False

    # Set configured paths
    if log_dir is not None:
        _configured_log_dir = log_dir

    if log_file is not None:
        _configured_log_file = log_file
    else:
        _configured_log_file = get_log_file()

    # Create directory if requested and file logging is not disabled
    if create_dir and not no_file_logging:
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

    # Add file handler if create_dir is True and file logging is not disabled
    if create_dir and not no_file_logging:
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
    if create_dir and not no_file_logging:
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
        self.logger.debug(msg, extra=kwargs if kwargs else None)

    def info(self, msg: str, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(msg, extra=kwargs if kwargs else None)

    def warning(self, msg: str, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(msg, extra=kwargs if kwargs else None)

    def error(self, msg: str, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(msg, extra=kwargs if kwargs else None)

    def critical(self, msg: str, **kwargs) -> None:
        """Log a critical message."""
        self.logger.critical(msg, extra=kwargs if kwargs else None)

    def exception(self, msg: str, **kwargs) -> None:
        """Log an exception message with traceback."""
        self.logger.exception(msg, extra=kwargs if kwargs else None)

# Don't configure logging on import - this is now explicit
# Instead, code must call configure_logging() when needed

def get_logger(name: str) -> DevSynthLogger:
    """
    Get a DevSynthLogger instance for the specified component.

    Args:
        name: The name of the component (typically __name__)

    Returns:
        DevSynthLogger: A logger instance for the component
    """
    return DevSynthLogger(name)
