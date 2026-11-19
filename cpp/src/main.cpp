/*
 * KrishiRakshak - offline crop disease and pest advisor
 * Bharat AI-SoC Challenge 2026-27, Problem Statement 1: Offline crop-disease/pest detection and advisory for farmers
 *
 * Everything below runs on the device (Raspberry Pi 5, four Cortex-A76 cores), with no internet connection:
 *   - ONNX Runtime (C++ API): tomato disease classifier (EfficientNet-B0) and insect pest detector (YOLOv8n)
 *   - OpenCV: photo decoding, quality gate, estimated severity
 *   - SQLite + FTS5 (compiled in): verified advice extracts from ICAR, NIPHM and TNAU publications
 *   - ExecuTorch (C++ runtime, XNNPACK): Llama 3.2 1B Instruct, 4-bit weights, explains the verified advice
 *   - CTranslate2 (C++ API): IndicTrans2 200M, INT8, translates the checked advice into 9 Indian languages
 *
 * Usage:
 *   krishirakshak [options] photo.jpg [photo2.jpg ...]     analyse photos, print the result as JSON (one per line)
 *   krishirakshak [options] --list files.txt              same, photo paths read from a file (parity tests)
 *   krishirakshak [options] --ask "question" --topic late_blight
 *   krishirakshak [options] --serve 8080                  farmer web page at http://<pi-ip>:8080/
 *   krishirakshak [options] --eval-advisor demo           Llama summary per topic without photos, through the same
 *                                                         Llama call and checks as a photo; one JSON line per topic
 *                                                         and a summary line (demo = the six demo diseases, all = the
 *                                                         27 topics of docs/llama_1b_quality.md, or TOPIC,TOPIC)
 * Options:
 *   --bind ADDR        address for --serve; default 0.0.0.0 (reachable over the Pi's Wi-Fi hotspot)
 *   --web DIR          with --serve: serve the farmer app folder (app/web, relative to --root) at /;
 *                      the built-in page stays at /basic
 *   --root DIR         repository root (models/, results/, app/kb/); default "."
 *   --lang en|hi       answer language; default en
 *   --int8 / --fp32    INT8 or FP32 ONNX vision models (default: INT8 on the Raspberry Pi build, where it is about
 *                      twice as fast with the same answers; FP32 on the development build, used by the parity test)
 *   --no-llama         vision + knowledge base only
 *   --sequential       run the two vision models one after the other (default: in parallel)
 *   --threads N        ONNX Runtime threads per vision model; default 2
 *   --llama-threads N  XNNPACK threads for Llama; default 4
 *   --llama-pte FILE   Llama model relative to --root; default models/llama3_2_1b_krishirakshak_lora_8da4w.pte
 *                      (LoRA-tuned 1B; base model: models/llama3_2_1b_instruct_8da4w.pte)
 *                      (e.g. models/llama3_2_3b_instruct_8da4w.pte for the 3B model; same tokenizer)
 *   --translate LANG   also translate the accepted English advice into LANG (hi te mr kn ta bn gu or pa);
 *                      the web page chooses the language per request instead
 *   --no-translate     do not load the translation model
 *   --translate-threads N  CTranslate2 threads; default 2 (4 is several times slower on the Pi 5)
 *   --translate-model DIR  CTranslate2 model folder relative to --root;
 *                      default models/indictrans2_en_indic_200M_ct2_int8 (with models/indictrans2_model.SRC)
 *   --ort-spin         let ONNX Runtime threads busy-wait after each run (off by default; for A/B timing)
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
                 "                     [--llama-threads N] [--llama-pte FILE] [--ort-spin] [--brief]\n"
                 "                     [--translate LANG] [--no-translate] [--translate-threads N] [--translate-model DIR] [--web DIR]\n"
                 "                     (photo ... | --list FILE | --ask QUESTION [--topic TOPIC] | --serve PORT\n"
                 "                      | --eval-advisor demo|all|TOPIC,TOPIC)\n";
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

// --eval-advisor: one JSON line per topic (same fields as results/llama_eval/<run>/eval.jsonl, read by
// llm/summarize_eval.py) and a summary line; progress on stderr
int evalAdvisor(kr::Pipeline& pipe, const std::string& spec) {
    std::vector<std::string> topics;
    if (spec == "demo") {
        topics = {"healthy", "early_blight", "late_blight", "septoria_leaf_spot", "bacterial_spot",
                  "yellow_leaf_curl_virus"};
    } else if (spec == "all") {     // the 27 topics of the prompt evaluation (docs/llama_1b_quality.md)
        topics = {"aphids", "bacterial_canker", "bacterial_speck", "bacterial_spot", "bacterial_wilt", "collar_rot",
                  "damping_off", "early_blight", "fruit_rots", "fusarium_wilt", "grey_leaf_spot", "healthy",
                  "helicoverpa_fruit_borer", "late_blight", "mites", "powdery_mildew", "pseudocercospora_leaf_blight",
                  "root_knot_nematode", "septoria_leaf_spot", "serpentine_leaf_miner",
                  "spodoptera_tobacco_caterpillar", "thrips", "tomato_mosaic", "tomato_spotted_wilt",
                  "tuta_absoluta_pinworm", "whitefly", "yellow_leaf_curl_virus"};
    } else {
        for (size_t s = 0; s <= spec.size();) {
            const size_t c = spec.find(',', s);
            const std::string tp = spec.substr(s, c == std::string::npos ? std::string::npos : c - s);
            if (!tp.empty()) topics.push_back(tp);
            if (c == std::string::npos) break;
            s = c + 1;
        }
    }
    int evaluated = 0, accepted = 0, grounded = 0, dropped = 0;
    double seconds = 0;
    for (const auto& tp : topics) {
        const auto r = pipe.evalAdvisor(tp);
        std::cout << r.dump() << std::endl;
        if (!r["llama"].is_object()) { std::cerr << tp << ": no Llama answer\n"; continue; }
        const auto& l = r["llama"];
        ++evaluated;
        accepted += l["accepted"].get<bool>() ? 1 : 0;
        grounded += l["grounded_sentences"].get<int>();
        dropped += static_cast<int>(l["dropped_sentences"].size());
        seconds += l["stats"].value("total_s", 0.0);
        std::cerr << tp << ": " << (l["accepted"].get<bool>() ? "accepted" : "rejected") << ", "
                  << l["grounded_sentences"] << " grounded, " << l["dropped_sentences"].size() << " dropped, "
                  << l["stats"].value("total_s", 0.0) << " s\n";
    }
    std::cout << nlohmann::json({{"summary", {{"topics", evaluated}, {"accepted", accepted},
                                              {"grounded_sentences", grounded}, {"dropped_sentences", dropped},
                                              {"llama_seconds", seconds}, {"config", pipe.info()}}}}).dump()
              << std::endl;
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    kr::PipelineConfig cfg;
    std::string lang = "en", listFile, question, topic, bindAddr = "0.0.0.0", translateTo, webDir, evalTopics;
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
        else if (a == "--translate") translateTo = next();
        else if (a == "--no-translate") cfg.useTranslator = false;
        else if (a == "--translate-threads") cfg.translateThreads = std::stoi(next());
        else if (a == "--translate-model") cfg.translateModel = next();
        else if (a == "--ort-spin") cfg.ortSpin = true;
        else if (a == "--brief") briefOut = true;
        else if (a == "--list") listFile = next();
        else if (a == "--ask") question = next();
        else if (a == "--topic") topic = next();
        else if (a == "--eval-advisor") evalTopics = next();
        else if (a == "--serve") servePort = std::stoi(next());
        else if (a == "--bind") bindAddr = next();
        else if (a == "--web") webDir = next();
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
            if (!webDir.empty())
                server.webRoot = (webDir[0] == '/') ? webDir : cfg.repoRoot + "/" + webDir;
            server.getInfo = [&] { return pipe.info().dump(); };
            server.analyse = [&](const std::string& bytes, const std::string& l, const std::string& tr) {
                const cv::Mat img = kr::decodeImageRgb(bytes);
                const std::string useLang = (l == "hi") ? "hi" : "en";
                if (img.empty()) return nlohmann::json({{"status", "not_an_image"}, {"messages", nlohmann::json::array()}}).dump();
                return pipe.analyse(img, useLang, tr).dump();   // unknown translation codes are ignored
            };
            server.ask = [&](const std::string& body) {
                const auto j = nlohmann::json::parse(body);
                const std::string t = j.contains("topic") && j["topic"].is_string() ? j["topic"].get<std::string>() : "";
                const std::string tr = j.contains("translate") && j["translate"].is_string() ? j["translate"].get<std::string>() : "";
                return pipe.followUp(j.value("question", ""), t, j.value("lang", "en"), tr).dump();
            };
            if (!server.start(bindAddr)) { std::cerr << "cannot listen on port " << servePort << "\n"; return 1; }
            std::cerr << "serving on http://" << bindAddr << ":" << servePort << "/\n";
            server.wait();
            return 0;
        }
        if (!question.empty()) {
            std::cout << pipe.followUp(question, topic, lang, translateTo).dump(1) << "\n";
            return 0;
        }
        if (!evalTopics.empty()) return evalAdvisor(pipe, evalTopics);
        for (const auto& path : photos) {
            cv::Mat img;
            try { img = kr::decodeImageRgb(kr::readFile(path)); } catch (const std::exception&) {}
            if (img.empty()) {
                std::cout << nlohmann::json({{"image", path}, {"error", "not an image"}}).dump() << "\n";
                continue;
            }
            const auto r = pipe.analyse(img, lang, translateTo);
            std::cout << (briefOut ? brief(path, r).dump() : r.dump(1)) << "\n";
        }
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
