"""
Error Logger Module

This module provides enhanced error logging functionality for memory operations.
It helps track and analyze errors across memory adapters.
"""

import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


class MemoryErrorLogger:
    """
    Enhanced error logger for memory operations.
    
    This class provides methods for logging and analyzing errors in memory operations.
    It maintains an in-memory log of recent errors and can persist them to disk
    for later analysis.
    """
    
    def __init__(
        self,
        max_errors: int = 100,
        log_dir: Optional[str] = None,
        persist_errors: bool = True,
    ):
        """
        Initialize the memory error logger.
        
        Args:
            max_errors: Maximum number of errors to keep in memory
            log_dir: Directory to store error logs. If None, uses the default log directory.
            persist_errors: Whether to persist errors to disk
        """
        self.max_errors = max_errors
        self.errors: List[Dict[str, Any]] = []
        self.persist_errors = persist_errors
        
        # Set up log directory
        if log_dir is None:
            # Use default log directory
            home_dir = os.path.expanduser("~")
            self.log_dir = os.path.join(home_dir, ".devsynth", "logs", "memory")
        else:
            self.log_dir = log_dir
            
        if self.persist_errors:
            os.makedirs(self.log_dir, exist_ok=True)
            
    def log_error(
        self,
        operation: str,
        adapter_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log an error that occurred during a memory operation.
        
        Args:
            operation: The operation that failed (e.g., "store", "retrieve")
            adapter_name: The name of the adapter that failed
            error: The exception that was raised
            context: Additional context information
            
        Returns:
            The error entry that was logged
        """
        # Create error entry
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "adapter_name": adapter_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }
        
        # Add to in-memory log
        self.errors.append(error_entry)
        
        # Trim if necessary
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
            
        # Log to standard logger
        logger.error(
            f"Memory operation '{operation}' failed on adapter '{adapter_name}': "
            f"{type(error).__name__}: {error}"
        )
        
        # Persist to disk if enabled
        if self.persist_errors:
            self._persist_error(error_entry)
            
        return error_entry
        
    def _persist_error(self, error_entry: Dict[str, Any]) -> None:
        """
        Persist an error entry to disk.
        
        Args:
            error_entry: The error entry to persist
        """
        try:
            # Create filename based on timestamp
            timestamp = datetime.fromisoformat(error_entry["timestamp"])
            filename = f"memory_error_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
            filepath = os.path.join(self.log_dir, filename)
            
            # Write to file
            with open(filepath, "w") as f:
                json.dump(error_entry, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to persist error log: {e}")
            
    def get_recent_errors(
        self,
        operation: Optional[str] = None,
        adapter_name: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent errors, optionally filtered by criteria.
        
        Args:
            operation: Filter by operation
            adapter_name: Filter by adapter name
            error_type: Filter by error type
            limit: Maximum number of errors to return
            
        Returns:
            A list of error entries
        """
        filtered_errors = self.errors
        
        if operation:
            filtered_errors = [e for e in filtered_errors if e["operation"] == operation]
            
        if adapter_name:
            filtered_errors = [e for e in filtered_errors if e["adapter_name"] == adapter_name]
            
        if error_type:
            filtered_errors = [e for e in filtered_errors if e["error_type"] == error_type]
            
        # Return most recent errors first
        return sorted(
            filtered_errors,
            key=lambda e: e["timestamp"],
            reverse=True
        )[:limit]
        
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of errors by type, adapter, and operation.
        
        Returns:
            A dictionary with error statistics
        """
        if not self.errors:
            return {
                "total_errors": 0,
                "by_adapter": {},
                "by_operation": {},
                "by_error_type": {},
            }
            
        # Count errors by different dimensions
        by_adapter = {}
        by_operation = {}
        by_error_type = {}
        
        for error in self.errors:
            # Count by adapter
            adapter = error["adapter_name"]
            by_adapter[adapter] = by_adapter.get(adapter, 0) + 1
            
            # Count by operation
            operation = error["operation"]
            by_operation[operation] = by_operation.get(operation, 0) + 1
            
            # Count by error type
            error_type = error["error_type"]
            by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
            
        return {
            "total_errors": len(self.errors),
            "by_adapter": by_adapter,
            "by_operation": by_operation,
            "by_error_type": by_error_type,
        }
        
    def clear_errors(self) -> None:
        """Clear all in-memory errors."""
        self.errors = []


# Create a global instance
memory_error_logger = MemoryErrorLogger()