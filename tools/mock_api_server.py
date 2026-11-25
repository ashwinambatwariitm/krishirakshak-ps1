"""Mock of the KrishiRakshak device API for app development without a Raspberry Pi.

Serves the same three calls as the C++ server on the Pi (krishirakshak --serve), answering with the saved example
responses in docs/api_examples/ (see docs/APP_API.md). The photo sent to /api/analyse is ignored; choose the
example with the query parameter "example" (default: early blight). A delay imitates the time the Pi needs.
Also serves the static web interface directly from app/web/ so opening http://localhost:8080/ in your browser
opens the full farmer app immediately.

Usage:
    python tools/mock_api_server.py                    # http://localhost:8080
    python tools/mock_api_server.py --port 9000 --delay 0
    curl --data-binary @leaf.jpg "http://localhost:8080/api/analyse?lang=en&example=uncertain"

Examples (real answers of the Pi, see docs/api_examples/): early_blight (default), healthy, pest, not_tomato,
uncertain, retake. With a "translate" parameter the Marathi early-blight answer is used.
Only the Python standard library is needed. CORS is allowed for any origin, so a web app on another port can call it.
"""
import argparse
import json
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_DIR / "app" / "web"
EXAMPLES = ROOT_DIR / "docs" / "api_examples"

ANALYSE = {
    "early_blight": "analyse_en_early_blight.json",
    "healthy": "analyse_en_healthy_leaf.json",
    "pest": "analyse_en_pest_aphids.json",
    "not_tomato": "analyse_en_not_tomato.json",
    "uncertain": "analyse_en_uncertain.json",
    "retake": "analyse_en_retake_photo.json",
    "translated": "analyse_mr_early_blight.json"
}


class Handler(SimpleHTTPRequestHandler):
    delay = 2.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def send_json(self, path):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # CORS preflight from a web app on another origin
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/info":
            self.send_json(EXAMPLES / "info.json")
        else:
            super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        self.rfile.read(int(self.headers.get("Content-Length", 0)))   # photo or question, not used by the mock
        if self.delay > 0:
            time.sleep(self.delay)
        if url.path == "/api/analyse":
            name = "translated" if query.get("translate", [""])[0] else query.get("example", ["early_blight"])[0]
            self.send_json(EXAMPLES / ANALYSE.get(name, ANALYSE["early_blight"]))
        elif url.path == "/api/ask":
            self.send_json(EXAMPLES / "ask_en_harvest_after_spraying.json")
        else:
            self.send_error(404)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--delay", type=float, default=2.0, help="seconds before answering (the Pi: median 8.4 s with Llama and translation)")
    args = parser.parse_args()
    Handler.delay = args.delay
    print(f"mock KrishiRakshak API on http://localhost:{args.port}/  (examples from {EXAMPLES})")
    print(f"  - Static web app served from {WEB_DIR}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
