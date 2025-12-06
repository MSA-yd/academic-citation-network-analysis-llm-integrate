#!/usr/bin/env python3
"""
Logging utility
Provides centralized logging configuration
"""

import logging
from pathlib import Path
from typing import Optional
from config import Config


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers
    
    Parameters:
    -----------
    name : str
        Logger name (typically __name__)
    log_file : Optional[Path]
        Optional log file path
    level : int
        Logging level (default: INFO)
        
    Returns:
    --------
    logging.Logger
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        Config.LOG_DIR.mkdir(exist_ok=True)
        file_path = Config.LOG_DIR / log_file if not log_file.is_absolute() else log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

