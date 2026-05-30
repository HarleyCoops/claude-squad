"""
Directory monitoring component using watchdog.
"""
import time
import logging
from pathlib import Path
from typing import Callable, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from ..models.content import ContentPackage
from ..config import settings

# Configure logger
logger = logging.getLogger(__name__)


class ContentMonitorHandler(FileSystemEventHandler):
    """
    Handler for file system events in the watched directory.
    """
    def __init__(self, callback: Callable[[ContentPackage], None], 
                 content_ready_callback: Optional[Callable[[Path], bool]] = None):
        """
        Initialize the handler.
        
        Args:
            callback: Function to call when a new content package is detected
            content_ready_callback: Optional function to check if a content package is ready for processing
        """
        self.callback = callback
        self.content_ready_callback = content_ready_callback
        self.processing_directories = set()
        self.pending_directories = {}  # Directory -> last_modified_time
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            logger.info(f"New directory detected: {event.src_path}")
            # Add to pending directories
            self.pending_directories[event.src_path] = time.time()
            return
        
        # Get the parent directory of the file
        file_path = Path(event.src_path)
        directory = str(file_path.parent)
        
        # Update the last modified time for this directory
        self.pending_directories[directory] = time.time()
        
        # Check if we should process this directory now
        self._check_pending_directories()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Get the parent directory of the file
        file_path = Path(event.src_path)
        directory = str(file_path.parent)
        
        # Update the last modified time for this directory
        if directory in self.pending_directories:
            self.pending_directories[directory] = time.time()
    
    def _check_pending_directories(self):
        """Check if any pending directories are ready for processing."""
        current_time = time.time()
        directories_to_process = []
        
        for directory, last_modified in list(self.pending_directories.items()):
            # Skip directories that are already being processed
            if directory in self.processing_directories:
                continue
            
            # Check if enough time has passed since the last modification
            if current_time - last_modified > settings.OBSERVER_TIMEOUT:
                # Check if the directory is ready for processing
                if self.content_ready_callback:
                    if self.content_ready_callback(Path(directory)):
                        directories_to_process.append(directory)
                        del self.pending_directories[directory]
                else:
                    directories_to_process.append(directory)
                    del self.pending_directories[directory]
        
        # Process ready directories
        for directory in directories_to_process:
            self._process_directory(directory)
    
    def _process_directory(self, directory_path: str):
        """Process a directory that's ready."""
        try:
            # Mark as processing to avoid duplicate processing
            self.processing_directories.add(directory_path)
            
            # Create a ContentPackage from the directory
            directory = Path(directory_path)
            content_package = ContentPackage.from_directory(directory)
            
            # Call the callback with the content package
            logger.info(f"Processing content package: {content_package.id}")
            self.callback(content_package)
            
        except Exception as e:
            logger.error(f"Error processing directory {directory_path}: {str(e)}")
        finally:
            # Remove from processing set
            self.processing_directories.remove(directory_path)


class ContentMonitor:
    """
    Monitors a directory for new content packages.
    """
    def __init__(self, watch_directory: Path, 
                 callback: Callable[[ContentPackage], None],
                 content_ready_callback: Optional[Callable[[Path], bool]] = None,
                 recursive: bool = False):
        """
        Initialize the monitor.
        
        Args:
            watch_directory: Directory to watch for new content
            callback: Function to call when a new content package is detected
            content_ready_callback: Optional function to check if a content package is ready for processing
            recursive: Whether to watch subdirectories recursively
        """
        self.watch_directory = watch_directory
        self.callback = callback
        self.content_ready_callback = content_ready_callback
        self.recursive = recursive
        self.observer = None
        
        # Create the watch directory if it doesn't exist
        self.watch_directory.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start monitoring the directory."""
        logger.info(f"Starting to monitor directory: {self.watch_directory}")
        
        # Create the event handler
        event_handler = ContentMonitorHandler(
            self.callback, 
            self.content_ready_callback
        )
        
        # Create and start the observer
        self.observer = Observer()
        self.observer.schedule(
            event_handler, 
            str(self.watch_directory), 
            recursive=self.recursive
        )
        self.observer.start()
        
        # Process any existing content in the directory
        self._process_existing_content()
        
        logger.info("Directory monitor started successfully")
    
    def stop(self):
        """Stop monitoring the directory."""
        if self.observer:
            logger.info("Stopping directory monitor")
            self.observer.stop()
            self.observer.join()
            logger.info("Directory monitor stopped")
    
    def _process_existing_content(self):
        """Process any existing content in the watch directory."""
        logger.info("Checking for existing content in watch directory")
        
        # Get all subdirectories in the watch directory
        subdirectories = [d for d in self.watch_directory.iterdir() if d.is_dir()]
        
        for directory in subdirectories:
            try:
                # Check if the directory is ready for processing
                if self.content_ready_callback and not self.content_ready_callback(directory):
                    logger.info(f"Directory not ready for processing: {directory}")
                    continue
                
                # Create a ContentPackage from the directory
                content_package = ContentPackage.from_directory(directory)
                
                # Call the callback with the content package
                logger.info(f"Processing existing content package: {content_package.id}")
                self.callback(content_package)
                
            except Exception as e:
                logger.error(f"Error processing existing directory {directory}: {str(e)}")


def is_content_package_ready(directory: Path) -> bool:
    """
    Check if a content package is ready for processing.
    
    A package is considered ready if:
    1. It contains at least one text file or one image file
    2. No files in the directory have been modified in the last few seconds
    
    Args:
        directory: Directory to check
        
    Returns:
        bool: True if the package is ready, False otherwise
    """
    # Check if the directory exists
    if not directory.exists() or not directory.is_dir():
        return False
    
    # Check if the directory contains any files
    files = list(directory.iterdir())
    if not files:
        return False
    
    # Check if the directory contains at least one text file or one image file
    has_text_file = any(f.is_file() and f.suffix.lower() in ['.txt', '.md'] for f in files)
    has_image_file = any(f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif'] for f in files)
    
    if not (has_text_file or has_image_file):
        return False
    
    # Check if any files have been modified recently
    current_time = time.time()
    for file_path in files:
        if file_path.is_file():
            modified_time = file_path.stat().st_mtime
            if current_time - modified_time < settings.OBSERVER_TIMEOUT:
                return False
    
    return True


def start_monitoring(callback: Callable[[ContentPackage], None]) -> ContentMonitor:
    """
    Start monitoring the watch directory for new content.
    
    Args:
        callback: Function to call when a new content package is detected
        
    Returns:
        ContentMonitor: The monitor instance
    """
    watch_directory = Path(settings.WATCH_DIRECTORY)
    
    monitor = ContentMonitor(
        watch_directory=watch_directory,
        callback=callback,
        content_ready_callback=is_content_package_ready,
        recursive=settings.WATCHDOG_RECURSIVE
    )
    
    monitor.start()
    return monitor

