"""Pest severity level for one photo, from the insects found by the pest detector.

Same rule and constants as the C++ application (cpp/src/pest_severity.cpp); see docs/SEVERITY.md.
A photo cannot measure infestation of a field: the level describes this photo only, and each result quotes the
published scouting method (NIPHM AESA-based IPM package for tomato, TNAU IPM) and, where one exists, the economic
threshold, so the farmer checks the field before deciding to spray.

Level per pest topic (project rule, not an agronomic standard):
  colony insects (aphids, whitefly, mites, thrips, leafhoppers, mealybug): 1-4 low, 5-19 moderate, 20+ high
  chewing larvae (caterpillars, fruit borer, Spodoptera, cutworm, Tuta, leaf miner): 1-2 moderate, 3+ high
  species uncertain (insect_other): colony bands
"""
import math

COLONY = {"aphids", "whitefly", "mites", "thrips", "leafhoppers", "mealybug"}
CHEWING = {"caterpillars", "helicoverpa_fruit_borer", "spodoptera_tobacco_caterpillar", "cutworm",
           "tuta_absoluta_pinworm", "serpentine_leaf_miner"}
GRID = 256


def _scouting_quote(topic, group):
    if topic == "thrips":
        return "thrips", "For thrips:"
    if topic == "serpentine_leaf_miner":
        return "serpentine_leaf_miner", "For leaf miner:"
    if group == "colony":
        return "aesa_monitoring", "For sucking pests:"
    if group == "chewing":
        return "helicoverpa_fruit_borer", "For Helicoverpa and Spodoptera:"
    return "aesa_monitoring", "select five spots randomly"


def _threshold_quote(topic):
    if topic in ("helicoverpa_fruit_borer", "caterpillars"):
        return "helicoverpa_fruit_borer", "Economic Threshold Level (ETL): 8 eggs"
    return None


def _level(group, count):
    if group == "chewing":
        return "high" if count >= 3 else "moderate"
    return "high" if count >= 20 else ("moderate" if count >= 5 else "low")


def _union_share(boxes, w, h):
    """Share of the photo covered by the union of xyxy boxes, on a 256 x 256 grid."""
    grid = [[0] * GRID for _ in range(GRID)]
    for x1, y1, x2, y2 in boxes:
        gx0, gy0 = max(0, math.floor(x1 / w * GRID)), max(0, math.floor(y1 / h * GRID))
        gx1, gy1 = min(GRID, math.ceil(x2 / w * GRID)), min(GRID, math.ceil(y2 / h * GRID))
        for y in range(gy0, gy1):
            row = grid[y]
            for x in range(gx0, gx1):
                row[x] = 1
    return sum(map(sum, grid)) / (GRID * GRID)


def _quote(kb, topic, phrase, lang):
    c = kb.find_chunk(topic, phrase, lang)
    return None if c is None else {"text": c["text"], "source_org": c["source_org"],
                                   "source_title": c["source_title"], "url": c["url"]}


def pest_severity(pests, kb, width, height, lang="en"):
    """pests: detector output with "topic" and "box_xyxy"; returns one entry per topic, most severe first."""
    by_topic = {}
    for p in pests:
        by_topic.setdefault(p["topic"], []).append(p["box_xyxy"])
    rank = {"high": 3, "moderate": 2, "low": 1}
    rows = []
    for topic in sorted(by_topic):
        boxes = by_topic[topic]
        group = "colony" if topic in COLONY else ("chewing" if topic in CHEWING else "uncertain")
        level = _level(group, len(boxes))
        thr = _threshold_quote(topic)
        rows.append({"topic": topic, "name": kb.topic_name(topic, lang), "group": group, "count": len(boxes),
                     "box_share": round(_union_share(boxes, width, height), 3), "level": level,
                     "basis": "insects_in_this_photo",
                     "scouting": _quote(kb, *_scouting_quote(topic, group), lang),
                     "threshold": _quote(kb, *thr, lang) if thr else None})
    # stable sort: same tie order as the C++ code (topics in name order, then level and count)
    rows.sort(key=lambda r: (-rank[r["level"]], -r["count"]))
    return rows
