#!/usr/bin/env python3
"""
S4 Check NotNull Annotation Script

This script checks if a class member has the @NotNull annotation above it.
"""

import re
import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional

# print("Executing NayanSerializer/scripts/serializer/S4_check_notnull_macro.py")
# print("Executing NayanSerializer/scripts/serializer/S4_check_notnull_macro.py")
# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import S2_extract_dto_fields
except ImportError as e:
    # print(f"Error: Could not import required modules: {e}")
    # print(f"Error: Could not import required modules: {e}")
    sys.exit(1)


def extract_notnull_fields(file_path: str, class_name: str) -> List[Dict[str, str]]:
    """
    Extract all member variables that have the @NotNull annotation above them.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class
        
    Returns:
        List of dictionaries with 'type', 'name', and 'access' keys for fields with @NotNull annotation
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        # print(f"Error reading file: {e}")
        # print(f"Error reading file: {e}")
    
        pass
    # Find class boundaries
    boundaries = S2_extract_dto_fields.find_class_boundaries(file_path, class_name)
    if not boundaries:
        return []
    
    start_line, end_line = boundaries
    class_lines = lines[start_line - 1:end_line]
    
    notnull_fields = []
    current_access = None
    
    # Patterns
    access_pattern = r'^\s*(public|private|protected)\s*:'
    # Pattern for /* @NotNull */ or /*@NotNull*/ annotation (ignoring whitespace)
    notnull_annotation_pattern = r'/\*\s*@NotNull\s*\*/'
    # Field pattern: matches "int a;", "Public optional<int> x;", "Private optional<int> x;", etc.
    # Handles both with and without Public/Private/Protected prefix
    field_pattern = r'^\s*(?:Public|Private|Protected)?\s*([A-Za-z_][A-Za-z0-9_<>*&,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[;=]'
    
    for i, line in enumerate(class_lines):
        stripped = line.strip()
        
        # Skip other comments that aren't @NotNull annotations
        # But allow /* @NotNull */ annotations to be processed
        if stripped.startswith('/*') and not re.search(notnull_annotation_pattern, stripped):
            continue
        # Skip single-line comments
        if stripped.startswith('//'):
            continue
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Check for access specifier (case insensitive)
        access_match = re.search(access_pattern, stripped, re.IGNORECASE)
        if access_match:
            current_access = access_match.group(1).lower()
            continue
        
        # Check for @NotNull annotation (/* @NotNull */ or /*@NotNull*/)
        notnull_match = re.search(notnull_annotation_pattern, stripped)
        if notnull_match:
            # Look ahead for field declaration (within next 5 lines)
            for j in range(i + 1, min(i + 6, len(class_lines))):
                next_line = class_lines[j].strip()
                
                # Skip other comments that aren't annotations
                # But allow /* @NotNull */, /* @NotBlank */, etc. annotations to be processed
                if next_line.startswith('/*') and not re.search(r'/\*\s*@(NotNull|NotEmpty|NotBlank|Id|Entity|Serializable)\s*\*/', next_line):
                    continue
                # Skip single-line comments
                if next_line.startswith('//'):
                    continue
                
                # Skip empty lines
                if not next_line:
                    continue
                
                # Check for field declaration
                field_match = re.search(field_pattern, next_line)
                if field_match:
                    field_type = field_match.group(1).strip()
                    field_name = field_match.group(2).strip()
                    # Skip if it looks like a method declaration
                    if '(' not in next_line and ')' not in next_line and field_name not in ['public', 'private', 'protected']:
                        notnull_fields.append({
                            'type': field_type,
                            'name': field_name,
                            'access': current_access if current_access else 'none'
                        })
                    break
                
                # Stop if we hit another annotation or access specifier
                if next_line and (re.search(access_pattern, next_line, re.IGNORECASE) or 
                                 re.search(r'^\s*(Dto|Serializable|COMPONENT|SCOPE|VALIDATE|///\s*@(NotNull|NotEmpty|NotBlank|Id|Entity|Serializable))\s*$', next_line)):
                    break
    
    return notnull_fields


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract fields with @NotNull annotation from a class"
    )
    parser.add_argument(
        "file_path",
        help="Path to the C++ file"
    )
    parser.add_argument(
        "--class-name",
        required=True,
        help="Name of the class to extract fields from"
    )
    
    args = parser.parse_args()
    
    fields = extract_notnull_fields(args.file_path, args.class_name)
    
    # print(f"@NotNull fields found: {len(fields)}")
    # print(f"@NotNull fields found: {len(fields)}")
        # print(f"  {field['type']} {field['name']} (access: {field['access']})")
        # print(f"  {field['type']} {field['name']} (access: {field['access']})")
    return 0


# Export functions for other scripts to import
__all__ = [
    'extract_notnull_fields',
    'main'
]


if __name__ == "__main__":
    exit(main())

