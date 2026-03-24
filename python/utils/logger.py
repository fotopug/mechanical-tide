"""
Logging setup for Mechanical Tide Clock
Configures structured logging with file rotation
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


def setup_logger(name='tide_clock', config=None):
    """
    Set up application logger with file and console handlers
    
    Args:
        name: Logger name
        config: Configuration dict with logging settings
    
    Returns:
        Logger instance
    """
    # Default configuration
    if config is None:
        config = {
            'level': 'INFO',
            'file': 'logs/tide_clock.log',
            'max_size_mb': 10,
            'backup_count': 5
        }
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    level_str = config.get('level', 'INFO')
    level = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    log_file = Path(config.get('file', 'logs/tide_clock.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    max_bytes = config.get('max_size_mb', 10) * 1024 * 1024
    backup_count = config.get('backup_count', 5)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info(f"Logger initialized: {name} (level={level_str})")
    logger.info(f"Log file: {log_file.absolute()}")
    
    return logger


def get_logger(name='tide_clock'):
    """
    Get existing logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
