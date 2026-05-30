"""
Base class for social media platform integrations.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models.post import PlatformPost, MediaItem

# Configure logger
logger = logging.getLogger(__name__)


class PlatformBase(ABC):
    """
    Base class for all social media platform integrations.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the platform.
        
        Args:
            config: Platform-specific configuration
        """
        self.config = config
        self.name = "base"
        self.enabled = config.get('enabled', False)
        self.authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def publish_post(self, post: PlatformPost) -> Dict[str, Any]:
        """
        Publish a post to the platform.
        
        Args:
            post: The post to publish
            
        Returns:
            Dict[str, Any]: Response data including post ID, URL, etc.
        """
        pass
    
    @abstractmethod
    def upload_media(self, media_item: MediaItem) -> str:
        """
        Upload a media item to the platform.
        
        Args:
            media_item: The media item to upload
            
        Returns:
            str: Media ID or URL
        """
        pass
    
    def validate_post(self, post: PlatformPost) -> bool:
        """
        Validate a post before publishing.
        
        Args:
            post: The post to validate
            
        Returns:
            bool: True if the post is valid, False otherwise
        """
        # Check if the platform is enabled
        if not self.enabled:
            logger.error(f"{self.name} platform is not enabled")
            return False
        
        # Check if we're authenticated
        if not self.authenticated:
            logger.error(f"Not authenticated with {self.name}")
            return False
        
        # Check if the post has text or media
        if not post.text and not post.media:
            logger.error(f"Post must have text or media")
            return False
        
        # Check text length
        if post.text and 'character_limit' in self.config:
            if len(post.full_text) > self.config['character_limit']:
                logger.error(f"Text exceeds character limit for {self.name}")
                return False
        
        # Check media count
        if post.media and 'max_images' in self.config:
            if len(post.media) > self.config['max_images']:
                logger.error(f"Too many media items for {self.name}")
                return False
        
        return True
    
    def format_post(self, post: PlatformPost) -> Dict[str, Any]:
        """
        Format a post for the platform API.
        
        Args:
            post: The post to format
            
        Returns:
            Dict[str, Any]: Formatted post data
        """
        # Default implementation, override in subclasses
        return {
            'text': post.full_text,
            'media': [m.path for m in post.media],
            'link': post.link
        }
    
    def handle_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the response from the platform API.
        
        Args:
            response: The raw response from the API
            
        Returns:
            Dict[str, Any]: Processed response data
        """
        # Default implementation, override in subclasses
        return {
            'success': True,
            'platform': self.name,
            'response': response
        }
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle an error from the platform API.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Dict[str, Any]: Error data
        """
        logger.error(f"Error in {self.name} platform: {str(error)}")
        return {
            'success': False,
            'platform': self.name,
            'error': str(error)
        }


class PlatformFactory:
    """
    Factory for creating platform instances.
    """
    @staticmethod
    def create_platform(platform_name: str, config: Dict[str, Any]) -> Optional[PlatformBase]:
        """
        Create a platform instance.
        
        Args:
            platform_name: Name of the platform
            config: Platform-specific configuration
            
        Returns:
            Optional[PlatformBase]: Platform instance, or None if not supported
        """
        platform_name = platform_name.lower()
        
        # Import platform classes here to avoid circular imports
        from .twitter import TwitterPlatform
        from .facebook import FacebookPlatform
        from .instagram import InstagramPlatform
        from .linkedin import LinkedInPlatform
        from .ayrshare import AyrsharePlatform
        
        # Create the appropriate platform instance
        if platform_name == 'twitter':
            return TwitterPlatform(config)
        elif platform_name == 'facebook':
            return FacebookPlatform(config)
        elif platform_name == 'instagram':
            return InstagramPlatform(config)
        elif platform_name == 'linkedin':
            return LinkedInPlatform(config)
        elif platform_name == 'ayrshare':
            return AyrsharePlatform(config)
        else:
            logger.error(f"Unsupported platform: {platform_name}")
            return None

