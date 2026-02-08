#!/usr/bin/env python3
"""
00 Process Serializable Classes Script

Orchestrator script that processes all classes with @Serializable annotation in client files.
Uses 05_list_client_files.py to get the list of client files.
"""

import os
import sys
import importlib.util
from pathlib import Path

# print("Executing NayanSerializer/scripts/serializer/00_process_serializable_classes.py")
# print("Executing NayanSerializer/scripts/serializer/00_process_serializable_classes.py")
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
# Import the serializer scripts
# Determine script_dir - where this script and other serializer scripts are located
try:
    script_file = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_file)
except NameError:
    # __file__ not available (exec() context) - try to find script directory
    script_dir = None
    
    # Method 1: If we have script_dir pointing to scripts/core/, go up and into serializer/
    # This is the most reliable method since script_dir is set by 02_find_library.py
    if 'script_dir' in globals() and globals()['script_dir']:
        # script_dir is scripts/core/, so go up one level to scripts/, then to serializer/
        scripts_parent = os.path.dirname(globals()['script_dir'])
        candidate = os.path.join(scripts_parent, 'serializer')
        # print(f"DEBUG: Method 1 - script_dir={globals()['script_dir']}, scripts_parent={scripts_parent}, candidate={candidate}, exists={os.path.exists(candidate)}")
        # print(f"DEBUG: Method 1 - script_dir={globals()['script_dir']}, scripts_parent={scripts_parent}, candidate={candidate}, exists={os.path.exists(candidate)}")
        if os.path.exists(candidate):
            script_dir = candidate
    
    # Method 2: Try initial_script_dir (from execute_scripts.py) - this is scripts/
    if (not script_dir or not os.path.exists(script_dir)) and 'initial_script_dir' in globals() and globals()['initial_script_dir']:
        candidate = os.path.join(globals()['initial_script_dir'], 'serializer')
        if os.path.exists(candidate):
            script_dir = candidate
    
    # Method 3: Try _pre_build_script_dir (from pre_build.py) - this is scripts/
    if (not script_dir or not os.path.exists(script_dir)) and '_pre_build_script_dir' in globals():
        candidate = os.path.join(globals()['_pre_build_script_dir'], 'serializer')
        if os.path.exists(candidate):
            script_dir = candidate
    
    # Method 4: Try script_dir (from 02_find_library.py) - this is scripts/core/
    # (This is already handled in Method 1, but keeping as fallback)
    if (not script_dir or not os.path.exists(script_dir)) and 'script_dir' in globals() and globals()['script_dir']:
        # script_dir is scripts/core/, so go up one level to scripts/, then to serializer/
        scripts_parent = os.path.dirname(globals()['script_dir'])
        candidate = os.path.join(scripts_parent, 'serializer')
        if os.path.exists(candidate):
            script_dir = candidate
    
    # Method 4: Try to find from lib_dir (from 02_find_library.py)
    if (not script_dir or not os.path.exists(script_dir)) and 'lib_dir' in globals() and globals()['lib_dir']:
        candidate = os.path.join(globals()['lib_dir'], 'scripts', 'serializer')
        if os.path.exists(candidate):
            script_dir = candidate
    
    # Method 5: Fallback - search from current directory
    if not script_dir or not os.path.exists(script_dir):
        cwd = os.getcwd()
        possible_dirs = [
            os.path.join(cwd, 'scripts', 'serializer'),
            os.path.join(os.path.dirname(cwd), 'scripts', 'serializer'),
        ]
        for dir_path in possible_dirs:
            if os.path.exists(dir_path):
                script_dir = dir_path
                break
        
        # Final fallback - try to find from known library location or lib_dir
        if not script_dir or not os.path.exists(script_dir):
            # Try lib_dir first if available
            if 'lib_dir' in globals() and globals()['lib_dir']:
                candidate = os.path.join(globals()['lib_dir'], 'scripts', 'serializer')
                if os.path.exists(candidate):
                    script_dir = candidate
            
            # If still not found, try common library locations
            if not script_dir or not os.path.exists(script_dir):
                known_lib_paths = [
                    '/Users/nkurude/CLionProjects/Experiments/mylibs/NayanSerializer',
                ]
                for lib_path in known_lib_paths:
                    candidate = os.path.join(lib_path, 'scripts', 'serializer')
                    if os.path.exists(candidate):
                        script_dir = candidate
                        break

# Verify script_dir exists and contains the serializer scripts
# If script_dir doesn't exist or doesn't contain serializer scripts, try to fix it
if not os.path.exists(script_dir) or not os.path.exists(os.path.join(script_dir, "S1_check_dto_macro.py")):
    # If script_dir points to scripts/ instead of scripts/serializer/, fix it
    if script_dir.endswith('scripts') and os.path.exists(os.path.join(script_dir, 'serializer')):
        script_dir = os.path.join(script_dir, 'serializer')
    
    # If still not found, try lib_dir
    if (not os.path.exists(script_dir) or not os.path.exists(os.path.join(script_dir, "S1_check_dto_macro.py"))) and 'lib_dir' in globals() and globals()['lib_dir']:
        candidate = os.path.join(globals()['lib_dir'], 'scripts', 'serializer')
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, "S1_check_dto_macro.py")):
            script_dir = candidate
    
    # Final check
    if not os.path.exists(script_dir) or not os.path.exists(os.path.join(script_dir, "S1_check_dto_macro.py")):
        # print(f"Error: Could not find serializer directory at {script_dir}")
        # print(f"Error: Could not find serializer directory at {script_dir}")
        # if 'initial_script_dir' in globals():
        #     print(f"  initial_script_dir: {globals()['initial_script_dir']}")
        # if 'script_dir' in globals():
        #     print(f"  script_dir: {globals()['script_dir']}")
        # if 'lib_dir' in globals():
        #     print(f"  lib_dir: {globals()['lib_dir']}")
        raise FileNotFoundError(f"Serializer directory not found: {script_dir}")

sys.path.insert(0, script_dir)

# Import serializer modules
s1_path = os.path.join(script_dir, "S1_check_dto_macro.py")
if not os.path.exists(s1_path):
    # print(f"Error: Could not find S1_check_dto_macro.py at {s1_path}")
    # print(f"Error: Could not find S1_check_dto_macro.py at {s1_path}")
    # print(f"  Files in script_dir: {os.listdir(script_dir) if os.path.exists(script_dir) else 'directory does not exist'}")
    # print(f"  Files in script_dir: {os.listdir(script_dir) if os.path.exists(script_dir) else 'directory does not exist'}")

    pass
spec_s1 = importlib.util.spec_from_file_location("S1_check_dto_macro", s1_path)
S1_check_dto_macro = importlib.util.module_from_spec(spec_s1)
spec_s1.loader.exec_module(S1_check_dto_macro)

spec_s3 = importlib.util.spec_from_file_location("S3_inject_serialization", os.path.join(script_dir, "S3_inject_serialization.py"))
S3_inject_serialization = importlib.util.module_from_spec(spec_s3)
spec_s3.loader.exec_module(S3_inject_serialization)

# Import enum serialization script
spec_s8 = importlib.util.spec_from_file_location("S8_handle_enum_serialization", os.path.join(script_dir, "S8_handle_enum_serialization.py"))
S8_handle_enum_serialization = importlib.util.module_from_spec(spec_s8)
spec_s8.loader.exec_module(S8_handle_enum_serialization)


def discover_all_libraries(project_dir):
    """
    Discover all library directories in build/_deps/ (CMake) and .pio/libdeps/ (PlatformIO).
    
    Args:
        project_dir: Path to the project root directory
    
    Returns:
        List of Path objects pointing to library source directories
    """
    libraries = []
    seen_libraries = set()  # Track seen libraries to avoid duplicates
    
    if not project_dir:
        return libraries
    
    project_path = Path(project_dir).resolve()
    
    # Check CMake FetchContent location: build/_deps/
    build_deps = project_path / "build" / "_deps"
    
    if build_deps.exists() and build_deps.is_dir():
        for lib_dir in build_deps.iterdir():
            if lib_dir.is_dir() and not lib_dir.name.startswith("."):
                lib_name = lib_dir.name
                
                # Include -src directories (source libraries)
                if lib_name.endswith("-src"):
                    lib_root = lib_dir.resolve()
                    lib_path_str = str(lib_root)
                    if lib_path_str not in seen_libraries:
                        seen_libraries.add(lib_path_str)
                        libraries.append(lib_root)
                # Also check if it's a library with src/ directory (like arduino-core-src)
                elif (lib_dir / "src").exists() and (lib_dir / "src").is_dir():
                    lib_root = lib_dir.resolve()
                    lib_path_str = str(lib_root)
                    if lib_path_str not in seen_libraries:
                        seen_libraries.add(lib_path_str)
                        libraries.append(lib_root)
    
    # Check PlatformIO library location: .pio/libdeps/
    pio_libdeps = project_path / ".pio" / "libdeps"
    
    if pio_libdeps.exists() and pio_libdeps.is_dir():
        # Iterate through environment directories (e.g., esp32dev, native, etc.)
        for env_dir in pio_libdeps.iterdir():
            if env_dir.is_dir():
                # Iterate through libraries in this environment
                for lib_dir in env_dir.iterdir():
                    if lib_dir.is_dir():
                        lib_root = lib_dir.resolve()
                        lib_path_str = str(lib_root)
                        
                        # Check if this library has a src/ directory
                        if (lib_root / "src").exists() and (lib_root / "src").is_dir():
                            if lib_path_str not in seen_libraries:
                                seen_libraries.add(lib_path_str)
                                libraries.append(lib_root)
    
    return libraries


def process_all_serializable_classes(dry_run=False, serializable_macro=None):
    """
    Process all client files that contain classes with @Serializable annotation.
    
    Args:
        dry_run: If True, show what would be processed without modifying files
        serializable_macro: Name of the annotation (kept for backward compatibility, but now looks for @Serializable)
        
    Returns:
        Number of files processed
    """
    # Get serializable_macro from parameter, globals, or environment
    if serializable_macro is None:
        if 'serializable_macro' in globals():
            serializable_macro = globals()['serializable_macro']
        elif 'SERIALIZABLE_MACRO' in os.environ:
            serializable_macro = os.environ['SERIALIZABLE_MACRO']
        else:
            serializable_macro = "Serializable"
    
    # Get project_dir from globals or environment
    project_dir = None
    if 'project_dir' in globals():
        project_dir = globals()['project_dir']
    elif 'PROJECT_DIR' in os.environ:
        project_dir = os.environ['PROJECT_DIR']
    elif 'CMAKE_PROJECT_DIR' in os.environ:
        project_dir = os.environ['CMAKE_PROJECT_DIR']
    
    if not project_dir:
        return 0
    
    # Get client header files using get_client_files function
    if get_client_files is None:
        return 0
    
    # Discover all libraries in build/_deps/
    all_libraries = discover_all_libraries(project_dir)
    
    # Collect header files from project_dir and all discovered libraries
    header_files = []
    
    # Get files from project_dir
    try:
        project_files = get_client_files(project_dir, file_extensions=['.h', '.hpp'])
        header_files.extend(project_files)
    except Exception as e:
        pass
    
    # Get files from all discovered libraries
    for lib_dir in all_libraries:
        try:
            lib_files = get_client_files(str(lib_dir), skip_exclusions=True, file_extensions=['.h', '.hpp'])
            header_files.extend(lib_files)
        except Exception as e:
            pass
    
    if not header_files:
        return 0
    
    processed_count = 0
    
    # Process each header file
    for file_path in header_files:
        if not os.path.exists(file_path):
            continue
        
        # First, check if file has enum with @Serializable annotation
        enum_info = S8_handle_enum_serialization.check_enum_annotation(file_path, serializable_macro)
        if enum_info and enum_info.get('has_enum'):
            # Process enum serialization
            if not dry_run:
                enum_name = enum_info['enum_name']
                enum_line = enum_info['enum_line']
                annotation_line = enum_info['annotation_line']
                
                # Extract enum values
                enum_values = S8_handle_enum_serialization.extract_enum_values(file_path, enum_name, enum_line)
                
                if enum_values:
                    # Generate code
                    code = S8_handle_enum_serialization.generate_enum_serialization_code(enum_name, enum_values)
                    
                    # Add necessary includes
                    S8_handle_enum_serialization.add_include_if_needed(file_path, "<SerializationUtility.h>")
                    S8_handle_enum_serialization.add_include_if_needed(file_path, "<algorithm>")
                    S8_handle_enum_serialization.add_include_if_needed(file_path, "<cctype>")
                    
                    # Inject code
                    success = S8_handle_enum_serialization.inject_enum_code(file_path, code, dry_run=False)
                    if success:
                        # Mark annotation as processed
                        S8_handle_enum_serialization.mark_enum_annotation_processed(file_path, annotation_line, dry_run=False)
                        processed_count += 1
        
        # Check if file has @Serializable annotation (for classes)
        dto_info = S1_check_dto_macro.check_dto_macro(file_path, serializable_macro)
        
        if not dto_info or not dto_info.get('has_dto'):
            continue
        
        class_name = dto_info['class_name']
        # Extract fields
        import S2_extract_dto_fields
        spec_s2 = importlib.util.spec_from_file_location("S2_extract_dto_fields", os.path.join(script_dir, "S2_extract_dto_fields.py"))
        S2_extract_dto_fields = importlib.util.module_from_spec(spec_s2)
        spec_s2.loader.exec_module(S2_extract_dto_fields)
        
        fields = S2_extract_dto_fields.extract_all_fields(file_path, class_name)
        
        if not fields:
            # print(f"⚠️  Warning: No fields found in {class_name}")
            # print(f"⚠️  Warning: No fields found in {class_name}")
        
            pass
        # Separate optional and non-optional fields
        optional_fields = [field for field in fields if S3_inject_serialization.is_optional_type(field['type'].strip())]
        non_optional_fields = [field for field in fields if not S3_inject_serialization.is_optional_type(field['type'].strip())]
        
        # print(f"   Found {len(fields)} field(s): {len(optional_fields)} optional, {len(non_optional_fields)} non-optional")
        # print(f"   Found {len(fields)} field(s): {len(optional_fields)} optional, {len(non_optional_fields)} non-optional")
        # Discover validation macros
        import S6_discover_validation_macros
        spec_s6 = importlib.util.spec_from_file_location("S6_discover_validation_macros", os.path.join(script_dir, "S6_discover_validation_macros.py"))
        S6_discover_validation_macros = importlib.util.module_from_spec(spec_s6)
        spec_s6.loader.exec_module(S6_discover_validation_macros)
        
        validation_macros = S6_discover_validation_macros.find_validation_macro_definitions(None)
        
        # if validation_macros:
            # print(f"   Discovered {len(validation_macros)} validation macro(s)")
        
        # Extract validation fields
        import S7_extract_validation_fields
        spec_s7 = importlib.util.spec_from_file_location("S7_extract_validation_fields", os.path.join(script_dir, "S7_extract_validation_fields.py"))
        S7_extract_validation_fields = importlib.util.module_from_spec(spec_s7)
        spec_s7.loader.exec_module(S7_extract_validation_fields)
        
        validation_fields_by_macro = S7_extract_validation_fields.extract_validation_fields(
            file_path, class_name, validation_macros
        )
        
        if validation_fields_by_macro:
            total_validated = sum(len(fields) for fields in validation_fields_by_macro.values())
            # print(f"   {total_validated} field(s) with validation macros")
            # print(f"   {total_validated} field(s) with validation macros")
        # Generate and inject methods
        methods_code = S3_inject_serialization.generate_serialization_methods(class_name, fields, validation_fields_by_macro)
        
        # Add includes if needed
        if not dry_run:
            # Note: ArduinoJson.h is already included in NayanSerializer.h, so no need to add it here
            if optional_fields:
                S3_inject_serialization.add_include_if_needed(file_path, "<optional>")
        
        # Inject methods
        success = S3_inject_serialization.inject_methods_into_class(file_path, class_name, methods_code, dry_run=dry_run)
        
        if success:
            # Mark @Serializable annotation as processed
            if not dry_run:
                S3_inject_serialization.comment_dto_macro(file_path, dry_run=False, serializable_macro=serializable_macro)
            processed_count += 1
            # print(f"   ✅ Successfully processed {class_name}")
            # print(f"   ✅ Successfully processed {class_name}")
        else:
            # print(f"   ❌ Failed to process {class_name}")
            # print(f"   ❌ Failed to process {class_name}")
            pass
    return processed_count


def main():
    """Main function to process all Serializable classes."""
    # Get serializable_macro from globals or environment
    serializable_macro = None
    if 'serializable_macro' in globals():
        serializable_macro = globals()['serializable_macro']
    elif 'SERIALIZABLE_MACRO' in os.environ:
        serializable_macro = os.environ['SERIALIZABLE_MACRO']
    
    processed_count = process_all_serializable_classes(dry_run=False, serializable_macro=serializable_macro)
    
    if processed_count > 0:
        # print(f"\n✅ Successfully processed {processed_count} file(s) with Serializable classes")
        pass
    else:
        # print("\nℹ️  No files with Serializable classes found")
        # print("\nℹ️  No files with Serializable classes found")
        pass
    return 0


if __name__ == "__main__":
    exit(main())
