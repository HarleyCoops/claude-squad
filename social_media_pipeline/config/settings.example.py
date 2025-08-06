"""
Example settings for the social media posting pipeline.

Copy this file to settings.py and update with your own values.
"""
import os
from pathlib import Path

# Directory settings
WATCH_DIRECTORY = os.environ.get("WATCH_DIRECTORY", "./content_inbox")
PROCESSED_DIRECTORY = os.environ.get("PROCESSED_DIRECTORY", "./content_processed")
FAILED_DIRECTORY = os.environ.get("FAILED_DIRECTORY", "./content_failed")
TEMP_DIRECTORY = os.environ.get("TEMP_DIRECTORY", "./temp")

# File patterns
CONTENT_FILE_PATTERNS = ["*.txt", "*.md"]
IMAGE_FILE_PATTERNS = ["*.jpg", "*.jpeg", "*.png", "*.gif"]
METADATA_FILE_NAME = "metadata.yaml"

# Processing settings
MAX_SUMMARY_LENGTH = 280  # Characters
MAX_HASHTAGS = 5
DEFAULT_LANGUAGE = "en"

# Image processing
DEFAULT_IMAGE_SIZE = {
    "twitter": (1200, 675),
    "facebook": (1200, 630),
    "instagram": (1080, 1080),
    "linkedin": (1200, 627)
}
IMAGE_QUALITY = 85  # JPEG quality (0-100)
GENERATE_ALT_TEXT = True

# AI services
USE_AI_CAPTION = True
AI_PROVIDER = "openai"  # Options: "openai", "huggingface", "none"
OPENAI_MODEL = "gpt-4"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HUGGINGFACE_MODEL = "gpt2"

# Scheduling
DEFAULT_TIMEZONE = "America/Edmonton"
OPTIMAL_POSTING_TIMES = {
    "twitter": ["9:00", "12:00", "15:00", "18:00"],
    "facebook": ["9:00", "13:00", "15:00"],
    "instagram": ["11:00", "13:00", "19:00"],
    "linkedin": ["8:00", "10:00", "17:00"]
}
SCHEDULE_CHECK_INTERVAL = 60  # Seconds

# Publishing
USE_AYRSHARE = True  # If False, use individual platform SDKs
MAX_RETRIES = 3
RETRY_DELAY = 5  # Seconds

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "pipeline.log"
CONSOLE_LOG = True

# Advanced
WATCHDOG_RECURSIVE = False
OBSERVER_TIMEOUT = 1.0  # Seconds
PROCESS_IMMEDIATELY = True  # Process files as soon as they are detected

# Platform-specific configurations
# Ayrshare configuration (multi-platform API)
AYRSHARE_CONFIG = {
    "api_key": os.environ.get("AYRSHARE_API_KEY", ""),
    "enabled_platforms": ["twitter", "facebook", "instagram", "linkedin"],
    "shorten_links": True,
}

# Twitter configuration
TWITTER_CONFIG = {
    "enabled": True,
    "consumer_key": os.environ.get("TWITTER_CONSUMER_KEY", ""),
    "consumer_secret": os.environ.get("TWITTER_CONSUMER_SECRET", ""),
    "access_token": os.environ.get("TWITTER_ACCESS_TOKEN", ""),
    "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
    "character_limit": 280,
    "max_images": 4,
    "max_video_size_mb": 512,
    "max_gif_size_mb": 15,
}

# Facebook configuration
FACEBOOK_CONFIG = {
    "enabled": True,
    "app_id": os.environ.get("FACEBOOK_APP_ID", ""),
    "app_secret": os.environ.get("FACEBOOK_APP_SECRET", ""),
    "access_token": os.environ.get("FACEBOOK_ACCESS_TOKEN", ""),
    "page_id": os.environ.get("FACEBOOK_PAGE_ID", ""),
    "character_limit": 63206,  # Facebook's actual limit is much higher
    "max_images": 10,
}

# Instagram configuration
INSTAGRAM_CONFIG = {
    "enabled": True,
    "username": os.environ.get("INSTAGRAM_USERNAME", ""),
    "password": os.environ.get("INSTAGRAM_PASSWORD", ""),
    "character_limit": 2200,
    "max_hashtags": 30,
    "max_images": 10,  # For carousel posts
}

# LinkedIn configuration
LINKEDIN_CONFIG = {
    "enabled": True,
    "client_id": os.environ.get("LINKEDIN_CLIENT_ID", ""),
    "client_secret": os.environ.get("LINKEDIN_CLIENT_SECRET", ""),
    "access_token": os.environ.get("LINKEDIN_ACCESS_TOKEN", ""),
    "character_limit": 3000,
    "max_images": 9,
}

# Aggregate all platform configurations
PLATFORM_CONFIGS = {
    "ayrshare": AYRSHARE_CONFIG,
    "twitter": TWITTER_CONFIG,
    "facebook": FACEBOOK_CONFIG,
    "instagram": INSTAGRAM_CONFIG,
    "linkedin": LINKEDIN_CONFIG,
}

