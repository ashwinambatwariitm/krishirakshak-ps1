# KrishiRakshak - offline tomato disease and pest advisor, C++ on-device pipeline
#
# Native build (WSL / x86_64, for development and parity tests):
#   cmake -S cpp -B build/x86 -DCMAKE_BUILD_TYPE=Release && cmake --build build/x86 -j
# Cross build for Raspberry Pi 5 (aarch64):
#   cmake -S cpp -B build/arm -DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake -DCMAKE_BUILD_TYPE=Release
#   cmake --build build/arm -j
#
# Dependency locations (override with -D...):
#   ORT_ROOT          ONNX Runtime C++ release (1.23.2; same version used to validate the INT8 models)
#   OPENCV_ROOT       OpenCV for the target (ARM only; the x86 build uses the system OpenCV)
#   THIRD_PARTY_SRC   folder with sqlite-amalgamation-*/ and json.hpp (see cpp/README.md)
#   EXECUTORCH_ROOT   ExecuTorch install prefix; when set, the Llama advisor is compiled in (KR_WITH_LLM)
cmake_minimum_required(VERSION 3.16)
project(KrishiRakshak VERSION 0.1 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_FLAGS_RELEASE "-O3")
set(CMAKE_C_FLAGS_RELEASE "-O2")

set(THIRD_PARTY_SRC "$ENV{HOME}/third_party_src" CACHE PATH "sqlite amalgamation + json.hpp")
set(SQLITE_DIR "${THIRD_PARTY_SRC}/sqlite-amalgamation-3540100" CACHE PATH "SQLite amalgamation folder")
set(EXECUTORCH_ROOT "" CACHE PATH "ExecuTorch install prefix (optional)")

if(CMAKE_CROSSCOMPILING)
    message(STATUS "Cross-compiling for Raspberry Pi 5 (aarch64, Cortex-A76)")
    set(TARGET_ARCH "arm")
    # Cortex-A76 = Armv8.2-A with dot-product instructions (used by INT8 kernels)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mcpu=cortex-a76")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -mcpu=cortex-a76")
    set(ORT_ROOT "$ENV{HOME}/arm_libs/onnxruntime-linux-aarch64-1.23.2" CACHE PATH "ONNX Runtime")
    set(OPENCV_ROOT "$ENV{HOME}/arm_libs/opencv_4.10_arm" CACHE PATH "OpenCV for aarch64")
    set(OpenCV_INCLUDE_DIRS "${OPENCV_ROOT}/usr/include/opencv4")
    link_directories(${OPENCV_ROOT}/usr/lib/aarch64-linux-gnu)
    set(OpenCV_LIBS opencv_core opencv_imgproc opencv_imgcodecs)
    # Libraries of the Pi's own OS are resolved at run time on the Pi (same approach as road-anomaly-detection)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--allow-shlib-undefined -Wl,--unresolved-symbols=ignore-in-shared-libs")
else()
    message(STATUS "Native build (development machine)")
    set(TARGET_ARCH "native")
    set(ORT_ROOT "$ENV{HOME}/x86_libs/onnxruntime-linux-x64-1.23.2" CACHE PATH "ONNX Runtime")
    find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
endif()

# SQLite compiled into the binary (single-binary deployment), with the FTS5 full-text index enabled
add_library(sqlite3_static STATIC ${SQLITE_DIR}/sqlite3.c)
target_include_directories(sqlite3_static PUBLIC ${SQLITE_DIR})
target_compile_definitions(sqlite3_static PRIVATE SQLITE_ENABLE_FTS5 SQLITE_THREADSAFE=1 SQLITE_OMIT_LOAD_EXTENSION)

set(KR_SOURCES
    src/image_quality.cpp
    src/severity.cpp
    src/disease_classifier.cpp
    src/pest_detector.cpp
    src/knowledge_base.cpp
    src/output_guard.cpp
    src/pipeline.cpp
)

add_library(krishirakshak_core STATIC ${KR_SOURCES})
target_include_directories(krishirakshak_core PUBLIC src ${ORT_ROOT}/include ${OpenCV_INCLUDE_DIRS} ${THIRD_PARTY_SRC})
target_link_directories(krishirakshak_core PUBLIC ${ORT_ROOT}/lib)
target_link_libraries(krishirakshak_core PUBLIC onnxruntime ${OpenCV_LIBS} sqlite3_static pthread dl)

if(EXECUTORCH_ROOT)
    # Llama 3.2 1B through the ExecuTorch C++ LLM runner (XNNPACK backend).
    # Linking follows ExecuTorch's own examples/models/llama/CMakeLists.txt: operator and backend libraries
    # register themselves through static initialisers, so they are linked with --whole-archive
    # (executorch_target_link_options_shared_lib); otherwise loading the .pte fails with "missing operator".
    target_sources(krishirakshak_core PRIVATE src/llama_advisor.cpp)
    target_compile_definitions(krishirakshak_core PUBLIC KR_WITH_LLM)
    list(APPEND CMAKE_PREFIX_PATH ${EXECUTORCH_ROOT} ${EXECUTORCH_ROOT}/lib/cmake/ExecuTorch)
    # executorch-config.cmake also loads the tokenizers package (tokenizers::tokenizers); a second
    # find_package(tokenizers) would fail because its targets already exist.
    find_package(executorch CONFIG REQUIRED FIND_ROOT_PATH_BOTH)
    # Most installed (imported) ExecuTorch targets that register kernels or the XNNPACK delegate already carry
    # --whole-archive in their interface link options (executorch, optimized_native_cpu_ops_lib, quantized_ops_lib,
    # xnnpack_backend); wrapping them again would link them twice ("multiple definition").
    # custom_ops (llama::custom_sdpa, llama::update_cache) does not, so without WHOLE_ARCHIVE its registration
    # code is dropped and loading the .pte fails with "Missing operator: llama::update_cache.out".
    if(CMAKE_VERSION VERSION_LESS 3.24)
        message(FATAL_ERROR "The Llama build needs CMake >= 3.24 (WHOLE_ARCHIVE link feature)")
    endif()
    target_link_libraries(krishirakshak_core PUBLIC "$<LINK_LIBRARY:WHOLE_ARCHIVE,custom_ops>")
    set(KR_ET_LIBS executorch optimized_native_cpu_ops_lib quantized_ops_lib xnnpack_backend
        extension_llm_runner extension_module_static extension_data_loader extension_tensor extension_flat_tensor
        extension_threadpool tokenizers::tokenizers optimized_kernels quantized_kernels XNNPACK
        xnnpack-microkernels-prod
        portable_kernels)   # generic kernels the optimized ones fall back to (e.g. sum.dim_out, grid_sampler)
    if(TARGET kleidiai)                       # Arm KleidiAI micro-kernels (aarch64 build)
        list(APPEND KR_ET_LIBS kleidiai)
    endif()
    target_link_libraries(krishirakshak_core PUBLIC ${KR_ET_LIBS})
    message(STATUS "Llama advisor: ON (ExecuTorch at ${EXECUTORCH_ROOT})")
else()
    message(STATUS "Llama advisor: OFF (set EXECUTORCH_ROOT to enable)")
endif()

add_executable(krishirakshak src/main.cpp)

# Regression test of the Llama output grounding check (no models needed): build/<dir>/grounding_test <repo root>
enable_testing()
add_executable(grounding_test tests/grounding_test.cpp)
target_link_libraries(grounding_test PRIVATE krishirakshak_core)
add_test(NAME grounding COMMAND grounding_test ${CMAKE_CURRENT_SOURCE_DIR}/..)
target_link_libraries(krishirakshak PRIVATE krishirakshak_core)
# Find libonnxruntime.so next to the binary or in ./lib after deployment
set_target_properties(krishirakshak PROPERTIES BUILD_RPATH "${ORT_ROOT}/lib" INSTALL_RPATH "$ORIGIN:$ORIGIN/lib")

message(STATUS "===========================================")
message(STATUS "KrishiRakshak - build configuration")
message(STATUS "Target: ${TARGET_ARCH}   Build type: ${CMAKE_BUILD_TYPE}   C++${CMAKE_CXX_STANDARD}")
message(STATUS "ONNX Runtime: ${ORT_ROOT}")
message(STATUS "===========================================")
