#!/usr/bin/env python3
"""
Logger module for consistent debug output
"""
import sys
from datetime import datetime
from pathlib import Path

class Logger:
    """Centralized logging system"""
    
    def __init__(self, log_file=None):
        self.log_file = log_file
        if self.log_file:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _write(self, msg, level="INFO"):
        """Internal write method"""
        # Import here to avoid circular import
        try:
            from config import DEBUG_MODE
        except ImportError:
            DEBUG_MODE = True  # Default to verbose if config not available
        
        # Skip debug messages if DEBUG_MODE is off
        if level == "DEBUG" and not DEBUG_MODE:
            # Still write to log file, just don't print to console
            if self.log_file:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    formatted = f"[{timestamp}] [{level}] {msg}"
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(formatted + '\n')
                except:
                    pass
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {msg}"
        
        # Print to console
        print(formatted)
        sys.stdout.flush()
        
        # Write to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(formatted + '\n')
            except Exception as e:
                print(f"[ERROR] Failed to write to log file: {e}")
    
    def debug(self, msg):
        """Debug level message"""
        self._write(msg, "DEBUG")
    
    def info(self, msg):
        """Info level message"""
        self._write(msg, "INFO")
    
    def success(self, msg):
        """Success level message"""
        self._write(msg, "SUCCESS")
    
    def warning(self, msg):
        """Warning level message"""
        self._write(msg, "WARNING")
    
    def error(self, msg):
        """Error level message"""
        self._write(msg, "ERROR")
    
    def section(self, msg):
        """Print a section header"""
        separator = "=" * 60
        self._write(separator, "INFO")
        self._write(msg, "INFO")
        self._write(separator, "INFO")

# Global logger instance
_logger = None

def get_logger(log_file=None):
    """Get or create the global logger instance"""
    global _logger
    if _logger is None:
        _logger = Logger(log_file)
    return _logger