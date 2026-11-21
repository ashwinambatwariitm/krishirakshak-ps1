/*
 * KrishiRakshak - offline crop disease and pest advisor (Bharat AI-SoC Challenge 2026-27, PS1)
 *
 * demo_log.hpp - one short log line per pipeline step (each model's input, output and time), for the live demo.
 *
 * Switched at build time with the macro KR_DEMO_LOGS (CMake option of the same name, default ON):
 *   cmake -DKR_DEMO_LOGS=OFF ...   -> KR_DEMO_LOG(...) compiles to nothing; its text is not even built
 * When on, every line is
 *   - written to stderr ("[demo] +  118.2 ms leaf_check  ..."), so `journalctl -u krishirakshak -f` shows it live;
 *   - returned in the reply as "demo_log": [{"ms", "stage", "text"}], which app/web/demo.html prints.
 */
#pragma once

#include "common.hpp"
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

#ifndef KR_DEMO_LOGS
#define KR_DEMO_LOGS 1
#endif

namespace kr {

// printf-style formatting into a std::string (for the demo lines)
inline std::string strf(const char* fmt, ...) {
    char buf[512];
    va_list args;
    va_start(args, fmt);
    std::vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    return buf;
}

// Lines of one request, with the time since the request started
class DemoLog {
public:
    void add(const char* stage, const std::string& text) {
        const double ms = timer_.ms();
        lines_.push_back({{"ms", std::round(ms * 10) / 10}, {"stage", stage}, {"text", text}});
        std::fprintf(stderr, "[demo] +%8.1f ms %-12s %s\n", ms, stage, text.c_str());
        std::fflush(stderr);
    }
    const nlohmann::json& json() const { return lines_; }

private:
    Timer timer_;
    nlohmann::json lines_ = nlohmann::json::array();
};

}  // namespace kr

#if KR_DEMO_LOGS
#define KR_DEMO_LOG(log, stage, text) (log).add(stage, text)
#else
#define KR_DEMO_LOG(log, stage, text) \
    do {                              \
    } while (0)
#endif
