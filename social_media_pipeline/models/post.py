"""
Post model representing processed content ready for publishing.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import json


@dataclass
class MediaItem:
    """Represents a media item (image, video, etc.) in a post."""
    path: Path
    media_type: str  # 'image', 'video', 'gif', etc.
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    url: Optional[str] = None  # URL if uploaded to a service
    
    @property
    def is_local(self) -> bool:
        """Check if the media is local (has a path) or remote (has a URL)."""
        return self.url is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'path': str(self.path) if self.path else None,
            'media_type': self.media_type,
            'alt_text': self.alt_text,
            'width': self.width,
            'height': self.height,
            'size_bytes': self.size_bytes,
            'url': self.url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MediaItem':
        """Create a MediaItem from a dictionary."""
        path = data.get('path')
        if path:
            path = Path(path)
        
        return cls(
            path=path,
            media_type=data.get('media_type'),
            alt_text=data.get('alt_text'),
            width=data.get('width'),
            height=data.get('height'),
            size_bytes=data.get('size_bytes'),
            url=data.get('url')
        )


@dataclass
class PlatformPost:
    """Platform-specific post content."""
    platform: str
    text: str
    hashtags: List[str] = field(default_factory=list)
    media: List[MediaItem] = field(default_factory=list)
    link: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_text(self) -> str:
        """Get the full text including hashtags."""
        if not self.hashtags:
            return self.text
        
        hashtag_text = ' '.join([f"#{tag}" for tag in self.hashtags])
        return f"{self.text}\n\n{hashtag_text}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'platform': self.platform,
            'text': self.text,
            'hashtags': self.hashtags,
            'media': [m.to_dict() for m in self.media],
            'link': self.link,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'custom_params': self.custom_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformPost':
        """Create a PlatformPost from a dictionary."""
        scheduled_time = data.get('scheduled_time')
        if scheduled_time:
            scheduled_time = datetime.fromisoformat(scheduled_time)
        
        media = [MediaItem.from_dict(m) for m in data.get('media', [])]
        
        return cls(
            platform=data.get('platform'),
            text=data.get('text'),
            hashtags=data.get('hashtags', []),
            media=media,
            link=data.get('link'),
            scheduled_time=scheduled_time,
            custom_params=data.get('custom_params', {})
        )


@dataclass
class Post:
    """A complete post ready for publishing to multiple platforms."""
    id: str
    original_content_path: Path
    created_at: datetime = field(default_factory=datetime.now)
    title: Optional[str] = None
    summary: Optional[str] = None
    platform_posts: Dict[str, PlatformPost] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"  # draft, ready, scheduled, published, failed
    
    def add_platform_post(self, platform_post: PlatformPost) -> None:
        """Add a platform-specific post."""
        self.platform_posts[platform_post.platform] = platform_post
    
    def get_platform_post(self, platform: str) -> Optional[PlatformPost]:
        """Get a platform-specific post."""
        return self.platform_posts.get(platform)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'original_content_path': str(self.original_content_path),
            'created_at': self.created_at.isoformat(),
            'title': self.title,
            'summary': self.summary,
            'platform_posts': {k: v.to_dict() for k, v in self.platform_posts.items()},
            'metadata': self.metadata,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Post':
        """Create a Post from a dictionary."""
        platform_posts = {}
        for platform, post_data in data.get('platform_posts', {}).items():
            platform_posts[platform] = PlatformPost.from_dict(post_data)
        
        return cls(
            id=data.get('id'),
            original_content_path=Path(data.get('original_content_path')),
            created_at=datetime.fromisoformat(data.get('created_at')),
            title=data.get('title'),
            summary=data.get('summary'),
            platform_posts=platform_posts,
            metadata=data.get('metadata', {}),
            status=data.get('status', 'draft')
        )
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Post':
        """Create a Post from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Path) -> None:
        """Save the post to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'Post':
        """Load a post from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

