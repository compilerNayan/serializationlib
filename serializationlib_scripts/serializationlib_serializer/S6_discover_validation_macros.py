#!/usr/bin/env python3
"""
S6 Discover Validation Macros Script

This script discovers validation macros by scanning for the pattern:
#define MacroName /* Validation Function -> FunctionName */

Returns a dictionary mapping macro names to their validation function names.
"""

import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# print("Executing NayanSerializer/scripts/serializer/S6_discover_validation_macros.py")
# print("Executing NayanSerializer/scripts/serializer/S6_discover_validation_macros.py")
# Import get_client_files from serializationlib_core
# First, find the serializationlib_scripts directory to add to path
try:
    script_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(script_file)
    # current_dir is serializationlib_serializer/, so parent is serializationlib_scripts/
    serializationlib_scripts_dir = os.path.dirname(current_dir)
except NameError:
    # __file__ not available, try to find from globals or search
    serializationlib_scripts_dir = None
    if 'library_scripts_dir' in globals():
        serializationlib_scripts_dir = str(globals()['library_scripts_dir'])
    elif 'library_dir' in globals():
        # library_dir is parent of serializationlib_scripts
        potential = os.path.join(str(globals()['library_dir']), 'serializationlib_scripts')
        if os.path.exists(potential):
            serializationlib_scripts_dir = potential
    else:
        # Search from current directory
        search_dir = os.getcwd()
        for _ in range(5):  # Search up to 5 levels
            potential = os.path.join(search_dir, 'serializationlib_scripts')
            if os.path.exists(potential) and os.path.isdir(potential):
                serializationlib_scripts_dir = potential
                break
            parent = os.path.dirname(search_dir)
            if parent == search_dir:  # Reached root
                break
            search_dir = parent

# Add to path and import
get_client_files = None
if serializationlib_scripts_dir and os.path.exists(serializationlib_scripts_dir):
    core_dir = os.path.join(serializationlib_scripts_dir, 'serializationlib_core')
    if os.path.exists(core_dir):
        sys.path.insert(0, core_dir)
        try:
            from serializationlib_get_client_files import get_client_files
        except ImportError as e:
            # print(f"Warning: Could not import get_client_files: {e}")
            # print(f"Warning: Could not import get_client_files: {e}")
            pass
        # print(f"Warning: Could not find serializationlib_core directory at {core_dir}")
        # print(f"Warning: Could not find serializationlib_core directory at {core_dir}")
    # print(f"Warning: Could not find serializationlib_scripts directory")
    # print(f"Warning: Could not find serializationlib_scripts directory")
def find_validation_macro_definitions(search_directories: List[str] = None) -> Dict[str, str]:
    """
    Discover all validation macros by scanning files for the pattern:
    #define MacroName /* Validation Function -> FunctionName */
    
    Supports both namespaced and non-namespaced function names:
    - #define NotNull /* Validation Function -> DtoValidationUtility::ValidateNotNull */
    - #define NotNull /* Validation Function -> nayan::validation::DtoValidationUtility::ValidateNotNull */
    
    Args:
        search_directories: List of directories to search (default: uses get_client_files for project_dir and library_dir)
        
    Returns:
        Dictionary mapping macro names to validation function names
        Example: {'NotNull': 'DtoValidationUtility::ValidateNotNull', 'NotEmpty': 'nayan::validation::DtoValidationUtility::ValidateNotEmpty'}
    """
    validation_macros = {}
    
    # Pattern to match: #define MacroName /* Validation Function -> FunctionName */
    # FunctionName can include namespaces (e.g., nayan::validation::DtoValidationUtility::ValidateNotNull)
    # Skip commented lines (lines starting with //)
    # Capture group 1: macro name, group 2: function name (with optional namespaces)
    pattern = r'^[^/]*#define\s+(\w+)\s+/\*\s*Validation\s+Function\s*->\s*([^\*]+?)\s*\*/'
    
    header_files = []
    
    # If search_directories is None, use get_client_files to get files from both project_dir and library_dir
    if search_directories is None:
        if get_client_files is not None:
            # Get project_dir and library_dir from environment variables (set by execute_scripts)
            # or from module globals as fallback
            project_dir = os.environ.get('PROJECT_DIR') or os.environ.get('CMAKE_PROJECT_DIR')
            library_dir = os.environ.get('LIBRARY_DIR')
            
            # Fallback to globals if environment variables not set
            if not project_dir and 'project_dir' in globals():
                project_dir = globals()['project_dir']
            if not library_dir and 'library_dir' in globals():
                library_dir = globals()['library_dir']
            
            # Get header files from project_dir (client project)
            if project_dir:
                try:
                    project_header_files = get_client_files(project_dir, file_extensions=['.h', '.hpp'])
                    header_files.extend(project_header_files)
                except Exception as e:
                    # print(f"Warning: Failed to get client files from project_dir: {e}")
                    # print(f"Warning: Failed to get client files from project_dir: {e}")
                    pass
            # Get files from library_dir (all files, not just headers, since validation macros might be in any file)
            if library_dir:
                try:
                    library_files = get_client_files(library_dir, skip_exclusions=True)
                    # Filter to only header files for consistency
                    library_header_files = [f for f in library_files if f.endswith(('.h', '.hpp'))]
                    header_files.extend(library_header_files)
                except Exception as e:
                    # print(f"Warning: Failed to get library files from library_dir: {e}")
                    # print(f"Warning: Failed to get library files from library_dir: {e}")
                    pass
            search_directories = []  # Will use file list instead
        else:
            # Fallback: Check if client_files is available in global scope
            if 'client_files' in globals():
                # Use client_files - filter to only header files
                header_files = [f for f in globals()['client_files'] if f.endswith(('.h', '.hpp'))]
                search_directories = []  # Will use file list instead
            else:
                # Fallback to default directories
                # print(f"Warning: get_client_files is None and no client_files in globals, using fallback directories")
                # print(f"Warning: get_client_files is None and no client_files in globals, using fallback directories")
                pass
    else:
        # search_directories was provided, use directory-based search
        pass
    
    # If we have header_files list, use it directly
    if header_files:
        for file_path in header_files:
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Check each line (skip commented lines)
                for line in lines:
                    # Skip lines that are commented out (single-line comments)
                    stripped = line.strip()
                    if stripped.startswith('//'):
                        continue
                    
                    # Skip lines that have // before the #define (inline comments)
                    if '//' in line:
                        comment_pos = line.find('//')
                        define_pos = line.find('#define')
                        if define_pos != -1 and comment_pos != -1 and comment_pos < define_pos:
                            continue
                    
                    # Find matches in non-commented lines
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        macro_name = match.group(1).strip()
                        function_name = match.group(2).strip()
                        validation_macros[macro_name] = function_name
                        
            except Exception as e:
                # Skip files that can't be read
                continue
    
    # Use directory-based search if search_directories is provided (fallback)
    if search_directories:
        for search_dir in search_directories:
            if not os.path.exists(search_dir):
                continue
                
            # Search for header files
            for root, dirs, files in os.walk(search_dir):
                # Skip build directories and tempcode
                if 'build' in root or 'tempcode' in root or '.git' in root:
                    continue
                    
                for file in files:
                    if file.endswith(('.h', '.hpp')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                
                            # Check each line (skip commented lines)
                            for line in lines:
                                # Skip lines that are commented out (single-line comments)
                                stripped = line.strip()
                                if stripped.startswith('//'):
                                    continue
                                
                                # Skip lines that have // before the #define (inline comments)
                                # Check if there's a // before any potential #define
                                if '//' in line:
                                    # Find position of // and #define
                                    comment_pos = line.find('//')
                                    define_pos = line.find('#define')
                                    # If // comes before #define, skip this line
                                    if define_pos != -1 and comment_pos != -1 and comment_pos < define_pos:
                                        continue
                                
                                # Find matches in non-commented lines
                                match = re.search(pattern, line, re.IGNORECASE)
                                if match:
                                    macro_name = match.group(1).strip()
                                    function_name = match.group(2).strip()
                                    validation_macros[macro_name] = function_name
                                
                        except Exception as e:
                            # Skip files that can't be read
                            continue
    
    return validation_macros


def extract_validation_macros_from_file(file_path: str) -> Dict[str, str]:
    """
    Extract validation macro definitions from a specific file.
    
    Supports both namespaced and non-namespaced function names:
    - #define NotNull /* Validation Function -> DtoValidationUtility::ValidateNotNull */
    - #define NotNull /* Validation Function -> nayan::validation::DtoValidationUtility::ValidateNotNull */
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        Dictionary mapping macro names to validation function names
    """
    validation_macros = {}
    
    if not os.path.exists(file_path):
        return validation_macros
    
    # Pattern to match: #define MacroName /* Validation Function -> FunctionName */
    # FunctionName can include namespaces (e.g., nayan::validation::DtoValidationUtility::ValidateNotNull)
    pattern = r'#define\s+(\w+)\s+/\*\s*Validation\s+Function\s*->\s*([^\*]+?)\s*\*/'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Check each line (skip commented lines)
        for line in lines:
            # Skip lines that are commented out (single-line comments)
            stripped = line.strip()
            if stripped.startswith('//'):
                continue
            
            # Skip lines that have // before the #define (inline comments)
            # Check if there's a // before any potential #define
            if '//' in line:
                # Find position of // and #define
                comment_pos = line.find('//')
                define_pos = line.find('#define')
                # If // comes before #define, skip this line
                if define_pos != -1 and comment_pos != -1 and comment_pos < define_pos:
                    continue
            
            # Find matches in non-commented lines
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                macro_name = match.group(1).strip()
                function_name = match.group(2).strip()
                validation_macros[macro_name] = function_name
            
    except Exception as e:
        pass
    
    return validation_macros


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Discover validation macros from source files"
    )
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        help="Directories to search for validation macro definitions"
    )
    parser.add_argument(
        "--file",
        help="Specific file to scan for validation macros"
    )
    
    args = parser.parse_args()
    
    if args.file:
        macros = extract_validation_macros_from_file(args.file)
    else:
        search_dirs = args.search_dirs if args.search_dirs else None
        macros = find_validation_macro_definitions(search_dirs)
    
    # print(f"Found {len(macros)} validation macro(s):")
    # print(f"Found {len(macros)} validation macro(s):")
        # print(f"  {macro_name} -> {function_name}")
        # print(f"  {macro_name} -> {function_name}")
    return 0


# Export functions for other scripts to import
__all__ = [
    'find_validation_macro_definitions',
    'extract_validation_macro_definitions_from_file',
    'main'
]


if __name__ == "__main__":
    exit(main())

