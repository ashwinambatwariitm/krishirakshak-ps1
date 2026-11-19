#!/usr/bin/env bash
# Builds the libraries used by the C++ translation stage (IndicTrans2 on CTranslate2), for the development
# machine (x86_64) and for the Raspberry Pi 5 (aarch64 cross build).
#
#   CTranslate2 4.6.0   - shared library, built for aarch64 exactly like the official Python wheel that was
#                         evaluated on the Pi (CTranslate2 python/tools/prepare_build_environment_linux.sh):
#                         OpenBLAS for float GEMM, Ruy for INT8 GEMM, GNU OpenMP, generic Armv8 code.
#   OpenBLAS 0.3.21     - aarch64 only (the x86 build uses the system libopenblas-dev): static, TARGET=ARMV8,
#                         same options as the wheel, linked into libctranslate2, so the Pi needs no BLAS.
#   SentencePiece 0.2.1 - static library (tokenizer of the model).
#
# Why exactly the wheel's options: floating-point results depend on the kernels (summation order). With the
# same build, the C++ translator gives word-for-word the same translations on the Pi as the evaluated Python
# runs (measured: 270/270 sentences). A build with OpenBLAS 0.3.28 TARGET=CORTEXA76 and -mcpu=cortex-a76 was
# not faster and changed 10% of the translations (beam search takes a different path on near ties).
#
# libctranslate2 is linked with -Bsymbolic: the krishirakshak binary also contains ExecuTorch, whose static
# libraries bring their own copies of C++ standard-library template code; without -Bsymbolic the dynamic
# linker makes libctranslate2 call the executable's copies instead of its own, and translation on the Pi was
# 33% slower (1.70 s vs 1.21 s median per answer, same output).
#
# The prebuilt libctranslate2 from the pip wheel cannot be used: it is a manylinux build with the pre-C++11
# std::string ABI, while this project (and ONNX Runtime / ExecuTorch) use the C++11 ABI.
#
# Usage: cpp/tools/build_translation_deps.sh [x86|arm|all]     (default: all)
# Sources are cloned into $THIRD_PARTY_SRC (default ~/third_party_src); results are installed into
#   ~/x86_libs/{ctranslate2,sentencepiece}   and   ~/arm_libs/{openblas_arm,ctranslate2_arm,sentencepiece_arm}
set -euo pipefail

WHAT=${1:-all}
SRC=${THIRD_PARTY_SRC:-$HOME/third_party_src}
JOBS=${JOBS:-$(nproc)}
TOOLCHAIN="$(cd "$(dirname "$0")/.." && pwd)/arm-toolchain.cmake"
mkdir -p "$SRC"

fetch() {   # fetch <dir> <git url> <tag>
    [ -d "$SRC/$1" ] || git clone -q --depth 1 --branch "$3" --recurse-submodules --shallow-submodules "$2" "$SRC/$1"
}
fetch ctranslate2 https://github.com/OpenNMT/CTranslate2.git v4.6.0
fetch sentencepiece https://github.com/google/sentencepiece.git v0.2.1

# Options shared by both CTranslate2 builds: no MKL/CUDA, OpenBLAS + Ruy, GNU OpenMP, library only.
CT2_OPTS=(-DCMAKE_BUILD_TYPE=Release -DWITH_MKL=OFF -DWITH_DNNL=OFF -DWITH_CUDA=OFF -DWITH_OPENBLAS=ON
          -DWITH_RUY=ON -DOPENMP_RUNTIME=COMP -DBUILD_CLI=OFF -DBUILD_TESTS=OFF
          -DCMAKE_SHARED_LINKER_FLAGS=-Wl,-Bsymbolic)
SPM_OPTS=(-DCMAKE_BUILD_TYPE=Release -DSPM_ENABLE_SHARED=OFF -DSPM_ENABLE_TCMALLOC=OFF
          -DCMAKE_POSITION_INDEPENDENT_CODE=ON)

build_x86() {
    cmake -S "$SRC/ctranslate2" -B "$SRC/ctranslate2/build-x86" "${CT2_OPTS[@]}" \
          -DCMAKE_INSTALL_PREFIX="$HOME/x86_libs/ctranslate2"
    cmake --build "$SRC/ctranslate2/build-x86" -j "$JOBS" --target install
    cmake -S "$SRC/sentencepiece" -B "$SRC/sentencepiece/build-x86" "${SPM_OPTS[@]}" \
          -DCMAKE_INSTALL_PREFIX="$HOME/x86_libs/sentencepiece"
    cmake --build "$SRC/sentencepiece/build-x86" -j "$JOBS" --target install
}

build_arm() {
    local blas="$HOME/arm_libs/openblas_arm"
    if [ ! -f "$blas/lib/libopenblas.a" ]; then
        [ -d "$SRC/OpenBLAS-0.3.21" ] || curl -sL https://github.com/OpenMathLib/OpenBLAS/releases/download/v0.3.21/OpenBLAS-0.3.21.tar.gz | tar xz -C "$SRC"
        # Options of the CTranslate2 wheel build: static, OpenMP-threaded, single precision, CBLAS only.
        local opts=(TARGET=ARMV8 NO_SHARED=1 BUILD_SINGLE=1 NO_LAPACK=1 ONLY_CBLAS=1 USE_OPENMP=1 NOFORTRAN=1
                    NUM_THREADS=32 NUM_PARALLEL=8)
        make -C "$SRC/OpenBLAS-0.3.21" -j "$JOBS" "${opts[@]}" CC=aarch64-linux-gnu-gcc HOSTCC=gcc libs
        make -C "$SRC/OpenBLAS-0.3.21" PREFIX="$blas" "${opts[@]}" install
    fi
    # The cross toolchain only searches the target sysroot, so OpenBLAS is given by full path.
    # No -mcpu flag: generic Armv8 code, as in the wheel (CPU-specific kernels are chosen at run time).
    cmake -S "$SRC/ctranslate2" -B "$SRC/ctranslate2/build-arm" "${CT2_OPTS[@]}" \
          -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" \
          -DOPENBLAS_INCLUDE_DIR="$blas/include" -DOPENBLAS_LIBRARY="$blas/lib/libopenblas.a" \
          -DCMAKE_INSTALL_PREFIX="$HOME/arm_libs/ctranslate2_arm"
    cmake --build "$SRC/ctranslate2/build-arm" -j "$JOBS" --target install
    cmake -S "$SRC/sentencepiece" -B "$SRC/sentencepiece/build-arm" "${SPM_OPTS[@]}" \
          -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DCMAKE_CXX_FLAGS="-mcpu=cortex-a76" \
          -DCMAKE_INSTALL_PREFIX="$HOME/arm_libs/sentencepiece_arm"
    cmake --build "$SRC/sentencepiece/build-arm" -j "$JOBS" --target install
}

case "$WHAT" in
    x86) build_x86 ;;
    arm) build_arm ;;
    all) build_x86; build_arm ;;
    *) echo "usage: $0 [x86|arm|all]"; exit 2 ;;
esac
echo "translation dependencies built: $WHAT"
