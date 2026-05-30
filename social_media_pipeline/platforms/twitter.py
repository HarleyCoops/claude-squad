"""
Twitter platform integration.
"""
import logging
import os
from typing import Dict, Any, List
from pathlib import Path

import tweepy

from .platform_base import PlatformBase
from ..models.post import PlatformPost, MediaItem

# Configure logger
logger = logging.getLogger(__name__)


class TwitterPlatform(PlatformBase):
    """
    Twitter platform integration.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Twitter platform.
        
        Args:
            config: Twitter configuration
        """
        super().__init__(config)
        self.name = "twitter"
        self.consumer_key = config.get('consumer_key', os.environ.get('TWITTER_CONSUMER_KEY', ''))
        self.consumer_secret = config.get('consumer_secret', os.environ.get('TWITTER_CONSUMER_SECRET', ''))
        self.access_token = config.get('access_token', os.environ.get('TWITTER_ACCESS_TOKEN', ''))
        self.access_token_secret = config.get('access_token_secret', os.environ.get('TWITTER_ACCESS_TOKEN_SECRET', ''))
        self.character_limit = config.get('character_limit', 280)
        self.max_images = config.get('max_images', 4)
        self.api = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Twitter.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Check if credentials are configured
            if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
                logger.error("Twitter credentials not fully configured")
                return False
            
            # Create authentication handler
            auth = tweepy.OAuth1UserHandler(
                self.consumer_key,
                self.consumer_secret,
                self.access_token,
                self.access_token_secret
            )
            
            # Create API instance
            self.api = tweepy.API(auth)
            
            # Verify credentials
            self.api.verify_credentials()
            
            logger.info("Successfully authenticated with Twitter")
            self.authenticated = True
            return True
        
        except Exception as e:
            logger.error(f"Error authenticating with Twitter: {str(e)}")
            return False
    
    def publish_post(self, post: PlatformPost) -> Dict[str, Any]:
        """
        Publish a post to Twitter.
        
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
            
            # Upload media if available
            media_ids = []
            if post.media:
                # Limit to max_images
                for media_item in post.media[:self.max_images]:
                    media_id = self.upload_media(media_item)
                    if media_id:
                        media_ids.append(media_id)
            
            # Prepare the post text
            post_text = post.full_text
            
            # Create the tweet
            if media_ids:
                response = self.api.update_status(
                    status=post_text,
                    media_ids=media_ids
                )
            else:
                response = self.api.update_status(
                    status=post_text
                )
            
            # Handle the response
            return self.handle_response(response._json)
        
        except Exception as e:
            return self.handle_error(e)
    
    def upload_media(self, media_item: MediaItem) -> str:
        """
        Upload a media item to Twitter.
        
        Args:
            media_item: The media item to upload
            
        Returns:
            str: Media ID
        """
        try:
            # Upload the media
            media = self.api.media_upload(str(media_item.path))
            
            # Set alt text if available
            if media_item.alt_text:
                self.api.create_media_metadata(
                    media_id=media.media_id,
                    alt_text=media_item.alt_text
                )
            
            logger.info(f"Successfully uploaded media to Twitter: {media.media_id}")
            return media.media_id
        
        except Exception as e:
            logger.error(f"Error uploading media to Twitter: {str(e)}")
            return None
    
    def validate_post(self, post: PlatformPost) -> bool:
        """
        Validate a post before publishing.
        
        Args:
            post: The post to validate
            
        Returns:
            bool: True if the post is valid, False otherwise
        """
        # Call the parent validation method
        if not super().validate_post(post):
            return False
        
        # Check text length
        if len(post.full_text) > self.character_limit:
            logger.error(f"Text exceeds Twitter character limit: {len(post.full_text)} > {self.character_limit}")
            return False
        
        # Check media count
        if post.media and len(post.media) > self.max_images:
            logger.warning(f"Too many images for Twitter: {len(post.media)} > {self.max_images}. Only the first {self.max_images} will be used.")
        
        return True
    
    def handle_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the response from the Twitter API.
        
        Args:
            response: The raw response from the API
            
        Returns:
            Dict[str, Any]: Processed response data
        """
        tweet_id = response.get('id_str')
        if tweet_id:
            logger.info(f"Successfully published tweet: {tweet_id}")
            return {
                'success': True,
                'platform': self.name,
                'post_id': tweet_id,
                'url': f"https://twitter.com/i/web/status/{tweet_id}",
                'response': response
            }
        else:
            logger.error(f"Failed to publish tweet: {response}")
            return {
                'success': False,
                'platform': self.name,
                'error': "Failed to get tweet ID from response",
                'response': response
            }

