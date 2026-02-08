#!/usr/bin/env python3
"""
S8 Handle Enum Serialization Script

This script detects enums with @Serializable annotation and generates
template specialization functions for Serialize and Deserialize.
"""

import re
import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple

def check_enum_annotation(file_path: str, serializable_annotation: str = "Serializable") -> Optional[Dict[str, any]]:
    """
    Check if a C++ file contains an enum with the @Serializable annotation above it.
    
    Args:
        file_path: Path to the C++ file
        serializable_annotation: Name of the annotation identifier (Serializable -> @Serializable)
        
    Returns:
        Dictionary with 'enum_name', 'has_enum', 'annotation_line', 'enum_line' if found, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return None
    except Exception as e:
        return None
    
    # Determine annotation name
    if serializable_annotation == "Serializable":
        annotation_name = "@Serializable"
    else:
        annotation_name = "@Serializable"
    
    # Pattern to match /* @Serializable */ or /* Serializable */ or /*@Serializable*/
    annotation_pattern = rf'/\*\s*{re.escape(annotation_name)}\s*\*/|/\*\s*Serializable\s*\*/'
    processed_pattern = rf'/\*--\s*{re.escape(annotation_name)}\s*--\*/'
    
    # Pattern to match enum class declarations
    enum_pattern = r'enum\s+(?:class\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:{])'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Check if line is already processed
        if re.search(processed_pattern, stripped_line):
            continue
        
        # Check for annotation
        annotation_match = re.search(annotation_pattern, stripped_line)
        if annotation_match:
            # Look ahead for enum declaration (within next 20 lines to allow for comments/macros)
            for i in range(line_num + 1, min(line_num + 21, len(lines) + 1)):  # Start from next line
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    
                    # Skip empty lines
                    if not next_line:
                        continue
                    
                    # Skip comments (but not the annotation itself)
                    if next_line.startswith('/*') and not re.search(processed_pattern, next_line):
                        continue
                    if next_line.startswith('//'):
                        continue
                    
                    # Check for enum declaration
                    enum_match = re.search(enum_pattern, next_line)
                    if enum_match:
                        enum_name = enum_match.group(1)
                        return {
                            'enum_name': enum_name,
                            'has_enum': True,
                            'annotation_line': line_num,
                            'enum_line': i
                        }
                    
                    # Continue searching - don't break early, allow for other text between annotation and enum
    
    return {
        'has_enum': False
    }


def extract_enum_values(file_path: str, enum_name: str, enum_line: int) -> List[str]:
    """
    Extract enum values from an enum declaration.
    
    Args:
        file_path: Path to the C++ file
        enum_name: Name of the enum
        enum_line: Line number where enum starts
        
    Returns:
        List of enum value names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception:
        return []
    
    enum_values = []
    brace_count = 0
    in_enum = False
    found_opening_brace = False
    
    # Start from enum line
    for i in range(enum_line - 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        # Check if we're entering the enum
        if f'enum' in stripped and enum_name in stripped:
            in_enum = True
            brace_count = stripped.count('{') - stripped.count('}')
            if '{' in stripped:
                found_opening_brace = True
            continue
        
        if in_enum:
            # Track opening brace
            if '{' in stripped:
                found_opening_brace = True
            
            brace_count += stripped.count('{')
            brace_count -= stripped.count('}')
            
            # Only extract values if we've found the opening brace
            if found_opening_brace:
                # Remove comments from line for parsing
                line_no_comments = re.sub(r'//.*$', '', stripped)  # Remove // comments
                line_no_comments = re.sub(r'/\*.*?\*/', '', line_no_comments)  # Remove /* */ comments
                
                # Extract enum values - pattern: ValueName (optionally followed by = value or comma)
                # Match: identifier at start of line or after comma/whitespace, before comma or }
                value_pattern = r'(?:^|\s|,)([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*[^,}]+)?\s*(?=,|}|$)'
                
                # Find all enum values in this line
                for match in re.finditer(value_pattern, line_no_comments):
                    value_name = match.group(1).strip()
                    # Filter out common keywords and the enum name itself
                    if (value_name and 
                        value_name not in enum_values and 
                        value_name != enum_name and
                        value_name not in ['if', 'endif', 'define', 'include', 'pragma']):
                        enum_values.append(value_name)
            
            # If braces are balanced and we found the opening brace, we're done
            if brace_count == 0 and found_opening_brace:
                break
    
    return enum_values


def generate_enum_serialization_code(enum_name: str, enum_values: List[str]) -> str:
    """
    Generate template specialization functions for enum serialization/deserialization.
    
    Args:
        enum_name: Name of the enum
        enum_values: List of enum value names
        
    Returns:
        Generated code as string
    """
    code_lines = []
    
    code_lines.append("namespace nayan {")
    code_lines.append("namespace serializer {")
    code_lines.append("")
    
    # Generate Serialize template specialization
    code_lines.append("    /**")
    code_lines.append(f"     * Serialize {enum_name} enum to JSON string")
    code_lines.append("     */")
    code_lines.append(f"    template<>")
    code_lines.append(f"    inline StdString SerializationUtility::Serialize<{enum_name}>(const {enum_name}& value) {{")
    code_lines.append("        // Convert enum to string representation")
    code_lines.append("        StdString enumStr;")
    code_lines.append("        switch (value) {")
    
    for value in enum_values:
        code_lines.append(f"            case {enum_name}::{value}:")
        code_lines.append(f"                enumStr = \"{value}\";")
        code_lines.append("                break;")
    
    code_lines.append("            default:")
    code_lines.append("                enumStr = \"UNKNOWN\";")
    code_lines.append("                break;")
    code_lines.append("        }")
    code_lines.append("        ")
    code_lines.append("        // Return enum as string (ArduinoJson will quote it when adding to JSON)")
    code_lines.append("        return enumStr;")
    code_lines.append("    }")
    code_lines.append("")
    
    # Generate Deserialize template specialization
    code_lines.append("    /**")
    code_lines.append(f"     * Deserialize JSON string to {enum_name} enum")
    code_lines.append("     */")
    code_lines.append(f"    template<>")
    code_lines.append(f"    inline {enum_name} SerializationUtility::Deserialize<{enum_name}>(const StdString& input) {{")
    code_lines.append("        // Remove quotes if present")
    code_lines.append("        StdString cleaned = input;")
    code_lines.append("        if (cleaned.length() >= 2 && cleaned.front() == '\\\"' && cleaned.back() == '\\\"') {")
    code_lines.append("            cleaned = cleaned.substr(1, cleaned.length() - 2);")
    code_lines.append("        }")
    code_lines.append("        ")
    code_lines.append("        // Try to parse as JSON first (handles quoted strings)")
    code_lines.append("        JsonDocument doc;")
    code_lines.append("        DeserializationError error = deserializeJson(doc, input.c_str());")
    code_lines.append("        if (error == DeserializationError::Ok && doc.is<const char*>()) {")
    code_lines.append("            cleaned = StdString(doc.as<const char*>());")
    code_lines.append("        }")
    code_lines.append("        ")
    code_lines.append("        // Convert string to enum")
    code_lines.append("        // Case-insensitive comparison")
    code_lines.append("        StdString lower = cleaned;")
    code_lines.append("        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);")
    code_lines.append("        ")
    
    for value in enum_values:
        value_lower = value.lower()
        code_lines.append(f"        if (lower == \"{value_lower}\" || cleaned == \"{value}\") {{")
        code_lines.append(f"            return {enum_name}::{value};")
        code_lines.append("        }")
    
    code_lines.append("        ")
    code_lines.append("        // Default or unknown value")
    code_lines.append(f"        return {enum_name}::{enum_values[0] if enum_values else 'UNKNOWN'};")
    code_lines.append("    }")
    code_lines.append("")
    
    code_lines.append("} // namespace serializer")
    code_lines.append("} // namespace nayan")
    
    return "\n".join(code_lines)


def find_last_endif(file_path: str) -> Optional[int]:
    """
    Find the line number of the last #endif in the file.
    
    Args:
        file_path: Path to the C++ file
        
    Returns:
        Line number of last #endif, or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception:
        return None
    
    last_endif = None
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('#endif'):
            last_endif = i
    
    return last_endif


def check_include_exists(file_path: str, include_pattern: str) -> bool:
    """
    Check if an include statement already exists in the file.
    
    Args:
        file_path: Path to the C++ file
        include_pattern: Pattern to search for (e.g., "SerializationUtility.h")
        
    Returns:
        True if include exists, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return include_pattern in content or f'<{include_pattern}>' in content or f'"{include_pattern}"' in content
    except Exception:
        return False


def add_include_if_needed(file_path: str, include_path: str) -> bool:
    """
    Add an include statement if it doesn't already exist.
    
    Args:
        file_path: Path to the C++ file
        include_path: Include path to add (e.g., "<SerializationUtility.h>" or '"some/header.h"')
        
    Returns:
        True if include was added or already exists, False on error
    """
    if check_include_exists(file_path, include_path.replace('<', '').replace('>', '').replace('"', '')):
        return True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Find the last #include line
        last_include_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('#include'):
                last_include_idx = i
        
        # Insert after the last include
        if last_include_idx >= 0:
            lines.insert(last_include_idx + 1, f'#include {include_path}\n')
        else:
            # No includes found, add after header guard
            for i, line in enumerate(lines):
                if line.strip().startswith('#define') and '_H' in line:
                    lines.insert(i + 1, f'#include {include_path}\n')
                    break
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        return True
    except Exception as e:
        return False


def inject_enum_code(file_path: str, code: str, dry_run: bool = False) -> bool:
    """
    Inject enum serialization code just before the last #endif.
    
    Args:
        file_path: Path to the C++ file
        code: Code to inject
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if successful, False otherwise
    """
    last_endif_line = find_last_endif(file_path)
    if not last_endif_line:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception:
        return False
    
    # Check if code already exists
    file_content = ''.join(lines)
    if 'Serialize<' in file_content and 'Deserialize<' in file_content:
        # Check if it's for this enum specifically
        # Extract enum name from code
        serialize_match = re.search(r'Serialize<([A-Za-z_][A-Za-z0-9_]*)>', code)
        if serialize_match:
            enum_name = serialize_match.group(1)
            if f'Serialize<{enum_name}>' in file_content:
                # Already exists
                return True
    
    if dry_run:
        return True
    
    # Insert code before last #endif
    insert_idx = last_endif_line - 1  # Convert to 0-indexed
    
    # Add proper indentation
    code_lines = code.split('\n')
    indented_code = []
    for line in code_lines:
        if line.strip():
            indented_code.append(line + '\n')
        else:
            indented_code.append('\n')
    
    # Insert with blank line before
    lines[insert_idx:insert_idx] = ['\n'] + indented_code
    
    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return True
    except Exception as e:
        return False


def mark_enum_annotation_processed(file_path: str, annotation_line: int, dry_run: bool = False) -> bool:
    """
    Mark the enum annotation as processed.
    
    Args:
        file_path: Path to the C++ file
        annotation_line: Line number of the annotation
        dry_run: If True, don't actually modify the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except Exception:
        return False
    
    if annotation_line < 1 or annotation_line > len(lines):
        return False
    
    line = lines[annotation_line - 1]
    stripped = line.strip()
    
    # Pattern to match /* @Serializable */ or /* Serializable */
    annotation_pattern = r'/\*\s*(@?Serializable)\s*\*/'
    
    if re.search(annotation_pattern, stripped):
        # Replace with processed marker
        processed_line = re.sub(
            r'/\*\s*(@?Serializable)\s*\*/',
            r'/*--@Serializable--*/',
            line
        )
        
        if not dry_run:
            lines[annotation_line - 1] = processed_line
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                return True
            except Exception:
                return False
        else:
            return True
    
    return False


def main():
    """Main function to handle command line arguments and process enum serialization."""
    parser = argparse.ArgumentParser(
        description="Generate serialization/deserialization functions for enums with @Serializable annotation"
    )
    parser.add_argument(
        "file_path",
        help="Path to the C++ enum file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without modifying the file"
    )
    parser.add_argument(
        "--annotation",
        default="Serializable",
        help="Name of the annotation identifier (default: Serializable)"
    )
    
    args = parser.parse_args()
    
    # Check if enum has annotation
    enum_info = check_enum_annotation(args.file_path, args.annotation)
    
    if not enum_info or not enum_info.get('has_enum'):
        # No enum with annotation found
        return 0
    
    enum_name = enum_info['enum_name']
    enum_line = enum_info['enum_line']
    
    # Extract enum values
    enum_values = extract_enum_values(args.file_path, enum_name, enum_line)
    
    if not enum_values:
        # Could not extract enum values
        return 1
    
    # Generate code
    code = generate_enum_serialization_code(enum_name, enum_values)
    
    if args.dry_run:
        print(f"Would generate code for enum: {enum_name}")
        print(f"Enum values: {', '.join(enum_values)}")
        print("\nGenerated code:")
        print(code)
        return 0
    
    # Add necessary includes
    add_include_if_needed(args.file_path, "<SerializationUtility.h>")
    add_include_if_needed(args.file_path, "<algorithm>")
    add_include_if_needed(args.file_path, "<cctype>")
    
    # Inject code
    success = inject_enum_code(args.file_path, code, dry_run=False)
    if not success:
        return 1
    
    # Mark annotation as processed
    annotation_line = enum_info['annotation_line']
    mark_enum_annotation_processed(args.file_path, annotation_line, dry_run=False)
    
    return 0


# Export functions for other scripts to import
__all__ = [
    'check_enum_annotation',
    'extract_enum_values',
    'generate_enum_serialization_code',
    'inject_enum_code',
    'mark_enum_annotation_processed',
    'main'
]


if __name__ == "__main__":
    exit(main())

