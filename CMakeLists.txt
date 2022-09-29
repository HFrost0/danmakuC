cmake_minimum_required(VERSION 3.23)
project(danmakuC)
set(CMAKE_CXX_STANDARD 17)

find_package(fmt REQUIRED)


#include_directories(danmakuC)
include_directories(/opt/homebrew/Caskroom/miniforge/base/envs/test10/lib/python3.10/site-packages/pybind11/include)
include_directories(/opt/homebrew/Caskroom/miniforge/base/envs/test10/include)
include_directories(/opt/homebrew/Caskroom/miniforge/base/envs/test10/include/python3.10)
include_directories(/opt/homebrew/Cellar/boost/1.79.0_2/include)
include_directories(/opt/homebrew/Cellar/fmt/9.1.0/include)

#link_directories(/opt/homebrew/Caskroom/miniforge/base/envs/test10/libs)
#link_directories(/opt/homebrew/Cellar/fmt/9.1.0/lib)
add_executable(${PROJECT_NAME} test.cpp)
target_link_libraries(${PROJECT_NAME} fmt::fmt)
