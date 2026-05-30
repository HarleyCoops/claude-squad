"""
Scheduler component for the social media pipeline.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from ..models.schedule import Schedule, ScheduledPost
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class Scheduler:
    """
    Manages scheduled posts and optimal posting times.
    """
    def __init__(self, publish_callback: Callable[[str], Dict[str, Any]]):
        """
        Initialize the scheduler.
        
        Args:
            publish_callback: Function to call when a post is due for publishing
        """
        self.publish_callback = publish_callback
        self.scheduler = BackgroundScheduler()
        self.schedule = self._load_schedule()
        self.timezone = pytz.timezone(settings.DEFAULT_TIMEZONE)
    
    def start(self) -> None:
        """Start the scheduler."""
        logger.info("Starting scheduler")
        
        # Schedule the check for due posts
        self.scheduler.add_job(
            self._check_due_posts,
            IntervalTrigger(seconds=settings.SCHEDULE_CHECK_INTERVAL),
            id='check_due_posts',
            replace_existing=True
        )
        
        # Schedule cleanup of old posts
        self.scheduler.add_job(
            self._cleanup_old_posts,
            CronTrigger(hour=0, minute=0),  # Run at midnight
            id='cleanup_old_posts',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping scheduler")
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def schedule_post(self, post_id: str, scheduled_time: datetime, 
                     platforms: List[str], post_data_path: Path) -> ScheduledPost:
        """
        Schedule a post for publishing.
        
        Args:
            post_id: ID of the post to schedule
            scheduled_time: Time to publish the post
            platforms: Platforms to publish to
            post_data_path: Path to the post data
            
        Returns:
            ScheduledPost: The scheduled post
        """
        logger.info(f"Scheduling post {post_id} for {scheduled_time}")
        
        # Create a scheduled post
        scheduled_post = ScheduledPost(
            post_id=post_id,
            scheduled_time=scheduled_time,
            platforms=platforms,
            post_data_path=post_data_path
        )
        
        # Add to schedule
        self.schedule.add_post(scheduled_post)
        
        # Save the schedule
        self._save_schedule()
        
        return scheduled_post
    
    def cancel_scheduled_post(self, post_id: str) -> bool:
        """
        Cancel a scheduled post.
        
        Args:
            post_id: ID of the post to cancel
            
        Returns:
            bool: True if the post was cancelled, False otherwise
        """
        logger.info(f"Cancelling scheduled post {post_id}")
        
        # Get the scheduled post
        scheduled_post = self.schedule.get_post(post_id)
        
        if not scheduled_post:
            logger.warning(f"Scheduled post {post_id} not found")
            return False
        
        # Mark as cancelled
        scheduled_post.mark_cancelled()
        
        # Save the schedule
        self._save_schedule()
        
        return True
    
    def get_optimal_time(self, platform: str, start_time: Optional[datetime] = None) -> datetime:
        """
        Get the optimal time to post for a platform.
        
        Args:
            platform: The target platform
            start_time: The earliest time to consider (defaults to now)
            
        Returns:
            datetime: The optimal posting time
        """
        # If no start time provided, use now
        if start_time is None:
            start_time = datetime.now(self.timezone)
        elif start_time.tzinfo is None:
            # Add timezone if not provided
            start_time = self.timezone.localize(start_time)
        
        # Get optimal times for the platform
        optimal_times = settings.OPTIMAL_POSTING_TIMES.get(platform.lower(), ["9:00", "12:00", "15:00", "18:00"])
        
        # Convert to datetime objects
        today = start_time.date()
        optimal_datetimes = []
        
        for time_str in optimal_times:
            try:
                # Parse the time string
                hour, minute = map(int, time_str.split(':'))
                
                # Create a datetime
                optimal_time = self.timezone.localize(
                    datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                )
                
                # If the time is in the past, use tomorrow
                if optimal_time < start_time:
                    optimal_time = self.timezone.localize(
                        datetime.combine(today + timedelta(days=1), 
                                        datetime.min.time().replace(hour=hour, minute=minute))
                    )
                
                optimal_datetimes.append(optimal_time)
            
            except Exception as e:
                logger.error(f"Error parsing optimal time {time_str}: {str(e)}")
        
        # If no valid times, use start_time + 1 hour
        if not optimal_datetimes:
            return start_time + timedelta(hours=1)
        
        # Find the next optimal time
        next_optimal_time = min(optimal_datetimes, key=lambda dt: abs((dt - start_time).total_seconds()))
        
        # If the next optimal time is in the past, use the next day
        if next_optimal_time < start_time:
            next_day = today + timedelta(days=1)
            next_optimal_time = self.timezone.localize(
                datetime.combine(next_day, next_optimal_time.time())
            )
        
        return next_optimal_time
    
    def _check_due_posts(self) -> None:
        """Check for posts that are due for publishing."""
        logger.debug("Checking for due posts")
        
        # Get all due posts
        due_posts = self.schedule.get_due_posts()
        
        if not due_posts:
            return
        
        logger.info(f"Found {len(due_posts)} due posts")
        
        # Process each due post
        for scheduled_post in due_posts:
            try:
                # Call the publish callback
                result = self.publish_callback(scheduled_post.post_id)
                
                # Update the scheduled post
                if result.get('success', False):
                    scheduled_post.mark_published()
                else:
                    error = result.get('error', "Unknown error")
                    scheduled_post.mark_failed(error)
            
            except Exception as e:
                logger.error(f"Error publishing scheduled post {scheduled_post.post_id}: {str(e)}")
                scheduled_post.mark_failed(str(e))
        
        # Save the schedule
        self._save_schedule()
    
    def _cleanup_old_posts(self) -> None:
        """Clean up old posts from the schedule."""
        logger.info("Cleaning up old posts")
        
        # Clean up posts older than 30 days
        removed_count = self.schedule.clean_old_posts(days=30)
        
        logger.info(f"Removed {removed_count} old posts from schedule")
        
        # Save the schedule
        self._save_schedule()
    
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

