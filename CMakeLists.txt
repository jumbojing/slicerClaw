cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerClaw)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/YourUsername/SlicerClaw")
set(EXTENSION_CATEGORY "AI & Machine Learning")
set(EXTENSION_CONTRIBUTORS "Slicer Community")
set(EXTENSION_DESCRIPTION "A native LLM Agent directly integrated into 3D Slicer")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/YourUsername/SlicerClaw/main/SlicerClaw/Resources/Icons/SlicerClaw.png")
set(EXTENSION_DEPENDENCIES "")
set(EXTENSION_BUILD_SUBDIRECTORY ".")
set(EXTENSION_LICENSE_FILE ${CMAKE_CURRENT_SOURCE_DIR}/LICENSE)
set(EXTENSION_README_FILE ${CMAKE_CURRENT_SOURCE_DIR}/README.md)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(SlicerClaw)
