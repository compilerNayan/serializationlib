# Helper CMake file to set up serializationlib pre-build script
# Include this file in your CMakeLists.txt after FetchContent_Populate(serializationlib)
# Usage: include(${serializationlib_SOURCE_DIR}/cmake/serializationlib_pre_build.cmake)

if(NOT DEFINED serializationlib_SOURCE_DIR)
    message(FATAL_ERROR "serializationlib_SOURCE_DIR must be defined. Make sure to call this after FetchContent_Populate(serializationlib)")
endif()

find_program(PYTHON_EXECUTABLE python3 python REQUIRED)

# Create the pre-build target
if(NOT TARGET serializationlib_pre_build)
    add_custom_target(serializationlib_pre_build
        COMMAND ${PYTHON_EXECUTABLE} 
            "${serializationlib_SOURCE_DIR}/serializationlib_scripts/serializationlib_pre_build.py"
        WORKING_DIRECTORY ${serializationlib_SOURCE_DIR}
        COMMENT "Running serializationlib pre-build script"
        VERBATIM
        ALL
    )
    message(STATUS "serializationlib_pre_build target created")
endif()

