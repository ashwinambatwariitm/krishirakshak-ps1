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
#   CT2_ROOT, SPM_ROOT  CTranslate2 4.6.0 and SentencePiece 0.2.1 installs (cpp/tools/build_translation_deps.sh);
#                     when both are found, the IndicTrans2 translator is compiled in (KR_WITH_TRANSLATION)
cmake_minimum_required(VERSION 3.16)
project(KrishiRakshak VERSION 0.1 LANGUAGES C CXX)
# find_package(executorch) may also use EXECUTORCH_ROOT as a search prefix (CMake >= 3.27); it is the install prefix
if(POLICY CMP0144)
    cmake_policy(SET CMP0144 NEW)
endif()

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
    set(CT2_ROOT "$ENV{HOME}/arm_libs/ctranslate2_arm" CACHE PATH "CTranslate2 for aarch64")
    set(SPM_ROOT "$ENV{HOME}/arm_libs/sentencepiece_arm" CACHE PATH "SentencePiece for aarch64")
    # Libraries of the Pi's own OS are resolved at run time on the Pi (same approach as road-anomaly-detection)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--allow-shlib-undefined -Wl,--unresolved-symbols=ignore-in-shared-libs")
else()
    message(STATUS "Native build (development machine)")
    set(TARGET_ARCH "native")
    set(ORT_ROOT "$ENV{HOME}/x86_libs/onnxruntime-linux-x64-1.23.2" CACHE PATH "ONNX Runtime")
    find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
    set(CT2_ROOT "$ENV{HOME}/x86_libs/ctranslate2" CACHE PATH "CTranslate2")
    set(SPM_ROOT "$ENV{HOME}/x86_libs/sentencepiece" CACHE PATH "SentencePiece")
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
    src/pest_severity.cpp
    src/knowledge_base.cpp
    src/output_guard.cpp
    src/pipeline.cpp
    src/indic_text.cpp      # IndicTrans2 text pre/post-processing (no dependencies; tested without the model)
)

add_library(krishirakshak_core STATIC ${KR_SOURCES})
target_include_directories(krishirakshak_core PUBLIC src)
# Demo log (src/demo_log.hpp): one line per model per photo on stderr and in the reply ("demo_log").
# Off: cmake -DKR_DEMO_LOGS=OFF (the KR_DEMO_LOG macro then compiles to nothing).
option(KR_DEMO_LOGS "Per-model demo log lines (stderr and reply)" ON)
target_compile_definitions(krishirakshak_core PUBLIC KR_DEMO_LOGS=$<BOOL:${KR_DEMO_LOGS}>)
# Third-party headers as system headers: with ExecuTorch, Abseil raises the language level to C++20 and GCC then
# warns about code inside the OpenCV 4.10 headers (166 warnings on the ARM build, none in project code)
target_include_directories(krishirakshak_core SYSTEM PUBLIC ${ORT_ROOT}/include ${OpenCV_INCLUDE_DIRS} ${THIRD_PARTY_SRC})
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
    # The cross toolchain restricts package search to the target sysroot (CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY),
    # which hides the ExecuTorch install and the packages it depends on (tokenizers, absl, re2, KleidiAI, ...).
    # Point every package config in the install at its folder explicitly.
    file(GLOB KR_ET_PKG_DIRS LIST_DIRECTORIES true "${EXECUTORCH_ROOT}/lib/cmake/*")
    foreach(dir ${KR_ET_PKG_DIRS})
        file(GLOB cfg "${dir}/*[Cc]onfig.cmake")
        foreach(f ${cfg})
            get_filename_component(name "${f}" NAME)
            string(REGEX REPLACE "(-config|Config)\\.cmake$" "" name "${name}")
            set(${name}_DIR "${dir}")
        endforeach()
    endforeach()
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

# IndicTrans2 translation (English -> 9 Indian languages) on the CTranslate2 C++ runtime. libctranslate2 is a shared
# library (OpenBLAS + Ruy + GNU OpenMP compiled in); SentencePiece is linked statically.
set(KR_WITH_TRANSLATION OFF)
if(EXISTS "${CT2_ROOT}/include/ctranslate2/translator.h" AND EXISTS "${SPM_ROOT}/lib/libsentencepiece.a")
    set(KR_WITH_TRANSLATION ON)
    target_sources(krishirakshak_core PRIVATE src/translator.cpp)
    target_compile_definitions(krishirakshak_core PUBLIC KR_WITH_TRANSLATION)
    target_include_directories(krishirakshak_core SYSTEM PUBLIC ${CT2_ROOT}/include ${SPM_ROOT}/include)
    target_link_libraries(krishirakshak_core PUBLIC ${CT2_ROOT}/lib/libctranslate2.so ${SPM_ROOT}/lib/libsentencepiece.a)
    message(STATUS "Translator: ON (CTranslate2 at ${CT2_ROOT})")
else()
    message(STATUS "Translator: OFF (run cpp/tools/build_translation_deps.sh, or set CT2_ROOT and SPM_ROOT)")
endif()

add_executable(krishirakshak src/main.cpp)
if(CMAKE_CROSSCOMPILING)
    # Measured on the Pi 5: INT8 vision 125 ms vs FP32 269 ms per photo with the same diagnoses (--fp32 overrides)
    target_compile_definitions(krishirakshak PRIVATE KR_DEFAULT_INT8)
endif()

# Memory bandwidth benchmark (no dependencies); its result feeds tools/perf_model.py
add_executable(membw tools/membw.cpp)
target_link_libraries(membw PRIVATE pthread)

# Regression test of the Llama output grounding check (no models needed): build/<dir>/grounding_test <repo root>
enable_testing()
add_executable(grounding_test tests/grounding_test.cpp)
target_link_libraries(grounding_test PRIVATE krishirakshak_core)
add_test(NAME grounding COMMAND grounding_test ${CMAKE_CURRENT_SOURCE_DIR}/..)
# Parity test of the IndicTrans2 text processing against the Python reference (no model needed)
# Per-photo pest severity rule on constructed detections, with the real knowledge base
add_executable(pest_severity_test tests/pest_severity_test.cpp)
target_link_libraries(pest_severity_test PRIVATE krishirakshak_core)
add_test(NAME pest_severity COMMAND pest_severity_test ${CMAKE_CURRENT_SOURCE_DIR}/..)
add_executable(indic_text_test tests/indic_text_test.cpp)
target_link_libraries(indic_text_test PRIVATE krishirakshak_core)
add_test(NAME indic_text COMMAND indic_text_test ${CMAKE_CURRENT_SOURCE_DIR}/..)
if(KR_WITH_TRANSLATION)
    # Timing / parity run of the translator on saved Llama answers
    add_executable(translate_bench tools/translate_bench.cpp)
    target_link_libraries(translate_bench PRIVATE krishirakshak_core)
endif()
target_link_libraries(krishirakshak PRIVATE krishirakshak_core)
# Library search path: on the development machine the ONNX Runtime folder; on the Pi the lib/ folder next to the
# binary (cpp/package_pi.sh puts libonnxruntime there; OpenCV comes from the Pi's own apt packages)
set(KR_BINARIES krishirakshak grounding_test indic_text_test pest_severity_test)
if(KR_WITH_TRANSLATION)
    list(APPEND KR_BINARIES translate_bench)
endif()
if(CMAKE_CROSSCOMPILING)
    set_target_properties(${KR_BINARIES} PROPERTIES BUILD_RPATH "\$ORIGIN/lib" INSTALL_RPATH "\$ORIGIN/lib")
else()
    set_target_properties(${KR_BINARIES} PROPERTIES BUILD_RPATH "${ORT_ROOT}/lib;${CT2_ROOT}/lib"
                          INSTALL_RPATH "\$ORIGIN/lib")
endif()

message(STATUS "===========================================")
message(STATUS "KrishiRakshak - build configuration")
message(STATUS "Target: ${TARGET_ARCH}   Build type: ${CMAKE_BUILD_TYPE}   C++${CMAKE_CXX_STANDARD}")
message(STATUS "ONNX Runtime: ${ORT_ROOT}")
message(STATUS "===========================================")
