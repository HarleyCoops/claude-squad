"""
Content processing component for the social media pipeline.
"""
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
import uuid

from ..models.content import ContentPackage
from ..models.post import Post, PlatformPost, MediaItem
from ..utils import text_utils, image_utils
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class ContentProcessor:
    """
    Processes raw content into platform-ready posts.
    """
    def __init__(self):
        """Initialize the processor."""
        # Create necessary directories
        Path(settings.PROCESSED_DIRECTORY).mkdir(parents=True, exist_ok=True)
        Path(settings.FAILED_DIRECTORY).mkdir(parents=True, exist_ok=True)
        Path(settings.TEMP_DIRECTORY).mkdir(parents=True, exist_ok=True)
    
    def process(self, content_package: ContentPackage) -> Optional[Post]:
        """
        Process a content package into a post.
        
        Args:
            content_package: The content package to process
            
        Returns:
            Optional[Post]: The processed post, or None if processing failed
        """
        try:
            logger.info(f"Processing content package: {content_package.id}")
            
            # Create a new post
            post = Post(
                id=f"post_{uuid.uuid4().hex}",
                original_content_path=content_package.directory
            )
            
            # Process text content
            if content_package.has_text:
                self._process_text(content_package, post)
            
            # Process images
            if content_package.has_images:
                self._process_images(content_package, post)
            
            # Create platform-specific posts
            self._create_platform_posts(content_package, post)
            
            # Save the post
            self._save_post(post)
            
            # Move the content package to the processed directory
            self._move_to_processed(content_package)
            
            logger.info(f"Successfully processed content package: {content_package.id}")
            return post
        
        except Exception as e:
            logger.error(f"Error processing content package {content_package.id}: {str(e)}")
            
            # Move the content package to the failed directory
            self._move_to_failed(content_package)
            
            return None
    
    def _process_text(self, content_package: ContentPackage, post: Post) -> None:
        """
        Process text content.
        
        Args:
            content_package: The content package
            post: The post to update
        """
        # Get the primary text content
        text_content = content_package.primary_text_content
        if not text_content:
            logger.warning(f"No text content found in package {content_package.id}")
            return
        
        # Clean the text
        cleaned_text = text_utils.clean_text(text_content)
        
        # Detect language
        language = text_utils.detect_language(cleaned_text)
        
        # Summarize the text
        summary = text_utils.summarize_text(cleaned_text)
        
        # Extract hashtags
        hashtags = text_utils.extract_hashtags(cleaned_text)
        
        # Add metadata hashtags if available
        if content_package.metadata.hashtags:
            for tag in content_package.metadata.hashtags:
                if tag not in hashtags:
                    hashtags.append(tag)
        
        # Update the post
        post.summary = summary
        post.metadata['language'] = language
        post.metadata['original_text'] = cleaned_text
        post.metadata['hashtags'] = hashtags
        
        # Extract title if available
        if content_package.metadata.title:
            post.title = content_package.metadata.title
        else:
            # Try to extract a title from the first line
            first_line = cleaned_text.split('\n', 1)[0].strip()
            if len(first_line) <= 100:  # Reasonable title length
                post.title = first_line
    
    def _process_images(self, content_package: ContentPackage, post: Post) -> None:
        """
        Process image content.
        
        Args:
            content_package: The content package
            post: The post to update
        """
        # Get all image files
        image_files = content_package.image_files
        if not image_files:
            logger.warning(f"No image files found in package {content_package.id}")
            return
        
        # Process each image
        processed_images = []
        
        for image_file in image_files:
            try:
                # Generate alt text
                alt_text = None
                if content_package.metadata.alt_text:
                    alt_text = content_package.metadata.alt_text
                elif settings.GENERATE_ALT_TEXT:
                    alt_text = image_utils.generate_alt_text_for_image(image_file.path)
                
                # Create a media item
                media_item = MediaItem(
                    path=image_file.path,
                    media_type='image',
                    alt_text=alt_text
                )
                
                processed_images.append(media_item)
            
            except Exception as e:
                logger.error(f"Error processing image {image_file.path}: {str(e)}")
                # Continue with other images
        
        # Update the post
        post.metadata['processed_images'] = [img.to_dict() for img in processed_images]
        post.metadata['image_count'] = len(processed_images)
    
    def _create_platform_posts(self, content_package: ContentPackage, post: Post) -> None:
        """
        Create platform-specific posts.
        
        Args:
            content_package: The content package
            post: The post to update
        """
        # Determine which platforms to post to
        platforms = self._get_target_platforms(content_package)
        
        if not platforms:
            logger.warning(f"No target platforms specified for package {content_package.id}")
            return
        
        # Get the base text and hashtags
        base_text = post.summary or ""
        base_hashtags = post.metadata.get('hashtags', [])
        
        # Get processed images
        processed_images = []
        for img_dict in post.metadata.get('processed_images', []):
            media_item = MediaItem.from_dict(img_dict)
            processed_images.append(media_item)
        
        # Process images for each platform
        platform_images = {}
        if processed_images:
            image_paths = [img.path for img in processed_images]
            platform_images = image_utils.process_images_for_platforms(image_paths, platforms)
        
        # Create a post for each platform
        for platform in platforms:
            try:
                # Get platform-specific content if available
                platform_text = base_text
                platform_hashtags = base_hashtags.copy()
                
                # Check for platform-specific overrides in metadata
                platform_config = content_package.metadata.platforms.get(platform, {})
                if platform_config.get('text'):
                    platform_text = platform_config.get('text')
                if platform_config.get('hashtags'):
                    platform_hashtags = platform_config.get('hashtags')
                
                # Enhance the caption if enabled
                if settings.USE_AI_CAPTION:
                    platform_text = text_utils.enhance_caption(platform_text, platform)
                
                # Truncate text to fit platform limits
                truncated_text, adjusted_hashtags = text_utils.truncate_text_for_platform(
                    platform_text, platform, platform_hashtags
                )
                
                # Get platform-specific images
                platform_media = []
                if platform in platform_images:
                    for i, img_path in enumerate(platform_images[platform]):
                        # Use the alt text from the original image if available
                        alt_text = processed_images[i].alt_text if i < len(processed_images) else None
                        
                        media_item = MediaItem(
                            path=img_path,
                            media_type='image',
                            alt_text=alt_text
                        )
                        platform_media.append(media_item)
                
                # Create the platform post
                platform_post = PlatformPost(
                    platform=platform,
                    text=truncated_text,
                    hashtags=adjusted_hashtags,
                    media=platform_media
                )
                
                # Check for scheduled time
                if content_package.metadata.schedule:
                    schedule_config = content_package.metadata.schedule
                    if 'time' in schedule_config:
                        # If platform is in the schedule platforms list, or no list is specified
                        platforms_list = schedule_config.get('platforms', [])
                        if not platforms_list or platform in platforms_list:
                            platform_post.scheduled_time = schedule_config['time']
                
                # Add the platform post to the post
                post.add_platform_post(platform_post)
                
                logger.info(f"Created {platform} post for package {content_package.id}")
            
            except Exception as e:
                logger.error(f"Error creating {platform} post for package {content_package.id}: {str(e)}")
                # Continue with other platforms
        
        # Update post status
        if post.platform_posts:
            post.status = "ready"
        else:
            post.status = "failed"
            logger.error(f"Failed to create any platform posts for package {content_package.id}")
    
    def _get_target_platforms(self, content_package: ContentPackage) -> List[str]:
        """
        Determine which platforms to post to.
        
        Args:
            content_package: The content package
            
        Returns:
            List[str]: List of target platforms
        """
        # Check if platforms are specified in the metadata
        if content_package.metadata.schedule and 'platforms' in content_package.metadata.schedule:
            return content_package.metadata.schedule['platforms']
        
        # Check if specific platform content is defined
        if content_package.metadata.platforms:
            return list(content_package.metadata.platforms.keys())
        
        # Otherwise, use all enabled platforms from settings
        enabled_platforms = []
        for platform, config in settings.PLATFORM_CONFIGS.items():
            if platform != 'ayrshare' and config.get('enabled', False):
                enabled_platforms.append(platform)
        
        return enabled_platforms
    
    def _save_post(self, post: Post) -> None:
        """
        Save the post to disk.
        
        Args:
            post: The post to save
        """
        # Create the processed directory if it doesn't exist
        processed_dir = Path(settings.PROCESSED_DIRECTORY)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the post to a JSON file
        post_file = processed_dir / f"{post.id}.json"
        post.save_to_file(post_file)
        
        logger.info(f"Saved post to {post_file}")
    
    def _move_to_processed(self, content_package: ContentPackage) -> None:
        """
        Move the content package to the processed directory.
        
        Args:
            content_package: The content package to move
        """
        # Create the processed directory if it doesn't exist
        processed_dir = Path(settings.PROCESSED_DIRECTORY) / "content"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a subdirectory for this package
        package_dir = processed_dir / content_package.id
        
        # If the directory already exists, remove it
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        # Move the content package
        shutil.move(str(content_package.directory), str(package_dir))
        
        logger.info(f"Moved content package {content_package.id} to processed directory")
    
    def _move_to_failed(self, content_package: ContentPackage) -> None:
        """
        Move the content package to the failed directory.
        
        Args:
            content_package: The content package to move
        """
        # Create the failed directory if it doesn't exist
        failed_dir = Path(settings.FAILED_DIRECTORY)
        failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a subdirectory for this package
        package_dir = failed_dir / content_package.id
        
        # If the directory already exists, remove it
        if package_dir.exists():
            shutil.rmtree(package_dir)
        
        # Move the content package
        shutil.move(str(content_package.directory), str(package_dir))
        
        logger.info(f"Moved content package {content_package.id} to failed directory")

