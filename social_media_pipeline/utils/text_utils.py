"""
Text processing utilities for the social media pipeline.
"""
import logging
import re
from typing import List, Optional, Tuple, Dict, Any
import spacy
from rake_nltk import Rake
from transformers import pipeline
import openai

from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)

# Initialize NLP components
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model not found. Using en_core_web_sm as a blank model.")
    nlp = spacy.blank("en")

# Initialize RAKE for keyword extraction
rake = Rake()

# Initialize summarizer if transformers is available
summarizer = None
if settings.AI_PROVIDER == "huggingface":
    try:
        summarizer = pipeline("summarization", model=settings.HUGGINGFACE_MODEL)
        logger.info(f"Initialized HuggingFace summarizer with model: {settings.HUGGINGFACE_MODEL}")
    except Exception as e:
        logger.error(f"Failed to initialize HuggingFace summarizer: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace, normalizing line breaks, etc.
    
    Args:
        text: The text to clean
        
    Returns:
        str: The cleaned text
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def detect_language(text: str) -> str:
    """
    Detect the language of the text.
    
    Args:
        text: The text to analyze
        
    Returns:
        str: The detected language code (e.g., 'en', 'es', 'fr')
    """
    # This is a simple implementation that only checks for English
    # For production, consider using a proper language detection library
    # like langdetect or spacy's language detection
    
    # For now, just return the default language
    return settings.DEFAULT_LANGUAGE


def summarize_text(text: str, max_length: int = None) -> str:
    """
    Summarize text to a shorter version.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        str: The summarized text
    """
    if max_length is None:
        max_length = settings.MAX_SUMMARY_LENGTH
    
    # If text is already shorter than max_length, return it as is
    if len(text) <= max_length:
        return text
    
    # Use different summarization methods based on configuration
    if settings.AI_PROVIDER == "openai" and settings.USE_AI_CAPTION:
        return summarize_with_openai(text, max_length)
    elif settings.AI_PROVIDER == "huggingface" and summarizer and settings.USE_AI_CAPTION:
        return summarize_with_huggingface(text, max_length)
    else:
        return simple_summarize(text, max_length)


def simple_summarize(text: str, max_length: int) -> str:
    """
    Simple text summarization by truncation and sentence extraction.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        str: The summarized text
    """
    # Parse the text with spaCy
    doc = nlp(text)
    
    # Extract sentences
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # If there's only one sentence, truncate it
    if len(sentences) <= 1:
        return text[:max_length].rsplit(' ', 1)[0] + '...'
    
    # Otherwise, take sentences until we reach the max length
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) + 1 <= max_length:
            summary += sentence + " "
        else:
            break
    
    return summary.strip()


def summarize_with_huggingface(text: str, max_length: int) -> str:
    """
    Summarize text using HuggingFace transformers.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        str: The summarized text
    """
    if not summarizer:
        logger.warning("HuggingFace summarizer not initialized. Falling back to simple summarization.")
        return simple_summarize(text, max_length)
    
    try:
        # Convert character limit to token limit (rough approximation)
        max_tokens = max(1, max_length // 4)
        
        # Generate summary
        summary = summarizer(text, max_length=max_tokens, min_length=10, do_sample=False)
        
        # Extract the summary text
        summary_text = summary[0]['summary_text']
        
        # Ensure it's within the character limit
        if len(summary_text) > max_length:
            summary_text = summary_text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return summary_text
    
    except Exception as e:
        logger.error(f"Error in HuggingFace summarization: {str(e)}")
        return simple_summarize(text, max_length)


def summarize_with_openai(text: str, max_length: int) -> str:
    """
    Summarize text using OpenAI's API.
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        str: The summarized text
    """
    try:
        # Check if OpenAI API key is configured
        if not openai.api_key:
            openai.api_key = settings.OPENAI_API_KEY
        
        if not openai.api_key:
            logger.warning("OpenAI API key not configured. Falling back to simple summarization.")
            return simple_summarize(text, max_length)
        
        # Create the prompt
        prompt = f"Summarize the following text in a concise, engaging way suitable for a social media post. Keep it under {max_length} characters:\n\n{text}"
        
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text for social media."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_length // 2,  # Rough approximation
            temperature=0.7
        )
        
        # Extract the summary
        summary = response.choices[0].message.content.strip()
        
        # Ensure it's within the character limit
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
        
        return summary
    
    except Exception as e:
        logger.error(f"Error in OpenAI summarization: {str(e)}")
        return simple_summarize(text, max_length)


def extract_hashtags(text: str, max_hashtags: int = None) -> List[str]:
    """
    Extract relevant hashtags from text.
    
    Args:
        text: The text to analyze
        max_hashtags: Maximum number of hashtags to extract
        
    Returns:
        List[str]: List of hashtags (without the # symbol)
    """
    if max_hashtags is None:
        max_hashtags = settings.MAX_HASHTAGS
    
    # Extract existing hashtags from the text
    existing_hashtags = re.findall(r'#(\w+)', text)
    
    # If we already have enough hashtags, return them
    if len(existing_hashtags) >= max_hashtags:
        return existing_hashtags[:max_hashtags]
    
    # Use RAKE to extract keywords
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()
    
    # Convert keywords to hashtags (single words, no spaces)
    extracted_hashtags = []
    for keyword in keywords:
        # Split multi-word keywords and take each word
        words = keyword.split()
        for word in words:
            # Clean the word (remove non-alphanumeric characters)
            clean_word = re.sub(r'[^\w]', '', word).lower()
            if clean_word and len(clean_word) > 2:  # Only keep words with 3+ characters
                extracted_hashtags.append(clean_word)
    
    # Combine existing and extracted hashtags, remove duplicates
    all_hashtags = []
    for tag in existing_hashtags + extracted_hashtags:
        if tag.lower() not in [t.lower() for t in all_hashtags]:
            all_hashtags.append(tag)
    
    # Limit to max_hashtags
    return all_hashtags[:max_hashtags]


def generate_alt_text(image_path: str, existing_alt_text: Optional[str] = None) -> str:
    """
    Generate alt text for an image.
    
    Args:
        image_path: Path to the image
        existing_alt_text: Existing alt text to use if available
        
    Returns:
        str: Generated alt text
    """
    # If existing alt text is provided, use it
    if existing_alt_text:
        return existing_alt_text
    
    # For now, return a simple placeholder
    # In a production system, this would use a vision model or API
    return "Image from social media post"


def enhance_caption(text: str, platform: str) -> str:
    """
    Enhance a caption for a specific platform using AI.
    
    Args:
        text: The original caption
        platform: The target platform
        
    Returns:
        str: The enhanced caption
    """
    if not settings.USE_AI_CAPTION:
        return text
    
    if settings.AI_PROVIDER == "openai":
        return enhance_caption_with_openai(text, platform)
    else:
        return text


def enhance_caption_with_openai(text: str, platform: str) -> str:
    """
    Enhance a caption using OpenAI's API.
    
    Args:
        text: The original caption
        platform: The target platform
        
    Returns:
        str: The enhanced caption
    """
    try:
        # Check if OpenAI API key is configured
        if not openai.api_key:
            openai.api_key = settings.OPENAI_API_KEY
        
        if not openai.api_key:
            logger.warning("OpenAI API key not configured. Returning original caption.")
            return text
        
        # Get platform-specific character limit
        platform_config = settings.PLATFORM_CONFIGS.get(platform.lower(), {})
        character_limit = platform_config.get('character_limit', 280)
        
        # Create the prompt
        prompt = f"""
        Enhance this caption for {platform}. Make it engaging and appropriate for the platform.
        Keep it under {character_limit} characters:
        
        {text}
        """
        
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"You are a social media expert for {platform}."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=character_limit // 2,  # Rough approximation
            temperature=0.7
        )
        
        # Extract the enhanced caption
        enhanced_caption = response.choices[0].message.content.strip()
        
        # Ensure it's within the character limit
        if len(enhanced_caption) > character_limit:
            enhanced_caption = enhanced_caption[:character_limit].rsplit(' ', 1)[0] + '...'
        
        return enhanced_caption
    
    except Exception as e:
        logger.error(f"Error in OpenAI caption enhancement: {str(e)}")
        return text


def truncate_text_for_platform(text: str, platform: str, hashtags: List[str] = None) -> Tuple[str, List[str]]:
    """
    Truncate text to fit within a platform's character limit.
    
    Args:
        text: The text to truncate
        platform: The target platform
        hashtags: Optional list of hashtags
        
    Returns:
        Tuple[str, List[str]]: Truncated text and adjusted hashtags
    """
    # Get platform-specific character limit
    platform_config = settings.PLATFORM_CONFIGS.get(platform.lower(), {})
    character_limit = platform_config.get('character_limit', 280)
    
    # If no hashtags, just truncate the text
    if not hashtags:
        if len(text) <= character_limit:
            return text, []
        return text[:character_limit-3].rsplit(' ', 1)[0] + '...', []
    
    # Calculate hashtag text length
    hashtag_text = ' '.join([f"#{tag}" for tag in hashtags])
    hashtag_length = len(hashtag_text) + 2  # +2 for newlines
    
    # If text + hashtags fit within limit, return as is
    if len(text) + hashtag_length <= character_limit:
        return text, hashtags
    
    # If just the text is too long, truncate it
    if len(text) > character_limit - hashtag_length:
        truncated_text = text[:character_limit - hashtag_length - 3].rsplit(' ', 1)[0] + '...'
        return truncated_text, hashtags
    
    # If we need to reduce hashtags
    available_length = character_limit - len(text) - 2  # -2 for newlines
    
    # Keep removing hashtags until we fit
    adjusted_hashtags = hashtags.copy()
    while adjusted_hashtags and len(' '.join([f"#{tag}" for tag in adjusted_hashtags])) > available_length:
        adjusted_hashtags.pop()
    
    return text, adjusted_hashtags

