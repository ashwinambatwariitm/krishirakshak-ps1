"""Offline Flask user interface (runs on the Raspberry Pi 5 or on a PC; no internet needed).

    python -m app.server                 # http://127.0.0.1:5000
    python -m app.server --host 0.0.0.0  # reachable from a phone on the Pi's own Wi-Fi hotspot

All models are loaded once at start-up. The page uses no external CSS, fonts or scripts, so it works offline.
"""
import argparse
import base64
import io

from flask import Flask, jsonify, render_template, request

from app.pipeline.coordinator import Pipeline
from app.pipeline.quality import decode_image

app = Flask(__name__)
PIPE = None          # created in main(), shared by all requests (requests are handled one at a time)
MAX_UPLOAD_MB = 15
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html", info=PIPE.info(), result=None, lang="en")


@app.post("/analyse")
def analyse():
    """Form upload: run the pipeline and render the result page."""
    lang = request.form.get("lang", "en")
    upload = request.files.get("photo")
    data = upload.read() if upload else b""
    image = decode_image(data) if data else None
    if image is None:
        result = {"status": "retake_photo", "messages": [PIPE.kb.messages["quality"]["not_an_image"][lang]],
                  "timings_ms": {}}
        thumb = None
    else:
        result = PIPE.analyse(image, lang=lang)
        thumb = "data:image/jpeg;base64," + base64.b64encode(data).decode()
    return render_template("index.html", info=PIPE.info(), result=result, lang=lang, thumb=thumb)


@app.post("/api/analyse")
def api_analyse():
    """JSON API (for a future phone app or for testing with curl)."""
    lang = request.args.get("lang", "en")
    image = decode_image(request.get_data() or request.files["photo"].read())
    if image is None:
        return jsonify({"error": "not an image"}), 400
    return jsonify(PIPE.analyse(image, lang=lang))


@app.post("/api/ask")
def api_ask():
    """Follow-up question: {"question": "...", "topic": "late_blight", "lang": "en"} -> answer + cited extracts."""
    body = request.get_json(force=True)
    return jsonify(PIPE.follow_up(body.get("question", ""), body.get("topic"), body.get("lang", "en")))


def main():
    parser = argparse.ArgumentParser(description="KrishiRakshak offline web interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-llama", action="store_true")
    args = parser.parse_args()
    global PIPE
    PIPE = Pipeline(use_llama=not args.no_llama)
    print(f"models loaded: {PIPE.info()}")
    app.run(host=args.host, port=args.port, threaded=False)


if __name__ == "__main__":
    main()
