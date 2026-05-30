"""
Main pipeline orchestrator for the social media posting pipeline.
"""
import logging
import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models.content import ContentPackage
from ..models.post import Post
from .monitor import ContentMonitor, start_monitoring
from .processor import ContentProcessor
from .composer import PostComposer
from .publisher import Publisher
from .scheduler import Scheduler
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class Pipeline:
    """
    Main pipeline orchestrator.
    """
    def __init__(self):
        """Initialize the pipeline."""
        # Create components
        self.processor = ContentProcessor()
        self.composer = PostComposer()
        self.publisher = Publisher()
        self.scheduler = Scheduler(self._publish_scheduled_post)
        
        # Initialize state
        self.running = False
        self.monitor = None
    
    def start(self) -> None:
        """Start the pipeline."""
        logger.info("Starting social media pipeline")
        
        # Initialize platforms
        self.publisher.initialize_platforms()
        
        # Start the scheduler
        self.scheduler.start()
        
        # Start monitoring the directory
        self.monitor = start_monitoring(self._process_content_package)
        
        # Mark as running
        self.running = True
        
        logger.info("Social media pipeline started")
    
    def stop(self) -> None:
        """Stop the pipeline."""
        logger.info("Stopping social media pipeline")
        
        # Stop monitoring
        if self.monitor:
            self.monitor.stop()
        
        # Stop the scheduler
        self.scheduler.stop()
        
        # Mark as stopped
        self.running = False
        
        logger.info("Social media pipeline stopped")
    
    def _process_content_package(self, content_package: ContentPackage) -> None:
        """
        Process a content package.
        
        Args:
            content_package: The content package to process
        """
        try:
            logger.info(f"Processing content package: {content_package.id}")
            
            # Process the content package
            post = self.processor.process(content_package)
            
            if not post:
                logger.error(f"Failed to process content package: {content_package.id}")
                return
            
            # Compose platform-specific posts
            post = self.composer.compose(post)
            
            # Check if the post should be scheduled
            has_scheduled_time = False
            for platform_post in post.platform_posts.values():
                if platform_post.scheduled_time:
                    has_scheduled_time = True
                    break
            
            # Schedule or publish the post
            if has_scheduled_time:
                result = self.publisher.schedule_post(post)
                logger.info(f"Scheduled post {post.id}: {result}")
            elif settings.PROCESS_IMMEDIATELY:
                # Run in a separate thread to avoid blocking
                threading.Thread(
                    target=self._publish_post,
                    args=(post,),
                    daemon=True
                ).start()
            
            logger.info(f"Successfully processed content package: {content_package.id}")
        
        except Exception as e:
            logger.error(f"Error in pipeline processing content package {content_package.id}: {str(e)}")
    
    def _publish_post(self, post: Post) -> Dict[str, Any]:
        """
        Publish a post.
        
        Args:
            post: The post to publish
            
        Returns:
            Dict[str, Any]: Publishing results
        """
        try:
            logger.info(f"Publishing post: {post.id}")
            result = self.publisher.publish_post(post)
            logger.info(f"Published post {post.id}: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error publishing post {post.id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _publish_scheduled_post(self, post_id: str) -> Dict[str, Any]:
        """
        Publish a scheduled post.
        
        Args:
            post_id: ID of the post to publish
            
        Returns:
            Dict[str, Any]: Publishing results
        """
        try:
            logger.info(f"Publishing scheduled post: {post_id}")
            
            # Load the post
            post_path = Path(settings.PROCESSED_DIRECTORY) / f"{post_id}.json"
            post = Post.load_from_file(post_path)
            
            # Publish the post
            result = self.publisher.publish_post(post)
            
            logger.info(f"Published scheduled post {post_id}: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error publishing scheduled post {post_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_scheduled_posts(self) -> Dict[str, Any]:
        """
        Process all due scheduled posts.
        
        Returns:
            Dict[str, Any]: Processing results
        """
        return self.publisher.process_scheduled_posts()
    
    def retry_failed_posts(self) -> Dict[str, Any]:
        """
        Retry all failed posts that can be retried.
        
        Returns:
            Dict[str, Any]: Retry results
        """
        return self.publisher.retry_failed_posts()

