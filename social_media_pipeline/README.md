# Social Media Posting Pipeline

An end-to-end automated pipeline for social media content management and publishing.

## Overview

This system automatically monitors a directory for new content (text and images), processes them into polished social media posts, and publishes them to multiple platforms. The pipeline handles different platform requirements, scheduling, and error handling.

## Features

- **Directory Monitoring**: Watches a folder for new content using the watchdog library
- **Content Processing**: 
  - Text summarization and hashtag generation
  - Image resizing and alt-text generation
  - AI-powered caption enhancement
- **Multi-Platform Support**:
  - Twitter
  - Facebook
  - Instagram
  - LinkedIn
  - (More platforms via Ayrshare integration)
- **Scheduling**: Post at optimal times with timezone support
- **Error Handling**: Robust error handling with retries and logging

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/social-media-pipeline.git
cd social-media-pipeline

# Install dependencies
pip install -r requirements.txt

# Install language model for text processing (optional)
python -m spacy download en_core_web_sm
```

## Configuration

1. Copy `config/settings.example.py` to `config/settings.py`
2. Update the settings with your directory paths and preferences
3. Copy `config/platform_configs.example.py` to `config/platform_configs.py`
4. Add your social media platform credentials

## Usage

```bash
# Start the pipeline
python main.py

# Start with a specific config file
python main.py --config path/to/config.yaml
```

## Content Structure

The pipeline expects content to be organized in the following way:

```
watch_directory/
├── post_20231201_1/
│   ├── content.txt
│   ├── image1.jpg
│   ├── image2.jpg
│   └── metadata.yaml (optional)
├── post_20231201_2/
│   ├── content.txt
│   └── image1.png
```

Each subfolder represents a single post. The `content.txt` file contains the text for the post, and any image files will be included in the post. An optional `metadata.yaml` file can be included to specify platform-specific settings or scheduling information.

## Advanced Usage

### Scheduling

To schedule a post, include a `schedule` section in the metadata.yaml file:

```yaml
schedule:
  time: "2023-12-01T15:30:00"
  timezone: "America/Edmonton"
  platforms: ["twitter", "facebook"]
```

### Platform-Specific Content

To customize content for specific platforms, use the `platforms` section in metadata.yaml:

```yaml
platforms:
  twitter:
    text: "Twitter-specific text #twitter"
  instagram:
    text: "Instagram-specific text"
    hashtags: ["instagram", "photo"]
```

## Architecture

The pipeline follows a modular architecture with the following components:

- **Monitor**: Watches for new content
- **Processor**: Processes text and images
- **Composer**: Creates platform-specific posts
- **Publisher**: Publishes posts to platforms
- **Scheduler**: Manages scheduled posts

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

