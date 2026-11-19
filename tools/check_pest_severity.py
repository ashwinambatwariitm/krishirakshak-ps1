"""Check the Python per-photo pest severity rule (app/pipeline/pest_severity.py) on the same constructed cases as the
C++ test cpp/tests/pest_severity_test.cpp, so both implementations apply the same rule.

Usage (repository root): python -m tools.check_pest_severity
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.pipeline.coordinator import DEFAULT_CONFIG  # noqa: E402
from app.pipeline.knowledge import KnowledgeBase  # noqa: E402
from app.pipeline.pest_severity import pest_severity  # noqa: E402

APHIDS, RED_SPIDER, ARMY_WORM = 24, 21, 23
FAILS = []


def expect(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok:
        FAILS.append(what)


def insects(kb, species, reliable, n, step=50.0):
    out = []
    for i in range(n):
        x, y = 10.0 + step * (i % 18), 10.0 + 60.0 * (i // 18)
        out.append({"species_id": species, "species_reliable": reliable, "confidence": 0.5,
                    "topic": kb.pest_topic(species, reliable), "box_xyxy": [x, y, x + 40.0, y + 40.0]})
    return out


def main():
    db, src = Path(DEFAULT_CONFIG["kb_db"]), Path(DEFAULT_CONFIG["kb_json"])
    if not db.exists() or db.stat().st_mtime < src.stat().st_mtime:   # same rule as the coordinator
        from app.kb.build_kb import build
        build(src, db)
    kb = KnowledgeBase(db, src)
    for n, want in [(1, "low"), (4, "low"), (5, "moderate"), (19, "moderate"), (20, "high"), (35, "high")]:
        s = pest_severity(insects(kb, APHIDS, True, n), kb, 1000, 1000)
        expect(len(s) == 1 and s[0]["topic"] == "aphids" and s[0]["level"] == want, f"{n} aphids -> {want}")
    s = pest_severity(insects(kb, RED_SPIDER, False, 6), kb, 1000, 1000)
    expect(s[0]["topic"] == "insect_other" and s[0]["group"] == "uncertain" and s[0]["level"] == "moderate",
           "6 unreliable red spider -> insect_other moderate")
    one = pest_severity(insects(kb, ARMY_WORM, True, 1), kb, 1000, 1000)
    three = pest_severity(insects(kb, ARMY_WORM, True, 3), kb, 1000, 1000)
    expect(one[0]["topic"] == "caterpillars" and one[0]["level"] == "moderate", "1 caterpillar -> moderate")
    expect(three[0]["level"] == "high", "3 caterpillars -> high")
    expect("single larva per plant" in one[0]["threshold"]["text"], "caterpillars quote the fruit-borer threshold")
    expect("number of larvae" in one[0]["scouting"]["text"], "caterpillars quote the NIPHM larvae count")
    mixed = pest_severity(insects(kb, APHIDS, True, 25) + insects(kb, RED_SPIDER, False, 2), kb, 1000, 1000)
    expect([(r["topic"], r["level"]) for r in mixed] == [("aphids", "high"), ("insect_other", "low")],
           "most severe first: aphids high, then insect_other low")
    expect("five randomly selected leaves" in mixed[0]["scouting"]["text"] and
           "NIPHM" in mixed[0]["scouting"]["source_org"], "aphids quote the NIPHM five-leaves count")
    expect(mixed[0]["threshold"] is None, "no threshold invented")
    apart = pest_severity(insects(kb, APHIDS, True, 4, 50.0), kb, 1000, 1000)[0]["box_share"]
    stacked = pest_severity(insects(kb, APHIDS, True, 4, 0.0), kb, 1000, 1000)[0]["box_share"]
    expect(apart > 3.5 * stacked and 0.001 <= stacked <= 0.003, "box share: overlapping boxes counted once")
    print("FAILED" if FAILS else "ALL PASSED")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
