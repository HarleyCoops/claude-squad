"""
Platform-specific configurations and credentials.

IMPORTANT: Keep this file secure and never commit it to version control with real credentials.
Use environment variables or a secure vault for production deployments.
"""
import os

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

