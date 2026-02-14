"""
Resolve cpp_core and return get_all_files_std.

cpp_core is in the core library and is included everywhere. This helper
finds it from project_dir (build/_deps or .pio/libdeps) and returns
get_all_files_std for use by serializationlib scripts.
"""

import sys
from pathlib import Path


def find_and_import_get_all_files_std(project_dir):
    """
    Find cpp_core from project_dir and import get_all_files_std.
    Returns the function (cpp_core is assumed to be available).
    """
    project_path = Path(project_dir).resolve()

    # CMake: build/_deps/cpp_core-src/cpp_core_core
    cmake_core = project_path / "build" / "_deps" / "cpp_core-src" / "cpp_core_core"
    if cmake_core.exists() and (cmake_core / "get_all_source_files.py").exists():
        core_str = str(cmake_core)
        if core_str not in sys.path:
            sys.path.insert(0, core_str)
        from get_all_source_files import get_all_files_std
        return get_all_files_std

    # PlatformIO: .pio/libdeps/<env>/cpp_core/cpp_core_core
    pio_libdeps = project_path / ".pio" / "libdeps"
    if pio_libdeps.exists() and pio_libdeps.is_dir():
        for env_dir in pio_libdeps.iterdir():
            if env_dir.is_dir():
                cpp_core = env_dir / "cpp_core" / "cpp_core_core"
                if cpp_core.exists() and (cpp_core / "get_all_source_files.py").exists():
                    core_str = str(cpp_core)
                    if core_str not in sys.path:
                        sys.path.insert(0, core_str)
                    from get_all_source_files import get_all_files_std
                    return get_all_files_std

    raise ImportError("cpp_core not found; ensure it is a dependency (build/_deps or .pio/libdeps)")

