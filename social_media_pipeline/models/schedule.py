"""
Schedule model for managing scheduled posts.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
import json
from pathlib import Path
import pytz


@dataclass
class ScheduledPost:
    """A post scheduled for publishing."""
    post_id: str
    scheduled_time: datetime
    platforms: List[str]
    post_data_path: Path
    status: str = "pending"  # pending, published, failed, cancelled
    attempts: int = 0
    max_attempts: int = 3
    last_attempt: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def is_due(self) -> bool:
        """Check if the post is due for publishing."""
        return datetime.now(pytz.UTC) >= self.scheduled_time.astimezone(pytz.UTC)
    
    @property
    def can_retry(self) -> bool:
        """Check if the post can be retried."""
        return self.status == "failed" and self.attempts < self.max_attempts
    
    def mark_published(self) -> None:
        """Mark the post as published."""
        self.status = "published"
        self.last_attempt = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """Mark the post as failed."""
        self.status = "failed"
        self.attempts += 1
        self.last_attempt = datetime.now()
        self.error = error
    
    def mark_cancelled(self) -> None:
        """Mark the post as cancelled."""
        self.status = "cancelled"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'post_id': self.post_id,
            'scheduled_time': self.scheduled_time.isoformat(),
            'platforms': self.platforms,
            'post_data_path': str(self.post_data_path),
            'status': self.status,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledPost':
        """Create a ScheduledPost from a dictionary."""
        scheduled_time = datetime.fromisoformat(data.get('scheduled_time'))
        
        last_attempt = data.get('last_attempt')
        if last_attempt:
            last_attempt = datetime.fromisoformat(last_attempt)
        
        return cls(
            post_id=data.get('post_id'),
            scheduled_time=scheduled_time,
            platforms=data.get('platforms', []),
            post_data_path=Path(data.get('post_data_path')),
            status=data.get('status', 'pending'),
            attempts=data.get('attempts', 0),
            max_attempts=data.get('max_attempts', 3),
            last_attempt=last_attempt,
            error=data.get('error')
        )


@dataclass
class Schedule:
    """A schedule of posts to be published."""
    scheduled_posts: List[ScheduledPost] = field(default_factory=list)
    
    def add_post(self, scheduled_post: ScheduledPost) -> None:
        """Add a post to the schedule."""
        self.scheduled_posts.append(scheduled_post)
        # Sort by scheduled time
        self.scheduled_posts.sort(key=lambda p: p.scheduled_time)
    
    def remove_post(self, post_id: str) -> bool:
        """Remove a post from the schedule."""
        for i, post in enumerate(self.scheduled_posts):
            if post.post_id == post_id:
                del self.scheduled_posts[i]
                return True
        return False
    
    def get_post(self, post_id: str) -> Optional[ScheduledPost]:
        """Get a post from the schedule."""
        for post in self.scheduled_posts:
            if post.post_id == post_id:
                return post
        return None
    
    def get_due_posts(self) -> List[ScheduledPost]:
        """Get all posts that are due for publishing."""
        return [post for post in self.scheduled_posts 
                if post.status == "pending" and post.is_due]
    
    def get_posts_by_status(self, status: str) -> List[ScheduledPost]:
        """Get all posts with a specific status."""
        return [post for post in self.scheduled_posts if post.status == status]
    
    def get_posts_by_platform(self, platform: str) -> List[ScheduledPost]:
        """Get all posts for a specific platform."""
        return [post for post in self.scheduled_posts if platform in post.platforms]
    
    def get_posts_in_timeframe(self, start: datetime, end: datetime) -> List[ScheduledPost]:
        """Get all posts scheduled within a specific timeframe."""
        return [post for post in self.scheduled_posts 
                if start <= post.scheduled_time <= end]
    
    def get_next_post(self) -> Optional[ScheduledPost]:
        """Get the next pending post."""
        pending_posts = [post for post in self.scheduled_posts if post.status == "pending"]
        if not pending_posts:
            return None
        return min(pending_posts, key=lambda p: p.scheduled_time)
    
    def get_platforms(self) -> Set[str]:
        """Get all platforms in the schedule."""
        platforms = set()
        for post in self.scheduled_posts:
            platforms.update(post.platforms)
        return platforms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'scheduled_posts': [post.to_dict() for post in self.scheduled_posts]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Create a Schedule from a dictionary."""
        scheduled_posts = [ScheduledPost.from_dict(post_data) 
                          for post_data in data.get('scheduled_posts', [])]
        return cls(scheduled_posts=scheduled_posts)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Schedule':
        """Create a Schedule from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Path) -> None:
        """Save the schedule to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'Schedule':
        """Load a schedule from a JSON file."""
        if not file_path.exists():
            return cls()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
    
    def clean_old_posts(self, days: int = 30) -> int:
        """Remove posts older than a certain number of days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        old_posts = [post for post in self.scheduled_posts 
                    if post.status in ["published", "failed", "cancelled"] 
                    and post.scheduled_time < cutoff_date]
        
        for post in old_posts:
            self.remove_post(post.post_id)
        
        return len(old_posts)

