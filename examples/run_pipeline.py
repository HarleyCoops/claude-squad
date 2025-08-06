#!/usr/bin/env python
"""
Example script to run the social media posting pipeline.
"""
import os
import sys
import time
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from social_media_pipeline.core.pipeline import Pipeline
from social_media_pipeline.utils.logging_utils import setup_logging
from social_media_pipeline.config import settings

# Configure logging
logger = setup_logging(log_level="INFO")

def main():
    """Run the pipeline."""
    logger.info("Starting social media pipeline example")
    
    # Override settings for the example
    settings.WATCH_DIRECTORY = "./examples/content_inbox"
    settings.PROCESSED_DIRECTORY = "./examples/content_processed"
    settings.FAILED_DIRECTORY = "./examples/content_failed"
    settings.TEMP_DIRECTORY = "./examples/temp"
    
    # Create required directories
    for directory in [settings.WATCH_DIRECTORY, settings.PROCESSED_DIRECTORY, 
                     settings.FAILED_DIRECTORY, settings.TEMP_DIRECTORY]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create the pipeline
    pipeline = Pipeline()
    
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

