#!/bin/bash
# Script to set up environment variables for the social media pipeline

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    touch .env
    echo "Created .env file"
fi

# Function to prompt for a variable and add it to .env
add_env_var() {
    VAR_NAME=$1
    VAR_DESC=$2
    
    # Check if variable already exists in .env
    if grep -q "^${VAR_NAME}=" .env; then
        echo "${VAR_NAME} already set in .env"
    else
        # Prompt for the value
        echo "${VAR_DESC} (${VAR_NAME}):"
        read -r VAR_VALUE
        
        # Add to .env
        echo "${VAR_NAME}=${VAR_VALUE}" >> .env
        echo "Added ${VAR_NAME} to .env"
    fi
}

# Create directories
mkdir -p data/content_inbox data/content_processed data/content_failed data/temp
echo "Created data directories"

# Copy example settings if needed
if [ ! -f social_media_pipeline/config/settings.py ]; then
    cp social_media_pipeline/config/settings.example.py social_media_pipeline/config/settings.py
    echo "Copied example settings to settings.py"
fi

# Prompt for environment variables
echo "Setting up environment variables..."
echo "Leave blank to skip"

# OpenAI
add_env_var "OPENAI_API_KEY" "OpenAI API Key"

# Ayrshare
add_env_var "AYRSHARE_API_KEY" "Ayrshare API Key"

# Twitter
add_env_var "TWITTER_CONSUMER_KEY" "Twitter Consumer Key"
add_env_var "TWITTER_CONSUMER_SECRET" "Twitter Consumer Secret"
add_env_var "TWITTER_ACCESS_TOKEN" "Twitter Access Token"
add_env_var "TWITTER_ACCESS_TOKEN_SECRET" "Twitter Access Token Secret"

# Facebook
add_env_var "FACEBOOK_APP_ID" "Facebook App ID"
add_env_var "FACEBOOK_APP_SECRET" "Facebook App Secret"
add_env_var "FACEBOOK_ACCESS_TOKEN" "Facebook Access Token"
add_env_var "FACEBOOK_PAGE_ID" "Facebook Page ID"

# Instagram
add_env_var "INSTAGRAM_USERNAME" "Instagram Username"
add_env_var "INSTAGRAM_PASSWORD" "Instagram Password"

# LinkedIn
add_env_var "LINKEDIN_CLIENT_ID" "LinkedIn Client ID"
add_env_var "LINKEDIN_CLIENT_SECRET" "LinkedIn Client Secret"
add_env_var "LINKEDIN_ACCESS_TOKEN" "LinkedIn Access Token"

echo "Environment setup complete!"
echo "You can now run the pipeline with:"
echo "  docker-compose up -d"
echo "Or for development:"
echo "  python -m social_media_pipeline.main"

