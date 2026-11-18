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
 *   krishirakshak [options] --eval-advisor demo           Llama summary per topic without photos, scored by the
 *                                                         grounding check (demo = six diseases, or a comma list)
 * Options:
 *   --bind ADDR        address for --serve; default 0.0.0.0 (reachable over the Pi's Wi-Fi hotspot)
 *   --root DIR         repository root (models/, results/, app/kb/); default "."
 *   --lang en|hi       answer language; default en
 *   --int8 / --fp32    INT8 or FP32 ONNX vision models (default: INT8 on the Raspberry Pi build, where it is about
 *                      twice as fast with the same answers; FP32 on the development build, used by the parity test)
 *   --no-llama         vision + knowledge base only
 *   --sequential       run the two vision models one after the other (default: in parallel)
 *   --threads N        ONNX Runtime threads per vision model; default 2
 *   --llama-threads N  XNNPACK threads for Llama; default 4
 *   --llama-pte FILE   Llama model relative to --root; default models/llama3_2_1b_instruct_8da4w.pte
 *                      (e.g. models/llama3_2_3b_instruct_8da4w.pte for the 3B model; same tokenizer)
 *   --ort-spin         let ONNX Runtime threads busy-wait after each run (off by default; for A/B timing)
 *   --fact-bias X      add X to the logits of tokens that occur in the facts (Llama decoding; default 0 = off)
 *   --block-cause-words  forbid cause words (fungus, bacteria, virus...) that the facts do not contain
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
    std::cerr << "usage: krishirakshak [--root DIR] [--lang en|hi] [--int8|--fp32] [--no-llama] [--sequential] [--threads N]\n"
                 "                     [--llama-threads N] [--llama-pte FILE] [--ort-spin] [--fact-bias X]\n"
                 "                     [--block-cause-words] [--brief]\n"
                 "                     (photo ... | --list FILE | --ask QUESTION [--topic TOPIC] | --serve PORT\n"
                 "                      | --eval-advisor demo|TOPIC,TOPIC)\n";
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
    std::string lang = "en", listFile, question, topic, bindAddr = "0.0.0.0", evalTopics;
    bool briefOut = false;
    int servePort = 0;
    std::vector<std::string> photos;
#ifdef KR_DEFAULT_INT8
    bool useInt8 = true;     // Raspberry Pi build: INT8 vision 125 ms vs FP32 269 ms per photo, same diagnoses
#else
    bool useInt8 = false;
#endif

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto next = [&]() -> std::string {
            if (i + 1 >= argc) { usage(); std::exit(2); }
            return argv[++i];
        };
        if (a == "--root") cfg.repoRoot = next();
        else if (a == "--lang") lang = next();
        else if (a == "--int8") useInt8 = true;
        else if (a == "--fp32") useInt8 = false;
        else if (a == "--no-llama") cfg.useLlama = false;
        else if (a == "--sequential") cfg.parallelVision = false;
        else if (a == "--threads") cfg.visionThreads = std::stoi(next());
        else if (a == "--llama-threads") cfg.llamaThreads = std::stoi(next());
        else if (a == "--llama-pte") cfg.llamaPte = next();
        else if (a == "--ort-spin") cfg.ortSpin = true;
        else if (a == "--fact-bias") cfg.llamaFactBias = std::stof(next());
        else if (a == "--block-cause-words") cfg.llamaBlockCauseWords = true;
        else if (a == "--eval-advisor") evalTopics = next();
        else if (a == "--brief") briefOut = true;
        else if (a == "--list") listFile = next();
        else if (a == "--ask") question = next();
        else if (a == "--topic") topic = next();
        else if (a == "--serve") servePort = std::stoi(next());
        else if (a == "--bind") bindAddr = next();
        else if (a == "-h" || a == "--help") { usage(); return 0; }
        else photos.push_back(a);
    }
    if (useInt8) {
        cfg.diseaseOnnx = "models/tomato_disease_v5_effb0_6class_int8.onnx";
        cfg.pestOnnx = "models/pest_yolov8n_ip102_negatives_int8.onnx";
    }
    if (!listFile.empty()) {
        std::ifstream in(listFile);
        for (std::string line; std::getline(in, line);) if (!line.empty()) photos.push_back(line);
    }
    if (photos.empty() && question.empty() && servePort == 0 && evalTopics.empty()) { usage(); return 2; }

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
            // Streaming variant: newline-delimited JSON events ({"event": "result" | "token" | "final", ...})
            server.analyseStream = [&](const std::string& bytes, const std::string& l,
                                       const std::function<void(const std::string&)>& emit) {
                const cv::Mat img = kr::decodeImageRgb(bytes);
                const std::string useLang = (l == "hi") ? "hi" : "en";
                if (img.empty()) {
                    emit(nlohmann::json({{"event", "final"}, {"data", {{"status", "not_an_image"}, {"messages", nlohmann::json::array()}}}}).dump());
                    return;
                }
                const auto r = pipe.analyse(img, useLang, [&](const std::string& ev, const nlohmann::json& data) {
                    if (ev == "token") emit(nlohmann::json({{"event", "token"}, {"text", data["text"]}}).dump());
                    else emit(nlohmann::json({{"event", ev}, {"data", data}}).dump());
                });
                emit(nlohmann::json({{"event", "final"}, {"data", r}}).dump());
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
        if (!evalTopics.empty()) {
            // Same six demo diseases as llm/eval_advisor.py; or an explicit comma-separated list of topics
            std::vector<std::string> topics;
            if (evalTopics == "demo") {
                topics = {"healthy", "early_blight", "late_blight", "septoria_leaf_spot", "bacterial_spot",
                          "yellow_leaf_curl_virus"};
            } else {
                for (size_t s = 0; s <= evalTopics.size();) {
                    const size_t c = evalTopics.find(',', s);
                    const std::string tp = evalTopics.substr(s, c == std::string::npos ? std::string::npos : c - s);
                    if (!tp.empty()) topics.push_back(tp);
                    if (c == std::string::npos) break;
                    s = c + 1;
                }
            }
            int accepted = 0, grounded = 0, dropped = 0, evaluated = 0;
            double seconds = 0;
            for (const auto& tp : topics) {
                const auto r = pipe.evalAdvisor(tp);
                std::cout << r.dump() << "\n";
                if (!r["llama"].is_object()) continue;
                ++evaluated;
                accepted += r["llama"]["accepted"].get<bool>() ? 1 : 0;
                grounded += r["llama"]["grounded_sentences"].get<int>();
                dropped += static_cast<int>(r["llama"]["dropped_sentences"].size());
                seconds += r["llama"]["stats"].value("total_s", 0.0);
                std::cerr << tp << ": " << (r["llama"]["accepted"].get<bool>() ? "accepted" : "rejected") << ", "
                          << r["llama"]["grounded_sentences"] << " grounded, " << r["llama"]["dropped_sentences"].size()
                          << " dropped, " << r["llama"]["stats"].value("total_s", 0.0) << " s\n";
            }
            std::cout << nlohmann::json({{"summary", {{"topics", evaluated}, {"accepted", accepted},
                                                      {"grounded_sentences", grounded}, {"dropped_sentences", dropped},
                                                      {"llama_seconds", seconds}, {"config", pipe.info()}}}}).dump()
                      << "\n";
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
