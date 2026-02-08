#!/usr/bin/env python3
"""
S2 Extract Dto Fields Script

This script extracts public member variables from a Dto class.
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# print("Executing NayanSerializer/scripts/serializer/S2_extract_dto_fields.py")
# print("Executing NayanSerializer/scripts/serializer/S2_extract_dto_fields.py")

def find_class_boundaries(file_path: str, class_name: str) -> Optional[tuple]:
    """
    Find the start and end line numbers of a class definition.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class to find
        
    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        # print(f"Error reading file: {e}")
        pass
        # print(f"Error reading file: {e}")
    
    class_start = None
    brace_count = 0
    in_class = False
    
    # Pattern to match class declaration
    # Matches: "class TestDto : public Serializablex<TestDto> {" or "class TestDto {"
    # Use a simpler pattern that just checks for class name
    class_pattern = rf'class\s+{re.escape(class_name)}'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Skip commented lines
        if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.startswith('*'):
            continue
        
        # Check for class declaration
        if not in_class and re.search(class_pattern, stripped_line):
            class_start = line_num
            in_class = True
            # Initialize brace count from this line
            brace_count = stripped_line.count('{') - stripped_line.count('}')
        elif in_class:
            # Count braces for subsequent lines
            brace_count += stripped_line.count('{')
            brace_count -= stripped_line.count('}')
        
        if in_class:
            # If braces are balanced and we've closed the class, we're done
            if brace_count == 0:
                return (class_start, line_num)
    
    return None


def extract_all_fields(file_path: str, class_name: str) -> List[Dict[str, str]]:
    """
    Extract all member variables (public, private, protected) from a class.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class
        
    Returns:
        List of dictionaries with 'type' and 'name' keys
    """
    boundaries = find_class_boundaries(file_path, class_name)
    if not boundaries:
        return []
    
    start_line, end_line = boundaries
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception as e:
        # print(f"Error reading file: {e}")
        pass
        # print(f"Error reading file: {e}")
    
    class_lines = lines[start_line - 1:end_line]
    
    fields = []
    current_access = None
    
    # Patterns
    access_pattern = r'^\s*(public|private|protected)\s*:'
    # Field pattern: matches "int a;" or "StdString name;"
    field_pattern = r'^\s*([A-Za-z_][A-Za-z0-9_<>*&,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[;=]'
    
    for line in class_lines:
        stripped = line.strip()
        
        # Skip comments
        if stripped.startswith('//') or stripped.startswith('/*'):
            continue
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Check for access specifier (case insensitive)
        access_match = re.search(access_pattern, stripped, re.IGNORECASE)
        if access_match:
            current_access = access_match.group(1).lower()
            continue
        
        # Process all members (public, private, protected) - no access restriction
        # Check for member variable
        field_match = re.search(field_pattern, stripped)
        if field_match:
            field_type = field_match.group(1).strip()
            field_name = field_match.group(2).strip()
            # Skip if it looks like a method declaration (has parentheses) or is a keyword
            if '(' not in stripped and ')' not in stripped and field_name not in ['public', 'private', 'protected']:
                fields.append({
                    'type': field_type,
                    'name': field_name
                })
    
    return fields


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract public fields from a Dto class"
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
    
    fields = extract_public_fields(args.file_path, args.class_name)
    
    # print(f"Fields found: {len(fields)}")
    # print(f"Fields found: {len(fields)}")
    #     # print(f"  {field['type']} {field['name']}")
    #     print(f"  {field['type']} {field['name']}")
    return 0


# Alias for backward compatibility
extract_public_fields = extract_all_fields

# Export functions for other scripts to import
__all__ = [
    'find_class_boundaries',
    'extract_all_fields',
    'extract_public_fields',
    'main'
]


if __name__ == "__main__":
    exit(main())

