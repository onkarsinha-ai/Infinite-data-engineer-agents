"""Helper utilities for dmapagent."""
import os
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import hashlib


def is_file_exists(file_path: str) -> bool:
    """Check if file exists."""
    return os.path.isfile(file_path)


def is_directory_exists(dir_path: str) -> bool:
    """Check if directory exists."""
    return os.path.isdir(dir_path)


def get_file_extension(file_path: str) -> str:
    """Get file extension."""
    _, ext = os.path.splitext(file_path)
    return ext.lower()


def generate_id(prefix: str = "") -> str:
    """Generate unique ID."""
    timestamp = datetime.now().isoformat()
    hash_obj = hashlib.md5(timestamp.encode())
    unique_hash = hash_obj.hexdigest()[:8]
    return f"{prefix}_{unique_hash}" if prefix else unique_hash


def normalize_type_name(type_name: str) -> str:
    """Normalize SQL type name."""
    return type_name.lower().strip()


def safe_json_dumps(obj: Any, default="null") -> str:
    """Safely dump object to JSON string."""
    try:
        return json.dumps(obj, default=str, indent=2)
    except Exception as e:
        return f'{{"error": "JSON serialization failed: {str(e)}"}}'


def truncate_string(text: str, max_length: int = 100) -> str:
    """Truncate string to max length."""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def deduplicate_list(items: List[Any]) -> List[Any]:
    """Remove duplicates from list while preserving order."""
    seen = set()
    result = []
    for item in items:
        item_str = str(item)
        if item_str not in seen:
            seen.add(item_str)
            result.append(item)
    return result
