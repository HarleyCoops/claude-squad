"""
Main entry point for the social media posting pipeline.
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path
import signal
import yaml

from .core.pipeline import Pipeline
from .utils.logging_utils import setup_logging
from .config import settings

# Configure logger
logger = logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Social Media Posting Pipeline')
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--watch-dir',
        type=str,
        help='Directory to watch for new content'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file'
    )
    
    parser.add_argument(
        '--process-scheduled',
        action='store_true',
        help='Process scheduled posts and exit'
    )
    
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Retry failed posts and exit'
    )
    
    return parser.parse_args()


def load_config(config_path):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {str(e)}")
        return {}


def update_settings(config):
    """
    Update settings from configuration.
    
    Args:
        config: Configuration dictionary
    """
    # Update settings from config
    for key, value in config.items():
        if hasattr(settings, key.upper()):
            setattr(settings, key.upper(), value)
            logger.debug(f"Updated setting {key.upper()} = {value}")


def setup_signal_handlers(pipeline):
    """
    Set up signal handlers for graceful shutdown.
    
    Args:
        pipeline: The pipeline instance
    """
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        pipeline.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(
        log_file=args.log_file,
        log_level=args.log_level
    )
    
    logger.info("Starting social media posting pipeline")
    
    # Load configuration if provided
    if args.config:
        config = load_config(args.config)
        update_settings(config)
    
    # Override settings from command line arguments
    if args.watch_dir:
        settings.WATCH_DIRECTORY = args.watch_dir
    
    # Create required directories
    for directory in [settings.WATCH_DIRECTORY, settings.PROCESSED_DIRECTORY, 
                     settings.FAILED_DIRECTORY, settings.TEMP_DIRECTORY]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create the pipeline
    pipeline = Pipeline()
    
    # Set up signal handlers
    setup_signal_handlers(pipeline)
    
    # Process scheduled posts and exit if requested
    if args.process_scheduled:
        logger.info("Processing scheduled posts")
        result = pipeline.process_scheduled_posts()
        logger.info(f"Processed scheduled posts: {result}")
        return
    
    # Retry failed posts and exit if requested
    if args.retry_failed:
        logger.info("Retrying failed posts")
        result = pipeline.retry_failed_posts()
        logger.info(f"Retried failed posts: {result}")
        return
    
    # Start the pipeline
    pipeline.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        pipeline.stop()


if __name__ == '__main__':
    main()

