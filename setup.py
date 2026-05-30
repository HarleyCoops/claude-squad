"""
Setup script for the social media posting pipeline.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="social-media-pipeline",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An end-to-end automated pipeline for social media content management and publishing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/social-media-pipeline",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "watchdog>=3.0.0",
        "pillow>=10.1.0",
        "pyyaml>=6.0.1",
        "schedule>=1.2.1",
        "python-dateutil>=2.8.2",
        "pytz>=2023.3.post1",
        "requests>=2.31.0",
        "apscheduler>=3.10.4",
        "tweepy>=4.14.0",
        "facebook-sdk>=3.1.0",
        "instabot>=0.117.0",
        "linkedin-api>=2.0.0a5",
        "social-post-api>=1.0.15",
        "spacy>=3.7.2",
        "rake-nltk>=1.0.6",
        "transformers>=4.35.2",
        "torch>=2.1.1",
        "opencv-python>=4.8.1.78",
    ],
    entry_points={
        "console_scripts": [
            "social-media-pipeline=social_media_pipeline.main:main",
        ],
    },
)

