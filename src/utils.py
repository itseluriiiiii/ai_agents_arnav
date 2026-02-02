"""
Utility functions for AI Email Agent.

This module provides common utility functions used across the application.
"""

import re
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_name_from_email(email: str) -> str:
    """Extract name from email address."""
    if '@' not in email:
        return email
    
    local_part = email.split('@')[0]
    
    # Remove common separators and capitalize
    name = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    
    # Capitalize each word
    return ' '.join(word.capitalize() for word in name.split())


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def load_json_config(config_path: Path) -> Dict[str, Any]:
    """Load JSON configuration file."""
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_json_config(config: Dict[str, Any], config_path: Path):
    """Save configuration to JSON file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)
    except IOError:
        pass


def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).parent
    while current.parent != current:
        if (current / 'setup.py').exists() or (current / 'pyproject.toml').exists():
            return current
        current = current.parent
    
    # Fallback to current directory
    return Path.cwd()


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove email headers (basic)
    lines = text.split('\n')
    body_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip common header lines
        if any(header in line.lower() for header in ['from:', 'to:', 'subject:', 'date:', 'sent:']):
            continue
        if line:
            body_lines.append(line)
    
    return ' '.join(body_lines)


def extract_urls(text: str) -> list:
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def mask_sensitive_info(text: str) -> str:
    """Mask potentially sensitive information in text."""
    # Mask email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Mask phone numbers (basic)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Mask credit card numbers (basic)
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
    
    return text


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_environment_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with default value."""
    return os.getenv(key, default)


def is_valid_port(port: int) -> bool:
    """Check if port number is valid."""
    return 1 <= port <= 65535


def parse_template_variables(template_content: str) -> list:
    """Parse Jinja2 template variables from content."""
    pattern = r'\{\{\s*(\w+)\s*\}\}'
    return re.findall(pattern, template_content)


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """Merge two dictionaries, with dict2 taking precedence."""
    result = dict1.copy()
    result.update(dict2)
    return result


def safe_get_nested(data: dict, keys: list, default=None):
    """Safely get nested dictionary values."""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


class Timer:
    """Simple timer for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer."""
        import time
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """Stop the timer."""
        import time
        self.end_time = time.time()
    
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        
        import time
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()