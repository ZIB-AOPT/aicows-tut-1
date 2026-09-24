cmake_minimum_required(VERSION 3.24)
project(hiddengems_bot LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_TLS_VERIFY ON)
include(FetchContent)
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

# Use installed packages when available; otherwise download fixed releases.
find_package(Boost 1.92 CONFIG QUIET COMPONENTS beast)
if(NOT Boost_FOUND)
    set(BOOST_INCLUDE_LIBRARIES beast)
    set(BOOST_ENABLE_CMAKE ON)
    FetchContent_Declare(Boost
        URL https://github.com/boostorg/boost/releases/download/boost-1.92.0/boost-1.92.0-cmake.tar.xz
        URL_HASH SHA256=9bed76128d4e46755dbe818487788c6fceb6f72b378f4daa49b7e1e600d9088d
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
    FetchContent_MakeAvailable(Boost)
endif()
find_package(nlohmann_json 3.12 CONFIG QUIET)
if(NOT nlohmann_json_FOUND)
    FetchContent_Declare(json
        URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
        URL_HASH SHA256=42f6e95cad6ec532fd372391373363b62a14af6d771056dbfc86160e6dfff7aa
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
    FetchContent_MakeAvailable(json)
endif()

add_executable(hiddengems-bot src/main.cpp)
target_link_libraries(hiddengems-bot PRIVATE Boost::beast nlohmann_json::nlohmann_json OpenSSL::SSL OpenSSL::Crypto Threads::Threads)
if(MSVC)
    target_compile_options(hiddengems-bot PRIVATE /W4)
else()
    target_compile_options(hiddengems-bot PRIVATE -Wall -Wextra -Wpedantic)
endif()
