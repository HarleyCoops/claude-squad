"""
Content model representing raw input files before processing.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml
import os
from datetime import datetime


@dataclass
class ContentFile:
    """Represents a single file in the content directory."""
    path: Path
    file_type: str  # 'text', 'image', 'metadata', 'other'
    
    @property
    def name(self) -> str:
        """Return the file name."""
        return self.path.name
    
    @property
    def extension(self) -> str:
        """Return the file extension."""
        return self.path.suffix.lower()
    
    @property
    def size(self) -> int:
        """Return the file size in bytes."""
        return os.path.getsize(self.path)
    
    @property
    def modified_time(self) -> datetime:
        """Return the last modified time."""
        return datetime.fromtimestamp(os.path.getmtime(self.path))
    
    def read_text(self) -> str:
        """Read and return the file content as text."""
        if self.file_type != 'text' and self.file_type != 'metadata':
            raise ValueError(f"Cannot read {self.file_type} file as text")
        return self.path.read_text(encoding='utf-8')
    
    def read_binary(self) -> bytes:
        """Read and return the file content as binary."""
        return self.path.read_bytes()


@dataclass
class ContentMetadata:
    """Metadata for a content package."""
    schedule: Optional[Dict[str, Any]] = None
    platforms: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hashtags: List[str] = field(default_factory=list)
    alt_text: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    custom: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'ContentMetadata':
        """Create a ContentMetadata object from YAML content."""
        data = yaml.safe_load(yaml_content) or {}
        
        # Extract known fields
        schedule = data.pop('schedule', None)
        platforms = data.pop('platforms', {})
        hashtags = data.pop('hashtags', [])
        alt_text = data.pop('alt_text', None)
        title = data.pop('title', None)
        description = data.pop('description', None)
        author = data.pop('author', None)
        
        # Parse created_at if it exists
        created_at_str = data.pop('created_at', None)
        created_at = None
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
            except ValueError:
                # If parsing fails, leave as None
                pass
        
        # Any remaining fields go into custom
        custom = data
        
        return cls(
            schedule=schedule,
            platforms=platforms,
            hashtags=hashtags,
            alt_text=alt_text,
            title=title,
            description=description,
            author=author,
            created_at=created_at,
            custom=custom
        )
    
    def to_yaml(self) -> str:
        """Convert the metadata to YAML format."""
        data = {
            'schedule': self.schedule,
            'platforms': self.platforms,
            'hashtags': self.hashtags,
            'alt_text': self.alt_text,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'custom': self.custom
        }
        
        # Add created_at if it exists
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        return yaml.dump(data, default_flow_style=False)


@dataclass
class ContentPackage:
    """A package of content files representing a single post."""
    directory: Path
    text_files: List[ContentFile] = field(default_factory=list)
    image_files: List[ContentFile] = field(default_factory=list)
    metadata_file: Optional[ContentFile] = None
    other_files: List[ContentFile] = field(default_factory=list)
    metadata: ContentMetadata = field(default_factory=ContentMetadata)
    
    @property
    def id(self) -> str:
        """Generate a unique ID for this content package."""
        return self.directory.name
    
    @property
    def has_text(self) -> bool:
        """Check if the package has any text files."""
        return len(self.text_files) > 0
    
    @property
    def has_images(self) -> bool:
        """Check if the package has any image files."""
        return len(self.image_files) > 0
    
    @property
    def has_metadata(self) -> bool:
        """Check if the package has a metadata file."""
        return self.metadata_file is not None
    
    @property
    def primary_text_file(self) -> Optional[ContentFile]:
        """Return the primary text file (first one)."""
        return self.text_files[0] if self.has_text else None
    
    @property
    def primary_text_content(self) -> Optional[str]:
        """Return the content of the primary text file."""
        if not self.has_text:
            return None
        return self.primary_text_file.read_text()
    
    def load_metadata(self) -> None:
        """Load metadata from the metadata file if it exists."""
        if self.metadata_file:
            yaml_content = self.metadata_file.read_text()
            self.metadata = ContentMetadata.from_yaml(yaml_content)
    
    @classmethod
    def from_directory(cls, directory: Path) -> 'ContentPackage':
        """Create a ContentPackage from a directory."""
        if not directory.is_dir():
            raise ValueError(f"{directory} is not a directory")
        
        package = cls(directory=directory)
        
        # Categorize files
        for file_path in directory.iterdir():
            if file_path.is_file():
                # Determine file type
                extension = file_path.suffix.lower()
                
                if extension in ['.txt', '.md']:
                    file_type = 'text'
                    content_file = ContentFile(path=file_path, file_type=file_type)
                    package.text_files.append(content_file)
                elif extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    file_type = 'image'
                    content_file = ContentFile(path=file_path, file_type=file_type)
                    package.image_files.append(content_file)
                elif file_path.name.lower() == 'metadata.yaml' or file_path.name.lower() == 'metadata.yml':
                    file_type = 'metadata'
                    content_file = ContentFile(path=file_path, file_type=file_type)
                    package.metadata_file = content_file
                else:
                    file_type = 'other'
                    content_file = ContentFile(path=file_path, file_type=file_type)
                    package.other_files.append(content_file)
        
        # Load metadata if available
        if package.metadata_file:
            package.load_metadata()
        
        return package

