"""
Utility functions
"""
from pathlib import Path

def ensure_dirs(*dirs: Path):
    """Ensure directories exist"""
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

