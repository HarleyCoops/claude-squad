"""
Image processing utilities for the social media pipeline.
"""
import logging
import os
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Any
import tempfile
import uuid
from PIL import Image
import cv2
import requests
import openai

from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


def resize_image(image_path: Path, target_size: Tuple[int, int], 
                 output_path: Optional[Path] = None, quality: int = 85) -> Path:
    """
    Resize an image to the target dimensions.
    
    Args:
        image_path: Path to the input image
        target_size: Target dimensions (width, height)
        output_path: Path to save the resized image (if None, creates a temp file)
        quality: JPEG quality (0-100)
        
    Returns:
        Path: Path to the resized image
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize the image
            resized_img = img.resize(target_size, Image.LANCZOS)
            
            # Create output path if not provided
            if output_path is None:
                temp_dir = Path(settings.TEMP_DIRECTORY)
                temp_dir.mkdir(parents=True, exist_ok=True)
                output_path = temp_dir / f"resized_{uuid.uuid4().hex}{image_path.suffix}"
            
            # Save the resized image
            resized_img.save(output_path, quality=quality)
            
            return output_path
    
    except Exception as e:
        logger.error(f"Error resizing image {image_path}: {str(e)}")
        raise


def crop_image_for_platform(image_path: Path, platform: str, 
                           output_path: Optional[Path] = None) -> Path:
    """
    Crop and resize an image for a specific platform.
    
    Args:
        image_path: Path to the input image
        platform: Target platform
        output_path: Path to save the processed image
        
    Returns:
        Path: Path to the processed image
    """
    # Get platform-specific image dimensions
    platform_dimensions = settings.DEFAULT_IMAGE_SIZE.get(platform.lower())
    if not platform_dimensions:
        logger.warning(f"No image dimensions defined for platform {platform}. Using default.")
        platform_dimensions = (1200, 630)  # Default dimensions
    
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get original dimensions
            orig_width, orig_height = img.size
            target_width, target_height = platform_dimensions
            
            # Calculate target aspect ratio
            target_ratio = target_width / target_height
            orig_ratio = orig_width / orig_height
            
            # Determine if we need to crop width or height
            if orig_ratio > target_ratio:
                # Image is wider than target ratio, crop width
                new_width = int(orig_height * target_ratio)
                left = (orig_width - new_width) // 2
                right = left + new_width
                img = img.crop((left, 0, right, orig_height))
            elif orig_ratio < target_ratio:
                # Image is taller than target ratio, crop height
                new_height = int(orig_width / target_ratio)
                top = (orig_height - new_height) // 2
                bottom = top + new_height
                img = img.crop((0, top, orig_width, bottom))
            
            # Resize to target dimensions
            img = img.resize(platform_dimensions, Image.LANCZOS)
            
            # Create output path if not provided
            if output_path is None:
                temp_dir = Path(settings.TEMP_DIRECTORY)
                temp_dir.mkdir(parents=True, exist_ok=True)
                output_path = temp_dir / f"{platform.lower()}_{uuid.uuid4().hex}{image_path.suffix}"
            
            # Save the processed image
            img.save(output_path, quality=settings.IMAGE_QUALITY)
            
            return output_path
    
    except Exception as e:
        logger.error(f"Error processing image {image_path} for platform {platform}: {str(e)}")
        raise


def generate_alt_text_for_image(image_path: Path) -> str:
    """
    Generate alt text for an image using AI.
    
    Args:
        image_path: Path to the image
        
    Returns:
        str: Generated alt text
    """
    if not settings.GENERATE_ALT_TEXT:
        return "Image from social media post"
    
    if settings.AI_PROVIDER == "openai":
        return generate_alt_text_with_openai(image_path)
    else:
        return "Image from social media post"


def generate_alt_text_with_openai(image_path: Path) -> str:
    """
    Generate alt text for an image using OpenAI's API.
    
    Args:
        image_path: Path to the image
        
    Returns:
        str: Generated alt text
    """
    try:
        # Check if OpenAI API key is configured
        if not openai.api_key:
            openai.api_key = settings.OPENAI_API_KEY
        
        if not openai.api_key:
            logger.warning("OpenAI API key not configured. Returning default alt text.")
            return "Image from social media post"
        
        # Open the image file
        with open(image_path, "rb") as image_file:
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please describe this image concisely for alt text. Keep it under 100 characters."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )
            
            # Extract the alt text
            alt_text = response.choices[0].message.content.strip()
            
            # Ensure it's not too long
            if len(alt_text) > 100:
                alt_text = alt_text[:97] + "..."
            
            return alt_text
    
    except Exception as e:
        logger.error(f"Error generating alt text with OpenAI: {str(e)}")
        return "Image from social media post"


def compress_image(image_path: Path, max_size_kb: int = 1024, 
                  output_path: Optional[Path] = None) -> Path:
    """
    Compress an image to be under a maximum file size.
    
    Args:
        image_path: Path to the input image
        max_size_kb: Maximum file size in KB
        output_path: Path to save the compressed image
        
    Returns:
        Path: Path to the compressed image
    """
    try:
        # Get current file size
        current_size_kb = os.path.getsize(image_path) / 1024
        
        # If already under max size, return original
        if current_size_kb <= max_size_kb:
            return image_path
        
        # Create output path if not provided
        if output_path is None:
            temp_dir = Path(settings.TEMP_DIRECTORY)
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_path = temp_dir / f"compressed_{uuid.uuid4().hex}{image_path.suffix}"
        
        # Start with quality 85
        quality = 85
        
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save with initial quality
            img.save(output_path, quality=quality)
            
            # Check size and reduce quality until under max size
            while os.path.getsize(output_path) / 1024 > max_size_kb and quality > 10:
                quality -= 5
                img.save(output_path, quality=quality)
            
            # If still too large, resize the image
            if os.path.getsize(output_path) / 1024 > max_size_kb:
                width, height = img.size
                ratio = 0.9  # Reduce by 10%
                
                while os.path.getsize(output_path) / 1024 > max_size_kb and ratio > 0.1:
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    resized_img.save(output_path, quality=quality)
                    ratio -= 0.1
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error compressing image {image_path}: {str(e)}")
        raise


def upload_image_to_public_url(image_path: Path) -> str:
    """
    Upload an image to a public URL (for use with Ayrshare).
    
    This is a placeholder function. In a real implementation, you would
    upload the image to a service like S3, Cloudinary, or Imgur.
    
    Args:
        image_path: Path to the image
        
    Returns:
        str: Public URL of the uploaded image
    """
    # This is a placeholder. In a real implementation, you would:
    # 1. Upload the image to a service like S3, Cloudinary, or Imgur
    # 2. Return the public URL
    
    # For now, just return a placeholder URL
    logger.warning("Image upload to public URL not implemented. Returning placeholder.")
    return f"https://example.com/images/{image_path.name}"


def process_images_for_platforms(image_paths: List[Path], platforms: List[str]) -> Dict[str, List[Path]]:
    """
    Process images for multiple platforms.
    
    Args:
        image_paths: List of paths to input images
        platforms: List of target platforms
        
    Returns:
        Dict[str, List[Path]]: Dictionary mapping platforms to lists of processed image paths
    """
    result = {}
    
    for platform in platforms:
        platform_images = []
        
        for image_path in image_paths:
            try:
                # Crop and resize for the platform
                processed_path = crop_image_for_platform(image_path, platform)
                
                # Compress if needed
                platform_config = settings.PLATFORM_CONFIGS.get(platform.lower(), {})
                max_image_size_kb = platform_config.get('max_image_size_kb', 1024)
                compressed_path = compress_image(processed_path, max_image_size_kb)
                
                platform_images.append(compressed_path)
            except Exception as e:
                logger.error(f"Error processing image {image_path} for {platform}: {str(e)}")
                # Skip this image and continue with others
        
        result[platform] = platform_images
    
    return result


# Add missing import for base64
import base64

