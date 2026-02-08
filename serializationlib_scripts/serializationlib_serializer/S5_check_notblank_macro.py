#!/usr/bin/env python3
"""
S5 Check NotBlank Annotation Script

This script checks if a class member has the @NotBlank annotation above it.
@NotBlank validation only applies to string types.
"""

import re
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# print("Executing NayanSerializer/scripts/serializer/S5_check_notblank_macro.py")
# print("Executing NayanSerializer/scripts/serializer/S5_check_notblank_macro.py")
# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import S2_extract_dto_fields
except ImportError as e:
    # print(f"Error: Could not import required modules: {e}")
    # print(f"Error: Could not import required modules: {e}")
    sys.exit(1)


def is_string_type(field_type: str) -> bool:
    """
    Check if a field type is a string type (for NotBlank validation).
    Handles optional types like optional<StdString>, optional<CStdString>, etc.
    
    Args:
        field_type: The type string to check
        
    Returns:
        True if the type is a string type, False otherwise
    """
    field_type_clean = field_type.strip()
    
    # Extract inner type if it's optional
    if 'optional<' in field_type_clean.lower():
        # Extract inner type from optional<...>
        import re
        match = re.search(r'(?:std::)?optional<(.+)>', field_type_clean, re.IGNORECASE)
        if match:
            inner_type = match.group(1).strip()
            field_type_clean = inner_type
    
    field_type_lower = field_type_clean.lower()
    # Check for string types: StdString, CStdString, std::string, const std::string, etc.
    string_types = ['stdstring', 'cstdstring', 'std::string', 'const std::string', 'string']
    return any(st in field_type_lower for st in string_types)


def extract_notblank_fields(file_path: str, class_name: str) -> List[Dict[str, str]]:
    """
    Extract all member variables that have the @NotBlank annotation above them.
    Only includes fields that are string types (@NotBlank only applies to strings).
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class
        
    Returns:
        List of dictionaries with 'type', 'name', and 'access' keys for fields with @NotBlank annotation
        (only string types are included)
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
    
    notblank_fields = []
    current_access = None
    
    # Patterns
    access_pattern = r'^\s*(public|private|protected)\s*:'
    # Pattern for /* @NotBlank */ or /*@NotBlank*/ annotation (ignoring whitespace)
    notblank_annotation_pattern = r'/\*\s*@NotBlank\s*\*/'
    # Pattern for /* @NotNull */ or /*@NotNull*/ annotation (can appear between @NotBlank and field)
    notnull_annotation_pattern = r'/\*\s*@NotNull\s*\*/'
    # Field pattern: matches "int a;", "optional<StdString> x;" with optional access specifier
    field_pattern = r'^\s*(?:Public|Private|Protected)?\s*([A-Za-z_][A-Za-z0-9_<>*&,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[;=]'
    
    i = 0
    while i < len(class_lines):
        line = class_lines[i]
        stripped = line.strip()
        
        # Skip other comments that aren't @NotBlank annotations
        # But allow /* @NotBlank */ annotations to be processed
        if stripped.startswith('/*') and not re.search(notblank_annotation_pattern, stripped):
            i += 1
            continue
        # Skip single-line comments
        if stripped.startswith('//'):
            i += 1
            continue
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # Check for access specifier (case insensitive)
        access_match = re.search(access_pattern, stripped, re.IGNORECASE)
        if access_match:
            current_access = access_match.group(1).lower()
            i += 1
            continue
        
        # Check for @NotBlank annotation (/* @NotBlank */ or /*@NotBlank*/)
        notblank_match = re.search(notblank_annotation_pattern, stripped)
        if notblank_match:
            # Look ahead for field declaration (within next 10 lines, may have @NotNull in between)
            found_field = False
            for j in range(i + 1, min(i + 11, len(class_lines))):
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
                
                # Skip @NotNull annotation (can appear between @NotBlank and field)
                if re.search(notnull_annotation_pattern, next_line):
                    continue
                
                # Check for field declaration
                field_match = re.search(field_pattern, next_line)
                if field_match:
                    field_type = field_match.group(1).strip()
                    field_name = field_match.group(2).strip()
                    # Skip if it looks like a method declaration
                    if '(' not in next_line and ')' not in next_line and field_name not in ['public', 'private', 'protected']:
                        # Only include if it's a string type (@NotBlank only applies to strings)
                        if is_string_type(field_type):
                            notblank_fields.append({
                                'type': field_type,
                                'name': field_name,
                                'access': current_access if current_access else 'none'
                            })
                        found_field = True
                    break
                
                # Stop if we hit another annotation or access specifier
                if next_line and (re.search(access_pattern, next_line, re.IGNORECASE) or 
                                 re.search(r'^\s*(Dto|Serializable|COMPONENT|SCOPE|VALIDATE|///\s*@(NotNull|NotEmpty|NotBlank|Id|Entity|Serializable))\s*$', next_line)):
                    break
            
            i += 1
            continue
        
        i += 1
    
    return notblank_fields


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract fields with @NotBlank annotation from a class (string types only)"
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
    
    fields = extract_notblank_fields(args.file_path, args.class_name)
    
    # print(f"@NotBlank fields found: {len(fields)}")
    # print(f"@NotBlank fields found: {len(fields)}")
        # print(f"  {field['type']} {field['name']} (access: {field['access']})")
        # print(f"  {field['type']} {field['name']} (access: {field['access']})")
    return 0


# Export functions for other scripts to import
__all__ = [
    'extract_notblank_fields',
    'is_string_type',
    'main'
]


if __name__ == "__main__":
    exit(main())
