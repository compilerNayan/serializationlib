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

# Import get_std_file_discovery (uses cpp_core get_all_files_std)
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

# Add to path and import (cpp_core get_all_files_std - core library, included everywhere)
if serializationlib_scripts_dir and os.path.exists(serializationlib_scripts_dir):
    core_dir = os.path.join(serializationlib_scripts_dir, 'serializationlib_core')
    if os.path.exists(core_dir):
        sys.path.insert(0, core_dir)
        from get_std_file_discovery import find_and_import_get_all_files_std


def find_validation_macro_definitions(search_directories: List[str] = None) -> Dict[str, str]:
    """
    Discover all validation macros by scanning files for the pattern:
    #define MacroName /* Validation Function -> FunctionName */
    
    Supports both namespaced and non-namespaced function names:
    - #define NotNull /* Validation Function -> DtoValidationUtility::ValidateNotNull */
    - #define NotNull /* Validation Function -> nayan::validation::DtoValidationUtility::ValidateNotNull */
    
    Args:
        search_directories: List of directories to search (default: uses cpp_core get_all_files_std for project + libraries)
        
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
    
    if search_directories is None:
        project_dir = os.environ.get('PROJECT_DIR') or os.environ.get('CMAKE_PROJECT_DIR')
        if not project_dir and 'project_dir' in globals():
            project_dir = globals()['project_dir']
        get_all_files_std = find_and_import_get_all_files_std(project_dir)
        header_files = get_all_files_std(
            project_dir,
            file_extensions=['.h', '.hpp'],
            include_libraries=True,
        )
    
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

