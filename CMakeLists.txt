cmake_minimum_required(VERSION 3.16)
project(AlMaghriz VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build a shared library
add_library(al_maghriz SHARED)

# Public sources (always present)
target_sources(al_maghriz PRIVATE
    src_public/api_bridge.cpp
    src_public/access_runtime.cpp
    src_public/parameter_mapper.cpp
    src_public/validation.cpp
)

# Strategy implementation sources. These are required locally to build and are
# not part of the public repository.
file(GLOB STRATEGY_SOURCES private_core/*.cpp)
if(STRATEGY_SOURCES)
    target_sources(al_maghriz PRIVATE ${STRATEGY_SOURCES})
else()
    message(FATAL_ERROR
        "Strategy sources are missing. "
        "A pre-built shared library is already provided in dist/."
    )
endif()

target_include_directories(al_maghriz
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/private_core
        ${CMAKE_CURRENT_SOURCE_DIR}/src_public
)

# OpenSSL (used for SHA-256)
find_package(PkgConfig REQUIRED)
pkg_check_modules(OPENSSL REQUIRED openssl)
target_include_directories(al_maghriz PRIVATE ${OPENSSL_INCLUDE_DIRS})
target_link_libraries(al_maghriz PRIVATE ${OPENSSL_LIBRARIES})
target_link_options(al_maghriz PRIVATE ${OPENSSL_LDFLAGS_OTHER})

# Release flags: the library is intended to be distributed as a Release .so.
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(al_maghriz PRIVATE
        -O3
        -DNDEBUG
        -flto
        -fPIC
        -fvisibility=hidden
        -fvisibility-inlines-hidden
        -Wall
        -Wextra
    )
    target_link_options(al_maghriz PRIVATE
        -flto
        -s
    )
endif()

set_target_properties(al_maghriz PROPERTIES
    OUTPUT_NAME al_maghriz
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)

# Optional install rules
include(GNUInstallDirs)
install(TARGETS al_maghriz
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
install(FILES include/al_maghriz_api.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)
