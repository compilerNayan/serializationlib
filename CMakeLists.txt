cmake_minimum_required(VERSION 3.14)
project(serializationlib VERSION 1.0.0 LANGUAGES CXX)

# Run pre-build script during configuration (runs even if client creates own library)
# This will run whenever this CMakeLists.txt is processed
find_program(PYTHON_EXECUTABLE python3 python)
if(PYTHON_EXECUTABLE AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/serializationlib_scripts/serializationlib_pre_build.py")
    # Get the client project directory (CMAKE_SOURCE_DIR is the top-level project source directory)
    # When this library is included via FetchContent, CMAKE_SOURCE_DIR points to the client project
    set(CLIENT_PROJECT_DIR ${CMAKE_SOURCE_DIR})
    
    # Set environment variable for the script
    set(ENV{CMAKE_PROJECT_DIR} ${CLIENT_PROJECT_DIR})
    
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} 
            "${CMAKE_CURRENT_SOURCE_DIR}/serializationlib_scripts/serializationlib_pre_build.py"
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE PRE_BUILD_RESULT
        OUTPUT_VARIABLE PRE_BUILD_OUTPUT
        ERROR_VARIABLE PRE_BUILD_ERROR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_STRIP_TRAILING_WHITESPACE
    )
    if(PRE_BUILD_OUTPUT)
        message(STATUS "serializationlib pre-build output:\n${PRE_BUILD_OUTPUT}")
    endif()
    if(PRE_BUILD_ERROR)
        message(STATUS "serializationlib pre-build errors (expected in non-PlatformIO environment):\n${PRE_BUILD_ERROR}")
    endif()
    if(PRE_BUILD_RESULT AND NOT PRE_BUILD_RESULT EQUAL "0")
        message(STATUS "serializationlib pre-build script exited with code ${PRE_BUILD_RESULT} (this is expected in non-PlatformIO CMake builds)")
    endif()
endif()

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fetch dependencies
include(FetchContent)

# Fetch ArduinoJson dependency
FetchContent_Declare(
    ArduinoJson
    GIT_REPOSITORY https://github.com/bblanchon/ArduinoJson.git
    GIT_TAG        7.x  # Use the 7.x branch (latest stable)
)
FetchContent_MakeAvailable(ArduinoJson)

# Fetch cppcore for StandardDefines.h
FetchContent_Declare(
    cppcore
    GIT_REPOSITORY https://github.com/compilerNayan/cpp_core.git
    GIT_TAG        main  # Use the main branch
)
FetchContent_MakeAvailable(cppcore)

# Create header-only library (INTERFACE library)
add_library(serializationlib INTERFACE)

# Set target properties
set_target_properties(serializationlib PROPERTIES
    VERSION ${PROJECT_VERSION}
)

# Set include directories
target_include_directories(serializationlib INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    $<INSTALL_INTERFACE:include>
)

# Add cppcore include directory (for StandardDefines.h)
# Use BUILD_INTERFACE generator expression to properly handle FetchContent paths
FetchContent_GetProperties(cppcore)
if(cppcore_SOURCE_DIR)
    target_include_directories(serializationlib INTERFACE
        $<BUILD_INTERFACE:${cppcore_SOURCE_DIR}/include>
    )
endif()

# Link ArduinoJson (header-only library)
# Try the namespaced target first, fallback to non-namespaced
if(TARGET ArduinoJson::ArduinoJson)
    target_link_libraries(serializationlib INTERFACE ArduinoJson::ArduinoJson)
elseif(TARGET ArduinoJson)
    target_link_libraries(serializationlib INTERFACE ArduinoJson)
else()
    # Fallback: manually add include directory if target doesn't exist
    FetchContent_GetProperties(ArduinoJson)
    if(ArduinoJson_SOURCE_DIR)
        target_include_directories(serializationlib INTERFACE ${ArduinoJson_SOURCE_DIR})
    endif()
endif()

# Note: For INTERFACE libraries, we don't need to add header files to target_sources
# The include directories are sufficient for consumers to find the headers

# Add pre-build script execution
# Note: This script requires PlatformIO environment to run properly
find_program(PYTHON_EXECUTABLE python3 python REQUIRED)

# Create a custom target that runs the pre-build script
# Set the project directory environment variable for the script
if(CMAKE_SOURCE_DIR)
    set(CLIENT_PROJECT_DIR ${CMAKE_SOURCE_DIR})
else()
    # Fallback if CMAKE_SOURCE_DIR is not available
    get_filename_component(CLIENT_PROJECT_DIR "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
endif()

add_custom_target(serializationlib_pre_build
    COMMAND ${CMAKE_COMMAND} -E env "CMAKE_PROJECT_DIR=${CLIENT_PROJECT_DIR}"
        ${PYTHON_EXECUTABLE} 
        "${CMAKE_CURRENT_SOURCE_DIR}/serializationlib_scripts/serializationlib_pre_build.py"
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Running serializationlib pre-build script"
    VERBATIM
)

# Make the library depend on the pre-build step
add_dependencies(serializationlib serializationlib_pre_build)

# Optional: Set up installation
include(GNUInstallDirs)

install(TARGETS serializationlib
    EXPORT serializationlibTargets
)

install(FILES src/NayanMath.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(EXPORT serializationlibTargets
    FILE serializationlibTargets.cmake
    NAMESPACE serializationlib::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/serializationlib
)

# Optional: Create a config file for find_package support
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/cmake/serializationlibConfig.cmake.in")
    include(CMakePackageConfigHelpers)

    configure_package_config_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/cmake/serializationlibConfig.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/serializationlibConfig.cmake"
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/serializationlib
    )

    write_basic_package_version_file(
        "${CMAKE_CURRENT_BINARY_DIR}/serializationlibConfigVersion.cmake"
        VERSION ${PROJECT_VERSION}
        COMPATIBILITY AnyNewerVersion
    )

    install(FILES
        "${CMAKE_CURRENT_BINARY_DIR}/serializationlibConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/serializationlibConfigVersion.cmake"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/serializationlib
    )
endif()

