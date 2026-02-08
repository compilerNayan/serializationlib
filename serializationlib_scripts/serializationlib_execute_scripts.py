"""
Script to execute client file processing.
This script imports get_client_files and processes the client project files.
"""

import os
import sys
import importlib.util
import traceback
from serializationlib_core.serializationlib_get_client_files import get_client_files


def execute_scripts(project_dir, library_dir, serializable_macro="Serializable"):
    """
    Execute the scripts to process client files.
    
    Args:
        project_dir: Path to the client project root (where platformio.ini is)
        library_dir: Path to the library directory
        serializable_macro: Name of the macro to search for (default: "Serializable")
    """
    # Set project_dir in globals so serializer scripts can access it
    globals()['project_dir'] = project_dir
    globals()['library_dir'] = library_dir
    globals()['serializable_macro'] = serializable_macro
    
    if project_dir:
        try:
            client_files = get_client_files(project_dir, file_extensions=['.h', '.cpp'])
        except Exception as e:
            traceback.print_exc()
    
    if library_dir:
        try:
            library_files = get_client_files(library_dir, skip_exclusions=True)
        except Exception as e:
            traceback.print_exc()
    # Run the master serializer script (00_process_serializable_classes.py)
    # Find the serializer directory
    try:
        # Get the directory of this script
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        # current_dir is serializationlib_scripts/, so serializer is in serializationlib_serializer/
        serializer_dir = os.path.join(current_dir, 'serializationlib_serializer')
    except NameError:
        # __file__ not available, try to find from library_dir
        if library_dir:
            serializer_dir = os.path.join(library_dir, 'serializationlib_scripts', 'serializationlib_serializer')
        else:
            serializer_dir = None
    
    if serializer_dir and os.path.exists(serializer_dir):
        serializer_script_path = os.path.join(serializer_dir, '00_process_serializable_classes.py')
        if os.path.exists(serializer_script_path):
            try:
                # Set environment variables so serializer script can access project_dir and library_dir
                if project_dir:
                    os.environ['PROJECT_DIR'] = project_dir
                    os.environ['CMAKE_PROJECT_DIR'] = project_dir
                if library_dir:
                    os.environ['LIBRARY_DIR'] = str(library_dir)
                # Set serializable macro name
                os.environ['SERIALIZABLE_MACRO'] = serializable_macro
                
                # Load and execute the serializer script
                spec = importlib.util.spec_from_file_location("process_serializable_classes", serializer_script_path)
                serializer_module = importlib.util.module_from_spec(spec)
                
                # Add serializer directory to path for imports
                sys.path.insert(0, serializer_dir)
                
                # Set globals in the module's namespace before execution
                # This ensures the serializer script can access project_dir and library_dir
                serializer_module.__dict__['project_dir'] = project_dir
                serializer_module.__dict__['library_dir'] = library_dir
                serializer_module.__dict__['serializable_macro'] = serializable_macro
                
                # Execute the module (this will run the top-level code)
                spec.loader.exec_module(serializer_module)
                
                # Call the main function if it exists
                if hasattr(serializer_module, 'main'):
                    serializer_module.main()
                elif hasattr(serializer_module, 'process_all_serializable_classes'):
                    serializer_module.process_all_serializable_classes(dry_run=False)
            except Exception as e:
                traceback.print_exc()
