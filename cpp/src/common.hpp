/*
 * KrishiRakshak - offline crop disease and pest advisor (Bharat AI-SoC Challenge 2026-27, PS1)
 *
 * common.hpp - small shared helpers: wall-clock timer and file reading.
 */
#pragma once

#include <chrono>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace kr {

// Measures elapsed wall-clock time in milliseconds (steady clock, unaffected by clock changes).
class Timer {
public:
    Timer() : start_(std::chrono::steady_clock::now()) {}
    double ms() const {
        return std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start_).count();
    }
    void reset() { start_ = std::chrono::steady_clock::now(); }

private:
    std::chrono::steady_clock::time_point start_;
};

// Reads a whole file into a string; throws with the path in the message if it cannot be opened.
inline std::string readFile(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open " + path);
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

}  // namespace kr
