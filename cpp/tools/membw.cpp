/*
 * membw.cpp - memory bandwidth of the device, the number that limits Llama's decode speed.
 *
 * Every generated token reads (almost) all Llama weights from main memory once, so
 *     tokens per second  <=  main-memory read bandwidth / weight bytes read per token.
 * tools/perf_model.py combines this measurement with the model size to predict the Llama speed and to compute how
 * close the application gets to that limit (efficiency).
 *
 * Two measurements, both with 1..N threads:
 *   read   - each thread sums its own slice of a large buffer (what a matrix-vector product does with weights)
 *   copy   - memcpy between two large buffers (read + write traffic)
 * plus a working-set sweep (single thread, read): bandwidth for buffers from 16 KB to the full size, which shows
 * the L1 / L2 / L3 / DRAM steps of the memory hierarchy (on the Pi 5: 64 KB L1D and 512 KB L2 per core, 2 MB
 * shared L3, LPDDR4X).
 *
 * Usage:  membw [--mb 256] [--threads 4] [--reps 5] [--no-sweep]      prints one JSON object on stdout
 * Build:  part of cpp/CMakeLists.txt (target membw, no dependencies), or
 *         g++ -O3 -std=c++17 -pthread cpp/tools/membw.cpp -o membw
 */
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

namespace {

using Clock = std::chrono::steady_clock;

// Sum of 64-bit words. Written as a plain loop so that -O3 vectorises it (SSE/AVX on x86, NEON on the Pi): a
// hand-unrolled scalar version stays scalar and measures the core, not the memory. The result is kept in g_sink,
// so the compiler cannot remove the loop.
uint64_t sumWords(const uint64_t* __restrict p, size_t n) {
    uint64_t a = 0;
    for (size_t i = 0; i < n; ++i) a += p[i];
    return a;
}

volatile uint64_t g_sink = 0;   // keeps results alive

// Runs fn(threadIndex) on `threads` threads, all started together; returns the wall time of the slowest in seconds.
template <typename Fn>
double timedParallel(int threads, Fn fn) {
    std::vector<std::thread> pool;
    const auto t0 = Clock::now();
    for (int t = 0; t < threads; ++t) pool.emplace_back(fn, t);
    for (auto& th : pool) th.join();
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

// Best (highest) bandwidth in GB/s (1e9 bytes) over `reps` repetitions.
double readBandwidth(const uint64_t* buf, size_t words, int threads, int reps) {
    double best = 0.0;
    for (int r = 0; r < reps; ++r) {
        std::vector<uint64_t> partial(threads, 0);
        const double s = timedParallel(threads, [&](int t) {
            const size_t chunk = words / threads;
            partial[t] = sumWords(buf + t * chunk, chunk);
        });
        for (auto v : partial) g_sink += v;
        best = std::max(best, (words / threads) * threads * sizeof(uint64_t) / s / 1e9);
    }
    return best;
}

// memcpy bandwidth counted as bytes read + bytes written.
double copyBandwidth(uint64_t* dst, const uint64_t* src, size_t words, int threads, int reps) {
    double best = 0.0;
    for (int r = 0; r < reps; ++r) {
        const double s = timedParallel(threads, [&](int t) {
            const size_t chunk = words / threads;
            std::memcpy(dst + t * chunk, src + t * chunk, chunk * sizeof(uint64_t));
        });
        g_sink += dst[words / 2];
        best = std::max(best, 2.0 * (words / threads) * threads * sizeof(uint64_t) / s / 1e9);
    }
    return best;
}

// Single-thread read bandwidth for a small working set: the same bytes are read many times, so after the first
// pass they come from the cache level the working set fits in. About 256 MB of traffic per point.
double sweepPoint(const uint64_t* buf, size_t words) {
    const size_t bytes = words * sizeof(uint64_t);
    const int passes = static_cast<int>(std::max<size_t>(4, (256u << 20) / bytes));
    g_sink += sumWords(buf, words);   // warm up
    double best = 0.0;
    for (int r = 0; r < 3; ++r) {
        uint64_t acc = 0;
        const auto t0 = Clock::now();
        for (int p = 0; p < passes; ++p) acc += sumWords(buf, words);
        const double s = std::chrono::duration<double>(Clock::now() - t0).count();
        g_sink += acc;
        best = std::max(best, static_cast<double>(bytes) * passes / s / 1e9);
    }
    return best;
}

void usage() {
    std::fprintf(stderr, "usage: membw [--mb MB] [--threads N] [--reps R] [--no-sweep]\n");
}

}  // namespace

int main(int argc, char** argv) {
    size_t mb = 256;
    int maxThreads = static_cast<int>(std::max(1u, std::thread::hardware_concurrency()));
    int reps = 5;
    bool sweep = true;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto next = [&]() -> const char* {
            if (i + 1 >= argc) { usage(); std::exit(2); }
            return argv[++i];
        };
        if (a == "--mb") mb = std::strtoul(next(), nullptr, 10);
        else if (a == "--threads") maxThreads = std::atoi(next());
        else if (a == "--reps") reps = std::atoi(next());
        else if (a == "--no-sweep") sweep = false;
        else { usage(); return a == "-h" || a == "--help" ? 0 : 2; }
    }
    if (mb < 16 || maxThreads < 1 || reps < 1) { usage(); return 2; }

    const size_t words = (mb << 20) / sizeof(uint64_t);
    std::vector<uint64_t> a(words), b(words);
    for (size_t i = 0; i < words; ++i) a[i] = i * 2654435761u;   // touch every page before timing

    std::printf("{\n  \"tool\": \"membw\",\n  \"buffer_mb\": %zu,\n  \"repetitions\": %d,\n", mb, reps);
    std::printf("  \"hardware_threads\": %u,\n", std::thread::hardware_concurrency());
    std::printf("  \"read_gbps\": {");
    for (int t = 1; t <= maxThreads; ++t)
        std::printf("%s\"%d\": %.2f", t > 1 ? ", " : "", t, readBandwidth(a.data(), words, t, reps));
    std::printf("},\n  \"copy_gbps\": {");
    for (int t = 1; t <= maxThreads; ++t)
        std::printf("%s\"%d\": %.2f", t > 1 ? ", " : "", t, copyBandwidth(b.data(), a.data(), words, t, reps));
    std::printf("}");
    if (sweep) {
        // working set (KB) -> single-thread read GB/s
        std::printf(",\n  \"sweep_read_gbps_1thread\": {");
        bool first = true;
        for (size_t kb = 16; kb <= (mb << 10); kb *= 2) {
            std::printf("%s\"%zu\": %.2f", first ? "" : ", ", kb, sweepPoint(a.data(), (kb << 10) / sizeof(uint64_t)));
            first = false;
        }
        std::printf("}");
    }
    std::printf(",\n  \"checksum\": %llu\n}\n", static_cast<unsigned long long>(g_sink % 1000));
    return 0;
}
