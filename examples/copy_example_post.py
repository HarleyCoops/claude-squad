#!/usr/bin/env python
"""
Script to copy the example post to the watch directory.
"""
import os
import sys
import shutil
from pathlib import Path
import time

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from social_media_pipeline.config import settings

def main():
    """Copy the example post to the watch directory."""
    # Get the source and destination directories
    source_dir = Path(__file__).parent / "post_example"
    dest_dir = Path(settings.WATCH_DIRECTORY) / f"post_{int(time.time())}"
    
    # Create the destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from the example directory
    for file_path in source_dir.iterdir():
        if file_path.is_file():
            shutil.copy2(file_path, dest_dir / file_path.name)
    
    print(f"Copied example post to {dest_dir}")
    print("The pipeline should detect and process this post shortly.")

if __name__ == "__main__":
    main()

