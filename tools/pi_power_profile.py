"""Power and CPU use of the KrishiRakshak application on the Raspberry Pi 5, per stage.

Reads the Pi 5 power-management IC (vcgencmd pmic_read_adc: voltage and current of each internal supply rail) and
/proc/stat about 5 times per second while it sends photos to the running application (http://127.0.0.1:8080):
  idle     - the application waits (60 s)
  vision   - photos that get no Llama text (not a tomato leaf, retake): quality check, leaf check, disease, pest
  full     - tomato disease photos with Llama advice and Marathi translation
Board power = sum of voltage x current over the PMIC rails. It covers the SoC, memory and on-board supplies, not the
USB-C supply losses, USB devices or the fan, so it is lower than a wall-plug reading.

Run on the Pi:  python3 tools/pi_power_profile.py --photos photos/testset --out results_power
"""
import argparse
import glob
import json
import os
import re
import subprocess
import threading
import time
import urllib.request

RAIL = re.compile(r"^\s*(\S+)_([AV])\s+(?:current|volt)\(\d+\)=([0-9.]+)[AV]", re.M)


def read_power():
    """Board power in W from the PMIC rails (sum of V x I for every rail that reports both)."""
    out = subprocess.run(["vcgencmd", "pmic_read_adc"], capture_output=True, text=True).stdout
    amps, volts = {}, {}
    for name, kind, val in RAIL.findall(out):
        (amps if kind == "A" else volts)[name] = float(val)
    return sum(amps[n] * volts[n] for n in amps if n in volts)


def read_cpu():
    """(busy, total) jiffies over all CPUs from /proc/stat."""
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    idle = v[3] + v[4]
    return sum(v) - idle, sum(v)


def read_temp():
    out = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True).stdout
    return float(re.findall(r"[0-9.]+", out)[0])


class Sampler(threading.Thread):
    """Samples board power, CPU use (0-100% of all 4 cores) and temperature into a list."""
    def __init__(self, period=0.2):
        super().__init__(daemon=True)
        self.period, self.rows, self.stop_flag = period, [], False

    def run(self):
        busy0, total0 = read_cpu()
        while not self.stop_flag:
            t0 = time.time()
            p = read_power()
            busy, total = read_cpu()
            cpu = 100.0 * (busy - busy0) / max(1, total - total0)
            busy0, total0 = busy, total
            self.rows.append(dict(t=t0, power_w=p, cpu_pct=cpu, temp_c=read_temp() if len(self.rows) % 10 == 0 else None))
            time.sleep(max(0.0, self.period - (time.time() - t0)))


def analyse(path, query):
    """Send one photo to the running application; returns (start, end, response json)."""
    data = open(path, "rb").read()
    req = urllib.request.Request(f"http://127.0.0.1:8080/api/analyse?{query}", data=data, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.loads(r.read())
    return t0, time.time(), res


def stats(rows, t0, t1, period=0.2):
    sel = [r for r in rows if t0 <= r["t"] <= t1]
    if len(sel) < 2:   # request shorter than the sampling period: use the samples just around it
        sel = [r for r in rows if t0 - 1.5 * period <= r["t"] <= t1 + 1.5 * period]
    if not sel:
        return dict(samples=0, seconds=round(t1 - t0, 2), power_mean_w=None, power_max_w=None, energy_j=None,
                    cpu_mean_pct=None)
    p = [r["power_w"] for r in sel]
    return dict(samples=len(sel), seconds=round(t1 - t0, 2), power_mean_w=round(sum(p) / len(p), 2),
                power_max_w=round(max(p), 2), energy_j=round(sum(p) / len(p) * (t1 - t0), 1),
                cpu_mean_pct=round(sum(r["cpu_pct"] for r in sel) / len(sel), 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--photos", default="photos/testset")
    ap.add_argument("--out", default="results_power")
    ap.add_argument("--idle", type=float, default=60)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    vision = sorted(glob.glob(f"{args.photos}/4_not_tomato/*.jpg"))
    full = sorted(glob.glob(f"{args.photos}/1_tomato_disease/*.jpg"))
    s = Sampler(); s.start()
    events = []
    t = time.time(); time.sleep(args.idle); events.append(dict(stage="idle", photo="", start=t, end=time.time()))
    for stage, photos, query in (("vision", vision, "lang=en"), ("full", full, "lang=en&translate=mr")):
        time.sleep(5)   # back to idle between stages
        for f in photos:
            t0, t1, res = analyse(f, query)
            L = res.get("llama") or {}
            events.append(dict(stage=stage, photo=os.path.basename(f), start=t0, end=t1, status=res.get("status"),
                               llama=bool(L.get("text")), translation=bool(res.get("translation")),
                               timings_ms=res.get("timings_ms", {})))
    time.sleep(2); s.stop_flag = True; s.join()
    with open(f"{args.out}/power_samples.csv", "w") as f:   # raw samples first, so a later error keeps them
        f.write("t,power_w,cpu_pct,temp_c\n")
        for r in s.rows:
            f.write(f"{r['t']:.3f},{r['power_w']:.3f},{r['cpu_pct']:.1f},{'' if r['temp_c'] is None else r['temp_c']}\n")
    for e in events:
        e.update(stats(s.rows, e["start"], e["end"]))
    summary = {}
    for stage in ("idle", "vision", "full"):
        ev = [e for e in events if e["stage"] == stage]
        rows = [r for e in ev for r in s.rows if e["start"] - 0.3 <= r["t"] <= e["end"] + 0.3]
        if not rows:
            continue
        p = [r["power_w"] for r in rows]
        summary[stage] = dict(requests=len(ev) if stage != "idle" else 0, samples=len(rows),
                              power_mean_w=round(sum(p) / len(p), 2), power_max_w=round(max(p), 2),
                              cpu_mean_pct=round(sum(r["cpu_pct"] for r in rows) / len(rows), 1),
                              seconds_per_request=round(sum(e["end"] - e["start"] for e in ev) / len(ev), 2),
                              energy_j_per_request=round(sum(e["energy_j"] or 0 for e in ev) / len(ev), 1)
                              if stage != "idle" else None)
    temps = [r["temp_c"] for r in s.rows if r["temp_c"] is not None]
    summary["temperature_c"] = dict(min=min(temps), max=max(temps))
    summary["throttled"] = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True).stdout.strip()
    json.dump(dict(summary=summary, events=events), open(f"{args.out}/power_profile.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
