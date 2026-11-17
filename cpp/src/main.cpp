/*
 * KrishiRakshak - offline crop disease and pest advisor
 * Bharat AI-SoC Challenge 2026-27, Problem Statement 1: Offline crop-disease/pest detection and advisory for farmers
 *
 * Everything below runs on the device (Raspberry Pi 5, four Cortex-A76 cores), with no internet connection:
 *   - ONNX Runtime (C++ API): tomato disease classifier (EfficientNet-B0) and insect pest detector (YOLOv8n)
 *   - OpenCV: photo decoding, quality gate, estimated severity
 *   - SQLite + FTS5 (compiled in): verified advice extracts from ICAR, NIPHM and TNAU publications
 *   - ExecuTorch (C++ runtime, XNNPACK): Llama 3.2 1B Instruct, 4-bit weights, explains the verified advice
 *
 * Usage:
 *   krishirakshak [options] photo.jpg [photo2.jpg ...]     analyse photos, print the result as JSON (one per line)
 *   krishirakshak [options] --list files.txt              same, photo paths read from a file (parity tests)
 *   krishirakshak [options] --ask "question" --topic late_blight
 *   krishirakshak [options] --serve 8080                  farmer web page at http://<pi-ip>:8080/
 * Options:
 *   --bind ADDR        address for --serve; default 0.0.0.0 (reachable over the Pi's Wi-Fi hotspot)
 *   --root DIR         repository root (models/, results/, app/kb/); default "."
 *   --lang en|hi       answer language; default en
 *   --int8             use the INT8 ONNX vision models
 *   --no-llama         vision + knowledge base only
 *   --sequential       run the two vision models one after the other (default: in parallel)
 *   --threads N        ONNX Runtime threads per vision model; default 2
 *   --llama-threads N  XNNPACK threads for Llama; default 4
 *   --ort-spin         let ONNX Runtime threads busy-wait after each run (off by default; for A/B timing)
 *   --no-prefix-cache  prefill the whole Llama prompt on every request (for A/B timing)
 *   --brief            print only the fields used by the parity test
 */
#include "common.hpp"
#include "image_quality.hpp"
#include "pipeline.hpp"
#include "web_page.hpp"
#include "web_server.hpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

void usage() {
    std::cerr << "usage: krishirakshak [--root DIR] [--lang en|hi] [--int8] [--no-llama] [--sequential] [--threads N]\n"
                 "                     [--llama-threads N] [--ort-spin] [--no-prefix-cache] [--brief]\n"
                 "                     (photo ... | --list FILE | --ask QUESTION [--topic TOPIC])\n";
}

// Reduced result for the parity test against the Python reference (tools/cpp_parity.py)
nlohmann::json brief(const std::string& path, const nlohmann::json& r) {
    nlohmann::json b = {{"image", path}, {"status", r["status"]}};
    if (r.contains("disease")) b["disease"] = r["disease"]["top"];
    if (r.contains("pests")) {
        b["pests"] = nlohmann::json::array();
        for (const auto& p : r["pests"]) b["pests"].push_back({{"species_id", p["species_id"]}, {"confidence", p["confidence"]}, {"box_xyxy", p["box_xyxy"]}});
    }
    if (r.contains("severity")) b["severity"] = r["severity"];
    b["quality"] = r["quality"];
    b["timings_ms"] = r["timings_ms"];
    return b;
}

}  // namespace

int main(int argc, char** argv) {
    kr::PipelineConfig cfg;
    std::string lang = "en", listFile, question, topic, bindAddr = "0.0.0.0";
    bool briefOut = false;
    int servePort = 0;
    std::vector<std::string> photos;

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto next = [&]() -> std::string {
            if (i + 1 >= argc) { usage(); std::exit(2); }
            return argv[++i];
        };
        if (a == "--root") cfg.repoRoot = next();
        else if (a == "--lang") lang = next();
        else if (a == "--int8") {
            cfg.diseaseOnnx = "models/tomato_disease_v5_effb0_6class_int8.onnx";
            cfg.pestOnnx = "models/pest_yolov8n_ip102_negatives_int8.onnx";
        }
        else if (a == "--no-llama") cfg.useLlama = false;
        else if (a == "--sequential") cfg.parallelVision = false;
        else if (a == "--threads") cfg.visionThreads = std::stoi(next());
        else if (a == "--llama-threads") cfg.llamaThreads = std::stoi(next());
        else if (a == "--ort-spin") cfg.ortSpin = true;
        else if (a == "--no-prefix-cache") cfg.llamaPrefixCache = false;
        else if (a == "--brief") briefOut = true;
        else if (a == "--list") listFile = next();
        else if (a == "--ask") question = next();
        else if (a == "--topic") topic = next();
        else if (a == "--serve") servePort = std::stoi(next());
        else if (a == "--bind") bindAddr = next();
        else if (a == "-h" || a == "--help") { usage(); return 0; }
        else photos.push_back(a);
    }
    if (!listFile.empty()) {
        std::ifstream in(listFile);
        for (std::string line; std::getline(in, line);) if (!line.empty()) photos.push_back(line);
    }
    if (photos.empty() && question.empty() && servePort == 0) { usage(); return 2; }

    try {
        kr::Pipeline pipe(cfg);
        std::cerr << "loaded: " << pipe.info().dump() << "\n";
        if (servePort > 0) {
            web::Server server(servePort);
            server.pageHtml = [] { return web::farmerPageHtml(); };
            server.getInfo = [&] { return pipe.info().dump(); };
            server.analyse = [&](const std::string& bytes, const std::string& l) {
                const cv::Mat img = kr::decodeImageRgb(bytes);
                const std::string useLang = (l == "hi") ? "hi" : "en";
                if (img.empty()) return nlohmann::json({{"status", "not_an_image"}, {"messages", nlohmann::json::array()}}).dump();
                return pipe.analyse(img, useLang).dump();
            };
            server.ask = [&](const std::string& body) {
                const auto j = nlohmann::json::parse(body);
                const std::string t = j.contains("topic") && j["topic"].is_string() ? j["topic"].get<std::string>() : "";
                return pipe.followUp(j.value("question", ""), t, j.value("lang", "en")).dump();
            };
            if (!server.start(bindAddr)) { std::cerr << "cannot listen on port " << servePort << "\n"; return 1; }
            std::cerr << "serving on http://" << bindAddr << ":" << servePort << "/\n";
            server.wait();
            return 0;
        }
        if (!question.empty()) {
            std::cout << pipe.followUp(question, topic, lang).dump(1) << "\n";
            return 0;
        }
        for (const auto& path : photos) {
            cv::Mat img;
            try { img = kr::decodeImageRgb(kr::readFile(path)); } catch (const std::exception&) {}
            if (img.empty()) {
                std::cout << nlohmann::json({{"image", path}, {"error", "not an image"}}).dump() << "\n";
                continue;
            }
            const auto r = pipe.analyse(img, lang);
            std::cout << (briefOut ? brief(path, r).dump() : r.dump(1)) << "\n";
        }
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
