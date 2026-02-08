"""
Script to get all files in the client project, excluding library files.
This script walks through the client project directory and returns all files
excluding those in .pio/libdeps and other library directories.
"""

import os
from pathlib import Path


def get_client_files(project_dir, file_extensions=None, skip_exclusions=False):
    """
    Get all files in the client project, excluding library directories.
    Optionally filter files by their extensions.
    
    Args:
        project_dir: Path to the client project root (where platformio.ini is)
        file_extensions: Optional list of file extensions to filter by (e.g., ['.h', '.cpp'] or ['h', 'cpp']).
                        If None or empty, returns all files. Extensions are case-insensitive.
        skip_exclusions: If True, skip directory exclusion logic (useful for scanning library directories)
    
    Returns:
        List of full absolute file paths
    """
    project_path = Path(project_dir).resolve()
    client_files = []
    
    # Normalize file extensions: ensure they start with '.' and are lowercase
    normalized_extensions = None
    if file_extensions:
        normalized_extensions = []
        for ext in file_extensions:
            ext_str = str(ext).lower()
            if not ext_str.startswith('.'):
                ext_str = '.' + ext_str
            normalized_extensions.append(ext_str)
    
    # Directories to exclude (PlatformIO library and build directories)
    exclude_dirs = {
        '.pio',           # PlatformIO build and library directory
        '.git',           # Git directory
        'build',          # Build directory
        '.vscode',        # VS Code settings (optional, but common)
        '.idea',          # IDE settings
    }
    
    # Walk through the project directory
    for root, dirs, files in os.walk(project_path):
        # Convert to Path for easier manipulation
        root_path = Path(root)
        
        # Skip exclusion logic if skip_exclusions is True
        if not skip_exclusions:
            # Skip if this directory or any parent is in exclude_dirs
            should_skip = False
            for part in root_path.parts:
                if part in exclude_dirs:
                    should_skip = True
                    break
            
            if should_skip:
                # Remove excluded directories from dirs list to prevent walking into them
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                continue
        
        # Add files in this directory (with optional extension filtering)
        for file in files:
            file_path = root_path / file
            
            # Filter by extension if extensions are provided
            if normalized_extensions:
                file_ext = file_path.suffix.lower()
                if file_ext not in normalized_extensions:
                    continue
            
            # Get full absolute path
            try:
                full_path = file_path.resolve()
                client_files.append(str(full_path))
            except (ValueError, OSError):
                # Skip if path cannot be resolved
                continue
    
    return sorted(client_files)


if __name__ == "__main__":
    # This can be called standalone for testing
    import sys
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        # Default to current directory
        project_dir = os.getcwd()
    
    files = get_client_files(project_dir)
    for f in files:
        # print(f)
        # print(f)
        pass
