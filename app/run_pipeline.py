"""Command-line runner for the offline pipeline (useful on WSL and over SSH on the Raspberry Pi).

Usage:
    python -m app.run_pipeline leaf.jpg                      # English, Llama if the .pte is present
    python -m app.run_pipeline leaf.jpg --lang hi --json out.json
    python -m app.run_pipeline leaf.jpg --no-llama           # vision + knowledge base only
    python -m app.run_pipeline leaf.jpg --ask "when can I harvest after spraying"
"""
import argparse
import json
from pathlib import Path

from app.pipeline.coordinator import Pipeline
from app.pipeline.quality import decode_image


def print_result(result):
    """Readable summary of one result dictionary."""
    print(f"status: {result['status']}")
    for m in result.get("messages", []):
        print(f"  note: {m}")
    d = result.get("disease")
    if d:
        top = ", ".join(f"{t['class']} {t['probability']:.0%}" for t in d["top"])
        print(f"disease: {d['name'] or 'uncertain'}   (top-3: {top})")
    if result.get("severity"):
        print(f"estimated severity: {result['severity']}")
    for p in result.get("pests", []):
        print(f"pest: {p['name']} ({p['species']}, conf {p['confidence']:.2f}, reliable={p['species_reliable']})")
    for block in result.get("advice_blocks", []):
        print(f"\n== {block['name']}")
        for c in block["chunks"]:
            body = f"{c['product']} @ {c['dose']}" if c["section"] == "chemical" else c["text"]
            print(f"  [{c['section']}] {body}   ({c['source_org']})")
    if result.get("llama"):
        ll = result["llama"]
        print(f"\nLlama ({'accepted' if ll['accepted'] else 'REJECTED ' + str(ll['rejected_reasons'])}): "
              f"{ll['raw_text']}\n  stats: {ll['stats']}")
    print(f"\ntimings (ms): {result['timings_ms']}")


def main():
    parser = argparse.ArgumentParser(description="KrishiRakshak offline pipeline")
    parser.add_argument("image")
    parser.add_argument("--lang", choices=["en", "hi"], default="en")
    parser.add_argument("--no-llama", action="store_true")
    parser.add_argument("--int8", action="store_true", help="use the INT8 ONNX vision models")
    parser.add_argument("--ask", help="also answer this follow-up question")
    parser.add_argument("--json", help="write the full result to this file")
    args = parser.parse_args()

    overrides = {"use_llama": not args.no_llama}
    if args.int8:
        from app.pipeline.coordinator import DEFAULT_CONFIG
        overrides["disease_onnx"] = DEFAULT_CONFIG["disease_onnx"].with_name("tomato_disease_v5_effb0_6class_int8.onnx")
        overrides["pest_onnx"] = DEFAULT_CONFIG["pest_onnx"].with_name("pest_yolov8n_ip102_negatives_int8.onnx")
    pipe = Pipeline(**overrides)
    print(f"loaded: {pipe.info()}\n")

    image = decode_image(Path(args.image).read_bytes())
    if image is None:
        raise SystemExit("not an image")
    result = pipe.analyse(image, lang=args.lang)
    print_result(result)
    if args.ask:
        topic = (result.get("disease") or {}).get("topic")
        print(f"\nfollow-up: {json.dumps(pipe.follow_up(args.ask, topic, args.lang), ensure_ascii=False, indent=1)}")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
