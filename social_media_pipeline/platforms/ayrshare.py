"""
Ayrshare platform integration for multi-platform posting.
"""
import logging
from typing import Dict, Any, List
import os
from pathlib import Path

from social_post_api import SocialPost

from .platform_base import PlatformBase
from ..models.post import PlatformPost, MediaItem
from ..utils import image_utils

# Configure logger
logger = logging.getLogger(__name__)


class AyrsharePlatform(PlatformBase):
    """
    Ayrshare platform integration for posting to multiple social media platforms.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Ayrshare platform.
        
        Args:
            config: Ayrshare configuration
        """
        super().__init__(config)
        self.name = "ayrshare"
        self.api_key = config.get('api_key', os.environ.get('AYRSHARE_API_KEY', ''))
        self.enabled_platforms = config.get('enabled_platforms', [])
        self.shorten_links = config.get('shorten_links', True)
        self.client = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Ayrshare.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("Ayrshare API key not configured")
                return False
            
            # Initialize the client
            self.client = SocialPost(self.api_key)
            
            # Test the connection by getting the user profile
            profile = self.client.get_profile()
            
            if 'status' in profile and profile['status'] == 'success':
                logger.info("Successfully authenticated with Ayrshare")
                self.authenticated = True
                return True
            else:
                logger.error(f"Failed to authenticate with Ayrshare: {profile.get('message', 'Unknown error')}")
                return False
        
        except Exception as e:
            logger.error(f"Error authenticating with Ayrshare: {str(e)}")
            return False
    
    def publish_post(self, post: PlatformPost) -> Dict[str, Any]:
        """
        Publish a post to multiple platforms via Ayrshare.
        
        Args:
            post: The post to publish
            
        Returns:
            Dict[str, Any]: Response data including post ID, URL, etc.
        """
        try:
            # Validate the post
            if not self.validate_post(post):
                return {
                    'success': False,
                    'platform': self.name,
                    'error': "Post validation failed"
                }
            
            # Format the post for Ayrshare
            post_data = self.format_post(post)
            
            # Publish the post
            response = self.client.post(post_data)
            
            # Handle the response
            return self.handle_response(response)
        
        except Exception as e:
            return self.handle_error(e)
    
    def upload_media(self, media_item: MediaItem) -> str:
        """
        Upload a media item to a public URL for Ayrshare.
        
        Ayrshare requires media to be accessible via public URLs.
        This method uploads the media to a public location and returns the URL.
        
        Args:
            media_item: The media item to upload
            
        Returns:
            str: Public URL of the uploaded media
        """
        try:
            # Upload the media to a public URL
            public_url = image_utils.upload_image_to_public_url(media_item.path)
            
            logger.info(f"Uploaded media to public URL: {public_url}")
            return public_url
        
        except Exception as e:
            logger.error(f"Error uploading media for Ayrshare: {str(e)}")
            raise
    
    def validate_post(self, post: PlatformPost) -> bool:
        """
        Validate a post before publishing.
        
        Args:
            post: The post to validate
            
        Returns:
            bool: True if the post is valid, False otherwise
        """
        # Check if we're authenticated
        if not self.authenticated:
            logger.error("Not authenticated with Ayrshare")
            return False
        
        # Check if the post has text or media
        if not post.text and not post.media:
            logger.error("Post must have text or media")
            return False
        
        # Check if any platforms are enabled
        if not self.enabled_platforms:
            logger.error("No platforms enabled for Ayrshare")
            return False
        
        return True
    
    def format_post(self, post: PlatformPost) -> Dict[str, Any]:
        """
        Format a post for the Ayrshare API.
        
        Args:
            post: The post to format
            
        Returns:
            Dict[str, Any]: Formatted post data
        """
        # Prepare the post data
        post_data = {
            'post': post.full_text,
            'platforms': self.enabled_platforms,
            'shorten_links': self.shorten_links
        }
        
        # Add media URLs if available
        if post.media:
            media_urls = []
            for media_item in post.media:
                if media_item.url:
                    # If the media already has a URL, use it
                    media_urls.append(media_item.url)
                else:
                    # Otherwise, upload the media and get a URL
                    media_url = self.upload_media(media_item)
                    media_urls.append(media_url)
            
            if media_urls:
                post_data['mediaUrls'] = media_urls
        
        # Add link if available
        if post.link:
            post_data['link'] = post.link
        
        # Add scheduled time if available
        if post.scheduled_time:
            post_data['scheduleDate'] = post.scheduled_time.isoformat()
        
        return post_data
    
    def handle_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the response from the Ayrshare API.
        
        Args:
            response: The raw response from the API
            
        Returns:
            Dict[str, Any]: Processed response data
        """
        if 'status' in response and response['status'] == 'success':
            logger.info(f"Successfully published post via Ayrshare: {response.get('id', 'Unknown ID')}")
            return {
                'success': True,
                'platform': self.name,
                'post_id': response.get('id'),
                'status': response.get('status'),
                'platforms': response.get('platforms', []),
                'response': response
            }
        else:
            logger.error(f"Failed to publish post via Ayrshare: {response.get('message', 'Unknown error')}")
            return {
                'success': False,
                'platform': self.name,
                'error': response.get('message', 'Unknown error'),
                'response': response
            }

