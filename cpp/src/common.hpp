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

// Raspberry Pi CPU temperature in degrees Celsius from sysfs (as in the road anomaly detection project);
// -1 when the sensor is not available (for example on a laptop without that file).
inline double readCpuTempC() {
    std::ifstream in("/sys/class/thermal/thermal_zone0/temp");
    long milliC = 0;
    return (in >> milliC) ? milliC / 1000.0 : -1.0;
}

// Current clock of CPU 0 in MHz (the Pi 5 runs at 2400 MHz and lowers it when it throttles); -1 if unavailable.
inline double readCpuFreqMhz() {
    std::ifstream in("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq");
    long khz = 0;
    return (in >> khz) ? khz / 1000.0 : -1.0;
}

}  // namespace kr
