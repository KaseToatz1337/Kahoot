cmake_minimum_required(VERSION 3.12)

project("Kahoot")

set(CMAKE_CXX_STANDARD 20)

add_executable(Kahoot "src/main.cpp")

include_directories("lib/uWebSockets/src")
include_directories("lib/uWebSockets/uSockets/src")
include_directories("lib/zlib")