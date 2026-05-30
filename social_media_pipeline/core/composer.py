"""
Post composer component for the social media pipeline.
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..models.post import Post, PlatformPost
from ..utils import text_utils, image_utils
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class PostComposer:
    """
    Composes platform-specific posts from processed content.
    """
    def __init__(self):
        """Initialize the composer."""
        pass
    
    def compose(self, post: Post) -> Post:
        """
        Compose platform-specific posts.
        
        Args:
            post: The post to compose
            
        Returns:
            Post: The updated post with platform-specific posts
        """
        logger.info(f"Composing platform-specific posts for post: {post.id}")
        
        # Get the platforms from the post
        platforms = list(post.platform_posts.keys())
        
        if not platforms:
            logger.warning(f"No platforms specified for post: {post.id}")
            return post
        
        # Compose each platform post
        for platform in platforms:
            try:
                platform_post = post.get_platform_post(platform)
                if not platform_post:
                    logger.warning(f"No platform post found for {platform}")
                    continue
                
                # Compose the platform post
                composed_post = self._compose_platform_post(platform_post, platform)
                
                # Update the post
                post.add_platform_post(composed_post)
                
                logger.info(f"Composed {platform} post for post: {post.id}")
            
            except Exception as e:
                logger.error(f"Error composing {platform} post for post {post.id}: {str(e)}")
                # Continue with other platforms
        
        # Update post status
        if any(p.platform for p in post.platform_posts.values()):
            post.status = "ready"
        else:
            post.status = "failed"
            logger.error(f"Failed to compose any platform posts for post: {post.id}")
        
        return post
    
    def _compose_platform_post(self, platform_post: PlatformPost, platform: str) -> PlatformPost:
        """
        Compose a platform-specific post.
        
        Args:
            platform_post: The platform post to compose
            platform: The target platform
            
        Returns:
            PlatformPost: The composed platform post
        """
        # Get platform-specific configuration
        platform_config = settings.PLATFORM_CONFIGS.get(platform.lower(), {})
        
        # Adjust text for platform character limits
        text, hashtags = text_utils.truncate_text_for_platform(
            platform_post.text, platform, platform_post.hashtags
        )
        
        # Update the platform post
        platform_post.text = text
        platform_post.hashtags = hashtags
        
        # Process media for the platform
        self._process_media_for_platform(platform_post, platform)
        
        return platform_post
    
    def _process_media_for_platform(self, platform_post: PlatformPost, platform: str) -> None:
        """
        Process media for a specific platform.
        
        Args:
            platform_post: The platform post to update
            platform: The target platform
        """
        # Get platform-specific configuration
        platform_config = settings.PLATFORM_CONFIGS.get(platform.lower(), {})
        max_images = platform_config.get('max_images', 4)
        
        # Limit the number of media items
        if len(platform_post.media) > max_images:
            logger.warning(f"Too many media items for {platform}: {len(platform_post.media)} > {max_images}")
            platform_post.media = platform_post.media[:max_images]
        
        # Process each media item
        for i, media_item in enumerate(platform_post.media):
            try:
                # Skip if the media item already has a URL
                if media_item.url:
                    continue
                
                # Get the target dimensions for this platform
                target_dimensions = settings.DEFAULT_IMAGE_SIZE.get(platform.lower())
                if not target_dimensions:
                    continue
                
                # Resize and crop the image
                processed_path = image_utils.crop_image_for_platform(media_item.path, platform)
                
                # Update the media item
                media_item.path = processed_path
                
                # Get image dimensions
                with Image.open(processed_path) as img:
                    media_item.width = img.width
                    media_item.height = img.height
                    media_item.size_bytes = processed_path.stat().st_size
            
            except Exception as e:
                logger.error(f"Error processing media item for {platform}: {str(e)}")
                # Continue with other media items


# Import PIL.Image here to avoid circular imports
from PIL import Image

