"""Mock of the KrishiRakshak device API and static web app for laptop use without a Raspberry Pi.

Serves the same three calls as the C++ server on the Pi (krishirakshak --serve), answering with the saved example
responses in docs/api_examples/ (see docs/APP_API.md). Also serves the static web interface directly from app/web/
so opening http://localhost:8080/ in your browser opens the full farmer app immediately.

Usage:
    python tools/mock_api_server.py                    # http://localhost:8080
    python tools/mock_api_server.py --port 8080 --delay 1.0

Examples: early_blight (default), healthy, hindi, uncertain, retake, pest.
Only the Python standard library is needed.
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
    "hindi": "analyse_hi_late_blight.json",
    "uncertain": "analyse_en_uncertain.json",
    "retake": "analyse_en_retake_photo.json",
    "pest": "analyse_en_pest_CONSTRUCTED.json"
}


class Handler(SimpleHTTPRequestHandler):
    delay = 1.5

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

    def do_OPTIONS(self):
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
            # Serve static files from app/web/ (index.html, css, js, assets)
            super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.delay > 0:
            time.sleep(self.delay)

        if url.path == "/api/analyse":
            name = "hindi" if query.get("lang", ["en"])[0] == "hi" else query.get("example", ["early_blight"])[0]
            self.send_json(EXAMPLES / ANALYSE.get(name, ANALYSE["early_blight"]))
        elif url.path == "/api/ask":
            self.send_json(EXAMPLES / "ask_en_harvest_after_spraying.json")
        else:
            self.send_error(404)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--delay", type=float, default=1.5, help="seconds before answering (imitates Pi inference time)")
    args = parser.parse_args()
    Handler.delay = args.delay
    print(f"KrishiRakshak App & API running at: http://localhost:{args.port}/")
    print(f"  • Static web interface: {WEB_DIR}")
    print(f"  • API mock examples:    {EXAMPLES}")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
