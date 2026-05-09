cmake_minimum_required(VERSION 3.16)
project(CTGProcessor LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCV REQUIRED)

add_executable(ctg_processor
    main.cpp
    CTGProcessor.cpp
    SignalExtractor.cpp
    CsvWriter.cpp
)

target_include_directories(ctg_processor PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(ctg_processor PRIVATE ${OpenCV_LIBS})
