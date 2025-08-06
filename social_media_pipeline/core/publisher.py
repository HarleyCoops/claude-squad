"""
Publisher component for the social media pipeline.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

from ..models.post import Post, PlatformPost
from ..models.schedule import ScheduledPost, Schedule
from ..platforms.platform_base import PlatformBase, PlatformFactory
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class Publisher:
    """
    Publishes posts to social media platforms.
    """
    def __init__(self):
        """Initialize the publisher."""
        self.platforms = {}
        self.schedule = self._load_schedule()
    
    def initialize_platforms(self) -> None:
        """Initialize and authenticate with all enabled platforms."""
        logger.info("Initializing social media platforms")
        
        # Initialize Ayrshare if enabled
        if settings.USE_AYRSHARE:
            ayrshare_config = settings.PLATFORM_CONFIGS.get('ayrshare', {})
            if ayrshare_config:
                ayrshare = PlatformFactory.create_platform('ayrshare', ayrshare_config)
                if ayrshare and ayrshare.authenticate():
                    self.platforms['ayrshare'] = ayrshare
                    logger.info("Initialized Ayrshare platform")
                else:
                    logger.error("Failed to initialize Ayrshare platform")
        
        # Initialize individual platforms if Ayrshare is not enabled
        if not settings.USE_AYRSHARE:
            for platform_name, platform_config in settings.PLATFORM_CONFIGS.items():
                # Skip Ayrshare
                if platform_name == 'ayrshare':
                    continue
                
                # Skip disabled platforms
                if not platform_config.get('enabled', False):
                    continue
                
                # Create and authenticate the platform
                platform = PlatformFactory.create_platform(platform_name, platform_config)
                if platform and platform.authenticate():
                    self.platforms[platform_name] = platform
                    logger.info(f"Initialized {platform_name} platform")
                else:
                    logger.error(f"Failed to initialize {platform_name} platform")
    
    def publish_post(self, post: Post) -> Dict[str, Any]:
        """
        Publish a post to all platforms.
        
        Args:
            post: The post to publish
            
        Returns:
            Dict[str, Any]: Results for each platform
        """
        logger.info(f"Publishing post: {post.id}")
        
        # Check if platforms are initialized
        if not self.platforms:
            self.initialize_platforms()
        
        # Check if we have any platforms
        if not self.platforms:
            logger.error("No platforms initialized")
            return {'success': False, 'error': "No platforms initialized"}
        
        # Results for each platform
        results = {}
        
        # If using Ayrshare, publish to all platforms at once
        if settings.USE_AYRSHARE and 'ayrshare' in self.platforms:
            # Get all platform posts
            platform_posts = list(post.platform_posts.values())
            
            # If no platform posts, return error
            if not platform_posts:
                logger.error(f"No platform posts found for post: {post.id}")
                return {'success': False, 'error': "No platform posts found"}
            
            # Use the first platform post for Ayrshare
            platform_post = platform_posts[0]
            
            # Publish to Ayrshare
            ayrshare_result = self.platforms['ayrshare'].publish_post(platform_post)
            results['ayrshare'] = ayrshare_result
            
            # Update post status based on result
            if ayrshare_result.get('success', False):
                post.status = "published"
            else:
                post.status = "failed"
        
        # Otherwise, publish to each platform individually
        else:
            # Track overall success
            success_count = 0
            
            # Publish to each platform
            for platform_name, platform_post in post.platform_posts.items():
                # Skip if platform is not initialized
                if platform_name not in self.platforms:
                    logger.warning(f"Platform {platform_name} not initialized, skipping")
                    results[platform_name] = {
                        'success': False,
                        'platform': platform_name,
                        'error': "Platform not initialized"
                    }
                    continue
                
                # Publish to the platform
                platform_result = self.platforms[platform_name].publish_post(platform_post)
                results[platform_name] = platform_result
                
                # Track success
                if platform_result.get('success', False):
                    success_count += 1
            
            # Update post status based on results
            if success_count > 0:
                if success_count == len(post.platform_posts):
                    post.status = "published"
                else:
                    post.status = "partial"
            else:
                post.status = "failed"
        
        # Save the updated post
        self._save_post(post)
        
        # Return the results
        return {
            'success': post.status in ["published", "partial"],
            'status': post.status,
            'results': results
        }
    
    def schedule_post(self, post: Post) -> Dict[str, Any]:
        """
        Schedule a post for later publishing.
        
        Args:
            post: The post to schedule
            
        Returns:
            Dict[str, Any]: Scheduling results
        """
        logger.info(f"Scheduling post: {post.id}")
        
        # Check if any platform posts have scheduled times
        scheduled_platforms = []
        for platform_name, platform_post in post.platform_posts.items():
            if platform_post.scheduled_time:
                scheduled_platforms.append(platform_name)
        
        # If no scheduled times, return error
        if not scheduled_platforms:
            logger.error(f"No scheduled times found for post: {post.id}")
            return {'success': False, 'error': "No scheduled times found"}
        
        # Save the post
        post_path = self._save_post(post)
        
        # Create a scheduled post
        scheduled_post = ScheduledPost(
            post_id=post.id,
            scheduled_time=min(post.platform_posts[p].scheduled_time for p in scheduled_platforms),
            platforms=scheduled_platforms,
            post_data_path=post_path
        )
        
        # Add to schedule
        self.schedule.add_post(scheduled_post)
        
        # Save the schedule
        self._save_schedule()
        
        # Update post status
        post.status = "scheduled"
        self._save_post(post)
        
        return {
            'success': True,
            'status': "scheduled",
            'scheduled_time': scheduled_post.scheduled_time.isoformat(),
            'platforms': scheduled_platforms
        }
    
    def process_scheduled_posts(self) -> Dict[str, Any]:
        """
        Process all due scheduled posts.
        
        Returns:
            Dict[str, Any]: Processing results
        """
        logger.info("Processing scheduled posts")
        
        # Get all due posts
        due_posts = self.schedule.get_due_posts()
        
        if not due_posts:
            logger.info("No scheduled posts due")
            return {'success': True, 'processed': 0}
        
        # Process each due post
        processed_count = 0
        results = {}
        
        for scheduled_post in due_posts:
            try:
                # Load the post
                post = self._load_post(scheduled_post.post_data_path)
                
                # Publish the post
                publish_result = self.publish_post(post)
                
                # Update the scheduled post
                if publish_result.get('success', False):
                    scheduled_post.mark_published()
                    processed_count += 1
                else:
                    error = publish_result.get('error', "Unknown error")
                    scheduled_post.mark_failed(error)
                
                # Save the results
                results[scheduled_post.post_id] = publish_result
            
            except Exception as e:
                logger.error(f"Error processing scheduled post {scheduled_post.post_id}: {str(e)}")
                scheduled_post.mark_failed(str(e))
        
        # Save the schedule
        self._save_schedule()
        
        return {
            'success': processed_count > 0,
            'processed': processed_count,
            'total': len(due_posts),
            'results': results
        }
    
    def retry_failed_posts(self) -> Dict[str, Any]:
        """
        Retry all failed posts that can be retried.
        
        Returns:
            Dict[str, Any]: Retry results
        """
        logger.info("Retrying failed posts")
        
        # Get all failed posts that can be retried
        failed_posts = [post for post in self.schedule.get_posts_by_status("failed") 
                       if post.can_retry]
        
        if not failed_posts:
            logger.info("No failed posts to retry")
            return {'success': True, 'retried': 0}
        
        # Retry each failed post
        retried_count = 0
        success_count = 0
        results = {}
        
        for scheduled_post in failed_posts:
            try:
                # Load the post
                post = self._load_post(scheduled_post.post_data_path)
                
                # Publish the post
                publish_result = self.publish_post(post)
                
                # Update the scheduled post
                if publish_result.get('success', False):
                    scheduled_post.mark_published()
                    success_count += 1
                else:
                    error = publish_result.get('error', "Unknown error")
                    scheduled_post.mark_failed(error)
                
                retried_count += 1
                
                # Save the results
                results[scheduled_post.post_id] = publish_result
            
            except Exception as e:
                logger.error(f"Error retrying scheduled post {scheduled_post.post_id}: {str(e)}")
                scheduled_post.mark_failed(str(e))
        
        # Save the schedule
        self._save_schedule()
        
        return {
            'success': success_count > 0,
            'retried': retried_count,
            'succeeded': success_count,
            'results': results
        }
    
    def _save_post(self, post: Post) -> Path:
        """
        Save a post to disk.
        
        Args:
            post: The post to save
            
        Returns:
            Path: Path to the saved post
        """
        # Create the processed directory if it doesn't exist
        processed_dir = Path(settings.PROCESSED_DIRECTORY)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the post to a JSON file
        post_file = processed_dir / f"{post.id}.json"
        post.save_to_file(post_file)
        
        logger.debug(f"Saved post to {post_file}")
        return post_file
    
    def _load_post(self, post_path: Path) -> Post:
        """
        Load a post from disk.
        
        Args:
            post_path: Path to the post file
            
        Returns:
            Post: The loaded post
        """
        return Post.load_from_file(post_path)
    
    def _save_schedule(self) -> None:
        """Save the schedule to disk."""
        schedule_file = Path(settings.PROCESSED_DIRECTORY) / "schedule.json"
        self.schedule.save_to_file(schedule_file)
        logger.debug(f"Saved schedule to {schedule_file}")
    
    def _load_schedule(self) -> Schedule:
        """
        Load the schedule from disk.
        
        Returns:
            Schedule: The loaded schedule
        """
        schedule_file = Path(settings.PROCESSED_DIRECTORY) / "schedule.json"
        if schedule_file.exists():
            return Schedule.load_from_file(schedule_file)
        else:
            return Schedule()

