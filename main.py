#!/usr/bin/env python3
"""
SproutCV - Sprout Length Measurement Application
Main entry point
"""

import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

from sproutcv.gui.main_window import MainWindow
from sproutcv.config import LoggingConfig


def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    log_dir = Path(LoggingConfig.LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Setup root logger
    root_logger = logging.getLogger('sproutcv')
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LoggingConfig.DEFAULT_LEVEL))
    console_formatter = logging.Formatter(LoggingConfig.CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    log_file = log_dir / LoggingConfig.LOG_FILE
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, LoggingConfig.FILE_LEVEL))
    file_formatter = logging.Formatter(LoggingConfig.FILE_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    root_logger.info("="*50)
    root_logger.info("SproutCV Application Started")
    root_logger.info("="*50)


def main():
    """Initialize and run the application"""
    # Setup logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("SproutCV")
    app.setOrganizationName("SproutCV")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    exit_code = app.exec()
    
    logging.getLogger('sproutcv').info("Application closed")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()