/*
 * web_server.hpp - minimal embedded HTTP server for the offline farmer web page (POSIX sockets + C++ standard
 * library only, so it cross-compiles for the Raspberry Pi; same design as the road-anomaly-detection dashboard).
 *
 * The page is compiled into the binary (web_page.hpp), so deployment stays a single executable. A phone can open
 * it over the Pi's own Wi-Fi hotspot; no internet is involved.
 *
 * Endpoints:
 *   GET  /                      farmer web page: the built-in page, or index.html of the farmer app when webRoot is
 *                               set (krishirakshak --web app/web); other GET paths then serve files of that folder
 *   GET  /basic                 the built-in page (always available)
 *   OPTIONS *                   CORS pre-flight; every reply allows any origin (Android app inside the APK)
 *   GET  /api/info              JSON: models, runtime, knowledge-base version
 *   POST /api/analyse?lang=en&translate=ta   body = raw JPEG/PNG bytes of the photo -> JSON result
 *                               (translate: optional, translates the accepted English advice; hi te mr kn ta bn gu or pa)
 *   POST /api/ask               body = {"question": "...", "topic": "late_blight", "lang": "en", "translate": "ta"}
 *                               -> JSON answer
 *
 * Requests are handled on their own threads, but the application callbacks are serialised by a mutex: the
 * pipeline runs one photo at a time so each stage can use all four Cortex-A76 cores.
 */
#pragma once

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <csignal>
#include <cstdint>
#include <fstream>
#include <functional>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>

namespace web {

class Server {
public:
    // --- Callbacks wired by the application (all return JSON text) ---
    std::function<std::string()> getInfo;
    std::function<std::string(const std::string& imageBytes, const std::string& lang, const std::string& translate)>
        analyse;
    std::function<std::string(const std::string& jsonBody)> ask;
    std::function<std::string()> pageHtml;
    // Folder of the farmer web app (app/web: index.html, js/, css/, manifest, service worker). Empty: built-in page.
    std::string webRoot;

    static constexpr size_t kMaxBody = 15 * 1024 * 1024;   // 15 MB photo limit

    explicit Server(int port) : port_(port) {}
    ~Server() { stop(); }

    bool start(const std::string& bindAddress = "0.0.0.0") {
        std::signal(SIGPIPE, SIG_IGN);  // writing to a closed client must not kill the process
        listenFd_ = ::socket(AF_INET, SOCK_STREAM, 0);
        if (listenFd_ < 0) return false;
        int yes = 1;
        setsockopt(listenFd_, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(static_cast<uint16_t>(port_));
        if (::inet_pton(AF_INET, bindAddress.c_str(), &addr.sin_addr) != 1 ||
            ::bind(listenFd_, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0 || ::listen(listenFd_, 16) < 0) {
            ::close(listenFd_);
            listenFd_ = -1;
            return false;
        }
        running_ = true;
        acceptThread_ = std::thread([this] { acceptLoop(); });
        return true;
    }

    void wait() { if (acceptThread_.joinable()) acceptThread_.join(); }

    void stop() {
        if (!running_.exchange(false)) return;
        if (listenFd_ >= 0) { ::shutdown(listenFd_, SHUT_RDWR); ::close(listenFd_); listenFd_ = -1; }
        if (acceptThread_.joinable()) acceptThread_.join();
    }

private:
    int port_;
    int listenFd_ = -1;
    std::atomic<bool> running_{false};
    std::thread acceptThread_;
    std::mutex pipelineMutex_;

    static bool sendAll(int fd, const char* data, size_t len) {
        size_t sent = 0;
        while (sent < len) {
            const ssize_t n = ::send(fd, data + sent, len - sent, MSG_NOSIGNAL);
            if (n <= 0) return false;
            sent += static_cast<size_t>(n);
        }
        return true;
    }

    void acceptLoop() {
        while (running_) {
            sockaddr_in cli{};
            socklen_t cl = sizeof(cli);
            const int fd = ::accept(listenFd_, reinterpret_cast<sockaddr*>(&cli), &cl);
            if (fd < 0) { if (!running_) break; continue; }
            std::thread(&Server::handle, this, fd).detach();
        }
    }

    static std::string headerValue(const std::string& headers, const std::string& name) {
        // Case-insensitive search for "\r\nName:" in the header block
        std::string lowHeaders = headers, lowName = "\r\n" + name + ":";
        for (auto& c : lowHeaders) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        for (auto& c : lowName) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        const size_t p = lowHeaders.find(lowName);
        if (p == std::string::npos) return "";
        const size_t start = headers.find_first_not_of(' ', p + lowName.size());
        return headers.substr(start, headers.find("\r\n", start) - start);
    }

    static std::string queryParam(const std::string& query, const std::string& key, const std::string& fallback) {
        const std::string k = key + "=";
        for (size_t p = 0; p < query.size();) {
            const size_t amp = query.find('&', p);
            const std::string part = query.substr(p, amp == std::string::npos ? std::string::npos : amp - p);
            if (part.rfind(k, 0) == 0) return part.substr(k.size());
            if (amp == std::string::npos) break;
            p = amp + 1;
        }
        return fallback;
    }

    void handle(int fd) {
        // 1. Read the request line and headers
        std::string req;
        char buf[16384];
        size_t headerEnd;
        while ((headerEnd = req.find("\r\n\r\n")) == std::string::npos) {
            if (req.size() > 16384) { ::close(fd); return; }
            const ssize_t n = ::recv(fd, buf, sizeof(buf), 0);
            if (n <= 0) { ::close(fd); return; }
            req.append(buf, static_cast<size_t>(n));
        }
        const std::string headers = req.substr(0, headerEnd + 2);
        std::string body = req.substr(headerEnd + 4);

        const size_t sp1 = headers.find(' '), sp2 = headers.find(' ', sp1 + 1);
        const std::string method = headers.substr(0, sp1);
        const std::string target = headers.substr(sp1 + 1, sp2 - sp1 - 1);
        const size_t q = target.find('?');
        const std::string route = target.substr(0, q);
        const std::string query = q == std::string::npos ? "" : target.substr(q + 1);

        // 2. Read the body (Content-Length)
        const std::string cl = headerValue(headers, "Content-Length");
        const size_t contentLength = cl.empty() ? 0 : std::stoul(cl);
        if (contentLength > kMaxBody) { reply(fd, "413 Payload Too Large", "text/plain", "photo too large"); return; }
        while (body.size() < contentLength) {
            const ssize_t n = ::recv(fd, buf, sizeof(buf), 0);
            if (n <= 0) { ::close(fd); return; }
            body.append(buf, static_cast<size_t>(n));
        }

        // 3. Route
        try {
            if (method == "OPTIONS") {
                // CORS pre-flight: the Android app (page inside the APK) calls the Pi from another origin; a photo
                // POST with Content-Type image/jpeg is not a "simple" request, so the browser engine asks first
                reply(fd, "204 No Content", "text/plain", "");
            } else if (method == "GET" && (route == "/basic" ||
                                    (webRoot.empty() && (route == "/" || route == "/index.html")))) {
                reply(fd, "200 OK", "text/html; charset=utf-8", pageHtml ? pageHtml() : "");
            } else if (method == "GET" && route == "/api/info") {
                std::lock_guard<std::mutex> lock(pipelineMutex_);
                reply(fd, "200 OK", "application/json; charset=utf-8", getInfo ? getInfo() : "{}");
            } else if (method == "POST" && route == "/api/analyse") {
                std::lock_guard<std::mutex> lock(pipelineMutex_);
                reply(fd, "200 OK", "application/json; charset=utf-8",
                      analyse(body, queryParam(query, "lang", "en"), queryParam(query, "translate", "")));
            } else if (method == "POST" && route == "/api/ask") {
                std::lock_guard<std::mutex> lock(pipelineMutex_);
                reply(fd, "200 OK", "application/json; charset=utf-8", ask(body));
            } else if (method == "GET" && !webRoot.empty()) {
                serveFile(fd, route);
            } else {
                reply(fd, "404 Not Found", "text/plain", "not found");
            }
        } catch (const std::exception& e) {
            reply(fd, "500 Internal Server Error", "text/plain", e.what());
        }
    }

    // Static file of the farmer app. Only plain relative paths below webRoot are served ("..", backslashes and
    // empty path parts are refused), so a request cannot read files outside the app folder.
    void serveFile(int fd, std::string route) {
        if (route.empty() || route == "/") route = "/index.html";
        const std::string rel = route.substr(1);
        if (rel.empty() || rel.find("..") != std::string::npos || rel.find('\\') != std::string::npos ||
            rel.find("//") != std::string::npos || rel.find('\0') != std::string::npos || rel[0] == '/') {
            reply(fd, "404 Not Found", "text/plain", "not found");
            return;
        }
        std::ifstream in(webRoot + "/" + rel, std::ios::binary);
        if (!in) {
            reply(fd, "404 Not Found", "text/plain", "not found");
            return;
        }
        std::ostringstream ss;
        ss << in.rdbuf();
        reply(fd, "200 OK", contentType(rel), ss.str());
    }

    static const char* contentType(const std::string& path) {
        const auto dot = path.rfind('.');
        const std::string ext = dot == std::string::npos ? "" : path.substr(dot + 1);
        if (ext == "html") return "text/html; charset=utf-8";
        if (ext == "js") return "text/javascript; charset=utf-8";
        if (ext == "css") return "text/css; charset=utf-8";
        if (ext == "json" || ext == "webmanifest") return "application/manifest+json";
        if (ext == "svg") return "image/svg+xml";
        if (ext == "png") return "image/png";
        if (ext == "jpg" || ext == "jpeg") return "image/jpeg";
        if (ext == "ico") return "image/x-icon";
        return "application/octet-stream";
    }

    void reply(int fd, const char* status, const char* ctype, const std::string& body) {
        std::string hdr = "HTTP/1.1 " + std::string(status) + "\r\nContent-Type: " + ctype +
                          "\r\nContent-Length: " + std::to_string(body.size()) +
                          "\r\nCache-Control: no-store\r\nConnection: close"
                          // Any origin may call the API: the device is offline, on its own hotspot, and has no
                          // login or private data (the Android app is served from inside the APK)
                          "\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: GET, POST, OPTIONS"
                          "\r\nAccess-Control-Allow-Headers: Content-Type\r\n\r\n";
        if (sendAll(fd, hdr.data(), hdr.size())) sendAll(fd, body.data(), body.size());
        ::close(fd);
    }
};

}  // namespace web
