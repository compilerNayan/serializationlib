#!/usr/bin/env python3
"""
S1 Check Serializable Annotation Script

This script checks if a C++ class has the @Serializable annotation above it.
"""

import re
import argparse
from pathlib import Path
from typing import Optional, Dict

# print("Executing NayanSerializer/scripts/serializer/S1_check_dto_macro.py")
# print("Executing NayanSerializer/scripts/serializer/S1_check_dto_macro.py")

def check_dto_annotation(file_path: str, serializable_annotation: str = "Serializable") -> Optional[Dict[str, any]]:
    """
    Check if a C++ file contains a class with the @Serializable or @Entity annotation above it.
    
    Args:
        file_path: Path to the C++ file
        serializable_annotation: Name of the annotation identifier (Serializable -> @Serializable, _Entity -> @Entity)
        
    Returns:
        Dictionary with 'class_name', 'has_dto', 'line_number' if found, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        # print(f"Error: File '{file_path}' not found")
        # print(f"Error: File '{file_path}' not found")
        pass
    except Exception as e:
        # print(f"Error reading file '{file_path}': {e}")
        # print(f"Error reading file '{file_path}': {e}")
    
        pass
    # Determine annotation name based on annotation identifier
    if serializable_annotation == "_Entity":
        annotation_name = "@Entity"
    elif serializable_annotation == "Serializable":
        annotation_name = "@Serializable"
    else:
        # Default to @Serializable for backward compatibility
        annotation_name = "@Serializable"
    
    # Pattern to match /* @Entity */ or /*@Entity*/ or /* @Serializable */ or /*@Serializable*/ annotation (ignoring whitespace)
    # Also check for already processed /*--@Entity--*/ or /*--@Serializable--*/ pattern
    annotation_pattern = rf'/\*\s*{re.escape(annotation_name)}\s*\*/'
    processed_pattern = rf'/\*--\s*{re.escape(annotation_name)}\s*--\*/'
    
    # Pattern to match class declarations
    class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:[:{])'
    
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Check if line is already processed (/*--@Entity--*/ or /*--@Serializable--*/)
        if re.search(processed_pattern, stripped_line):
            continue
        
        # Skip other comments that aren't @Entity/@Serializable annotations
        # But allow /* @Entity */ or /* @Serializable */ annotations to be processed
        if stripped_line.startswith('/*') and not re.search(annotation_pattern, stripped_line):
            continue
        # Skip single-line comments
        if stripped_line.startswith('//'):
            continue
        
        # Check for annotation (/* @Entity */ or /*@Entity*/ or /* @Serializable */ or /*@Serializable*/)
        annotation_match = re.search(annotation_pattern, stripped_line)
        if annotation_match:
            # Look ahead for class declaration (within next 10 lines)
            for i in range(line_num, min(line_num + 11, len(lines) + 1)):
                if i <= len(lines):
                    next_line = lines[i - 1].strip()
                    
                    # Skip comments (but not the annotation itself which is in a comment)
                    if next_line.startswith('/*') and not re.search(processed_pattern, next_line):
                        continue
                    # Skip other single-line comments that aren't the annotation
                    if next_line.startswith('//') and not re.search(annotation_pattern, next_line):
                        continue
                    
                    # Check for class declaration
                    class_match = re.search(class_pattern, next_line)
                    if class_match:
                        class_name = class_match.group(1)
                        return {
                            'class_name': class_name,
                            'has_dto': True,
                            'dto_line': line_num,
                            'class_line': i
                        }
                    
                    # Stop if we hit something that's not an annotation or class
                    # Check if it starts with known annotations/macros
                    known_annotations = ('COMPONENT', 'SCOPE', 'VALIDATE', 'Dto')
                    if next_line and not (next_line.startswith(known_annotations) or 
                                         re.match(r'^[A-Z][A-Za-z0-9_]*\s*(?:\(|$)', next_line) or
                                         re.search(annotation_pattern, next_line)):
                        break
    
    return {
        'has_dto': False
    }


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Check if a C++ class has the @Serializable or @Entity annotation above it"
    )
    parser.add_argument(
        "file_path",
        help="Path to the C++ file to check"
    )
    parser.add_argument(
        "--annotation",
        "--macro",  # Keep for backward compatibility
        dest="annotation",
        default="Serializable",
        help="Name of the annotation identifier (Serializable -> @Serializable, _Entity -> @Entity)"
    )
    
    args = parser.parse_args()
    
    result = check_dto_annotation(args.file_path, args.annotation)
    
    if result and result.get('has_dto'):
        # Determine annotation name for display
        if args.annotation == "_Entity":
            annotation_name = "@Entity"
        elif args.annotation == "Serializable":
            annotation_name = "@Serializable"
        else:
            annotation_name = "@Serializable"
        # print(f"✅ Class '{result['class_name']}' has {annotation_name} annotation")
        # print(f"✅ Class '{result['class_name']}' has {annotation_name} annotation")
        # print(f"   Class declaration at line {result['class_line']}")
        # print(f"   Class declaration at line {result['class_line']}")
    else:
        # Determine annotation name for display
        if args.annotation == "_Entity":
            annotation_name = "@Entity"
        elif args.annotation == "Serializable":
            annotation_name = "@Serializable"
        else:
            annotation_name = "@Serializable"
        # print(f"❌ No class with {annotation_name} annotation found")
        # print(f"❌ No class with {annotation_name} annotation found")


# Backward compatibility alias
def check_dto_macro(file_path: str, serializable_macro: str = "Serializable") -> Optional[Dict[str, any]]:
    """
    Deprecated: Use check_dto_annotation instead.
    Check if a C++ file contains a class with the @Serializable or @Entity annotation above it.
    """
    return check_dto_annotation(file_path, serializable_macro)


# Export functions for other scripts to import
__all__ = [
    'check_dto_annotation',
    'check_dto_macro',  # Keep for backward compatibility
    'main'
]


if __name__ == "__main__":
    exit(main())


