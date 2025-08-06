#!/usr/bin/env python
"""
Script to run the social media posting pipeline.
"""
import os
import sys
import time
import logging
import argparse
from pathlib import Path

from social_media_pipeline.core.pipeline import Pipeline
from social_media_pipeline.utils.logging_utils import setup_logging
from social_media_pipeline.config import settings

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Social Media Posting Pipeline')
    
    parser.add_argument(
        '--watch-dir',
        type=str,
        help='Directory to watch for new content'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level'
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

def main():
    """Run the pipeline."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(log_level=args.log_level)
    
    logger.info("Starting social media pipeline")
    
    # Override settings from command line arguments
    if args.watch_dir:
        settings.WATCH_DIRECTORY = args.watch_dir
    
    # Create required directories
    for directory in [settings.WATCH_DIRECTORY, settings.PROCESSED_DIRECTORY, 
                     settings.FAILED_DIRECTORY, settings.TEMP_DIRECTORY]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create the pipeline
    pipeline = Pipeline()
    
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
    
    logger.info(f"Watching directory: {settings.WATCH_DIRECTORY}")
    logger.info("Drop content into the watch directory to process it")
    logger.info("Press Ctrl+C to stop the pipeline")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping pipeline")
        pipeline.stop()
        logger.info("Pipeline stopped")

if __name__ == "__main__":
    main()

