#!/usr/bin/env python3
"""
S7 Extract Validation Fields Script

Generic script to extract fields with any validation annotation.
Uses discovered validation macros to find fields with validation annotations.
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Set

# print("Executing NayanSerializer/scripts/serializer/S7_extract_validation_fields.py")
# print("Executing NayanSerializer/scripts/serializer/S7_extract_validation_fields.py")
# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    import S2_extract_dto_fields
    import S6_discover_validation_macros
except ImportError as e:
    # print(f"Error: Could not import required modules: {e}")
    # print(f"Error: Could not import required modules: {e}")
    sys.exit(1)


def is_string_type(field_type: str) -> bool:
    """
    Check if a field type is a string type.
    Handles optional types like optional<StdString>, optional<CStdString>, etc.
    
    Args:
        field_type: The type string to check
        
    Returns:
        True if the type is a string type, False otherwise
    """
    field_type_clean = field_type.strip()
    
    # Extract inner type if it's optional
    if 'optional<' in field_type_clean.lower():
        match = re.search(r'(?:std::)?optional<(.+)>', field_type_clean, re.IGNORECASE)
        if match:
            inner_type = match.group(1).strip()
            field_type_clean = inner_type
    
    field_type_lower = field_type_clean.lower()
    # Check for string types: StdString, CStdString, std::string, const std::string, etc.
    string_types = ['stdstring', 'cstdstring', 'std::string', 'const std::string', 'string']
    return any(st in field_type_lower for st in string_types)


def get_validation_function_info(validation_macros: Dict[str, str], macro_name: str) -> Optional[Dict[str, str]]:
    """
    Get information about a validation function from the macro name.
    
    Args:
        validation_macros: Dictionary mapping macro names to function names
        macro_name: Name of the validation macro
        
    Returns:
        Dictionary with 'function_name' and 'requires_string_type' keys, or None if not found
    """
    if macro_name not in validation_macros:
        return None
    
    function_name = validation_macros[macro_name]
    
    # Determine if this validation requires string types
    # For now, we'll check function name - can be made configurable later
    requires_string_type = 'NotBlank' in function_name or 'NotEmpty' in function_name or 'String' in function_name
    
    return {
        'function_name': function_name,
        'requires_string_type': requires_string_type
    }


def extract_validation_fields(file_path: str, class_name: str, validation_macros: Dict[str, str]) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract all fields with validation annotations.
    
    Args:
        file_path: Path to the C++ file
        class_name: Name of the class
        validation_macros: Dictionary mapping annotation names (e.g., 'NotNull') to function names
        
    Returns:
        Dictionary mapping validation annotation names to lists of fields
        Example: {'NotNull': [{'type': 'optional<int>', 'name': 'a', 'access': 'none'}], ...}
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
        return {}
    
    start_line, end_line = boundaries
    class_lines = lines[start_line - 1:end_line]
    
    # Build pattern for all validation annotations
    macro_names = list(validation_macros.keys())
    if not macro_names:
        return {}
    
    # Create pattern to match any validation annotation (/* @NotNull */, /* @NotEmpty */, /* @NotBlank */, etc.)
    # Map macro names to annotation patterns (e.g., 'NotNull' -> '/* @NotNull */')
    annotation_patterns = {}
    for macro_name in macro_names:
        annotation_patterns[macro_name] = rf'/\*\s*@{re.escape(macro_name)}\s*\*/'
    
    # Combined pattern to match any validation annotation
    all_annotations = '|'.join(annotation_patterns.values())
    validation_pattern = rf'({all_annotations})'
    
    # Patterns
    access_pattern = r'^\s*(public|private|protected)\s*:'
    field_pattern = r'^\s*(?:Public|Private|Protected)?\s*([A-Za-z_][A-Za-z0-9_<>*&,\s]*?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*[;=]'
    
    # Result dictionary: macro_name -> list of fields
    result = {macro: [] for macro in macro_names}
    
    current_access = None
    i = 0
    
    while i < len(class_lines):
        line = class_lines[i]
        stripped = line.strip()
        
        # Skip comments (but not the annotation itself which is in a comment)
        if stripped.startswith('/*'):
            i += 1
            continue
        # Skip other single-line comments that aren't annotations
        if stripped.startswith('//') and not re.search(validation_pattern, stripped):
            i += 1
            continue
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # Check for access specifier
        access_match = re.search(access_pattern, stripped, re.IGNORECASE)
        if access_match:
            current_access = access_match.group(1).lower()
            i += 1
            continue
        
        # Check for validation annotation
        validation_match = re.search(validation_pattern, stripped)
        if validation_match:
            # Find which annotation was matched
            matched_annotation = None
            for macro_name, pattern in annotation_patterns.items():
                if re.search(pattern, stripped):
                    matched_annotation = macro_name
                    break
            
            if matched_annotation:
                validation_info = get_validation_function_info(validation_macros, matched_annotation)
                
                if validation_info:
                    # Look ahead for field declaration (within next 10 lines, may have other annotations in between)
                    found_field = False
                    for j in range(i + 1, min(i + 11, len(class_lines))):
                        next_line = class_lines[j].strip()
                        
                        # Skip comments (but not the annotation itself)
                        if next_line.startswith('/*'):
                            continue
                        # Skip other single-line comments that aren't annotations
                        if next_line.startswith('//') and not re.search(r'///\s*@(NotNull|NotEmpty|NotBlank|Id|Entity|Serializable)\b', next_line):
                            continue
                        
                        # Skip empty lines
                        if not next_line:
                            continue
                        
                        # Skip other validation annotations (can appear between validation annotation and field)
                        if re.search(validation_pattern, next_line):
                            continue
                        
                        # Check for field declaration
                        field_match = re.search(field_pattern, next_line)
                        if field_match:
                            field_type = field_match.group(1).strip()
                            field_name = field_match.group(2).strip()
                            # Skip if it looks like a method declaration
                            if '(' not in next_line and ')' not in next_line and field_name not in ['public', 'private', 'protected']:
                                # Check if validation requires string type
                                if validation_info['requires_string_type']:
                                    if is_string_type(field_type):
                                        result[matched_annotation].append({
                                            'type': field_type,
                                            'name': field_name,
                                            'access': current_access if current_access else 'none',
                                            'function_name': validation_info['function_name']
                                        })
                                else:
                                    # No type restriction
                                    result[matched_annotation].append({
                                        'type': field_type,
                                        'name': field_name,
                                        'access': current_access if current_access else 'none',
                                        'function_name': validation_info['function_name']
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
    
    # Remove empty entries
    return {k: v for k, v in result.items() if v}


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract fields with validation annotations from a class"
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
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=['src', 'platform'],
        help="Directories to search for validation macro definitions"
    )
    
    args = parser.parse_args()
    
    # Discover validation macros
    validation_macros = S6_discover_validation_macros.find_validation_macro_definitions(args.search_dirs)
    
    if not validation_macros:
        # print("No validation macros found")
        # print("No validation macros found")
    
        pass
    # Extract fields
    fields_by_macro = extract_validation_fields(args.file_path, args.class_name, validation_macros)
    
    # print(f"Validation fields found: {sum(len(v) for v in fields_by_macro.values())}")
    # print(f"Validation fields found: {sum(len(v) for v in fields_by_macro.values())}")
        # print(f"  {macro_name} ({len(fields)} field(s)):")
        # print(f"  {macro_name} ({len(fields)} field(s)):")
            # print(f"    {field['type']} {field['name']} (access: {field['access']}, function: {field['function_name']})")
            # print(f"    {field['type']} {field['name']} (access: {field['access']}, function: {field['function_name']})")
    return 0


# Export functions for other scripts to import
__all__ = [
    'extract_validation_fields',
    'get_validation_function_info',
    'is_string_type',
    'main'
]


if __name__ == "__main__":
    exit(main())

