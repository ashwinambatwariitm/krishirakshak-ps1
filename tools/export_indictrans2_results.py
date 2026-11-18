"""Copy evaluation artifacts to Windows and decode the ASCII review CSV."""
import argparse
import csv
import html
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = args.destination
    if target.exists():
        raise SystemExit("Destination already exists; choose a fresh directory to preserve existing results")
    target.mkdir(parents=True)
    shutil.copytree(root / "results/indictrans2", target / "results")
    shutil.copy2(root / "docs/TRANSLATION_INDICTRANS2.md", target / "TRANSLATION_INDICTRANS2.md")
    with (target / "results/review_sheet.csv").open(encoding="ascii", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["translation"] = row["translation"].encode("ascii").decode("unicode_escape")
    with (target / "review_sheet_utf8.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    # Self-contained browser preview; no servers, fonts, or network requests.
    cells = []
    for row in rows:
        cells.append("<tr>" + "".join("<td>" + html.escape(row[key]) + "</td>"
                                    for key in ["id", "language", "english", "translation"]) + "</tr>")
    quality = json.loads((target / "results/summary.json").read_text())
    speed = json.loads((target / "results/bench_summary.json").read_text())
    measurements = []
    for language, q in quality["languages"].items():
        b = speed["languages"][language]
        measurements.append("<tr>" + "".join("<td>" + html.escape(str(v)) + "</td>" for v in [
            language, round(q["reference_chrf"], 2),
            str(q["number_passed"]) + "/" + str(q["number_checked"]), q["withheld"],
            round(b["fp32_warm_median_seconds"], 3), round(b["int8_warm_median_seconds"], 3),
            round(b["fp32_int8_chrf"], 2)]) + "</tr>")
    page = ("<!doctype html><html lang=en><meta charset=utf-8><title>IndicTrans2 review</title>"
            "<style>body{font:18px sans-serif;margin:2rem}table{border-collapse:collapse}"
            "td,th{border:1px solid #aaa;padding:.7rem;vertical-align:top}"
            "td:nth-child(3),td:nth-child(4){min-width:22rem}</style>"
            "<h1>IndicTrans2 WSL review</h1><p>Unreviewed machine translations. This is a review artifact, "
            "not farmer-facing output. Check meaning, negation, quantities and farmer comprehension. "
            "Candidates withheld by automated checks remain visible here for review. "
            "Edit review_sheet_utf8.csv to record decisions.</p>"
            "<p><strong>WSL-only measurements. No Pi downloads or inference. "
            "No language is approved for farmer use.</strong> The tested PyTorch backends exceed "
            "the 600 MB peak-memory target. CTranslate2 conversion is unresolved. "
            "chrF compares unreviewed translations and does not measure correctness.</p>"
            "<h2>Measured results</h2><table><tr><th>Language</th><th>Reference chrF</th>"
            "<th>Number passes</th><th>Withheld sentences</th><th>FP32 seconds</th>"
            "<th>Dynamic INT8 seconds</th><th>FP32/INT8 chrF</th></tr>"
            + "".join(measurements) + "</table><p>Seconds are warm medians for one two-sentence "
            "late-blight answer, not the full dataset. See TRANSLATION_INDICTRANS2.md for methodology, "
            "RSS and limitations.</p><h2>Fluent-speaker review</h2><table>"
            "<tr><th>ID</th><th>Language</th><th>English</th><th>Translation</th></tr>"
            + "".join(cells) + "</table></html>")
    (target / "review.html").write_text(page, encoding="utf-8")
    print(str(target))


if __name__ == "__main__":
    main()
