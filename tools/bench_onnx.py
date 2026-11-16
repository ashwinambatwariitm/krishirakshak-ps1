"""Measure file size, RAM and inference latency of ONNX models (FP32 vs INT8) with ONNX Runtime on the CPU.

Usage:
    python tools/bench_onnx.py exported/*.onnx
    python tools/bench_onnx.py exported/*.onnx --threads 1 4 --runs 100 --csv bench.csv

Each model is measured in its own fresh Python process, so the RAM numbers of one model do not include another
model. Input data is random (latency of these CNNs does not depend on pixel values); accuracy is measured separately
by the int8_ptq notebook on the real test images.

Reported per model and thread count:
    size_mb            file size on disk
    ram_session_mb     resident memory added by loading the model (session creation), above an idle ORT process
    ram_peak_mb        peak resident memory of the process during inference, minus the idle ORT process
    latency_ms_*       median / 90th percentile / mean of single-image (batch 1) inference, after warm-up runs

Run it on the Raspberry Pi 5 for the deployment numbers; numbers from a PC are only for relative comparison.
Requires: numpy, onnxruntime (standard library otherwise; RAM is read from /proc, so Linux only).
"""
import argparse
import csv
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

# Code run in the child process: prints one JSON line with the measurements for one model and thread count.
CHILD = r"""
import json, resource, sys, time
import numpy as np
import onnxruntime as ort

def rss_mb():
    # current resident set size from /proc (ru_maxrss only gives the peak)
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    return float("nan")

path, threads, warmup, runs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
idle = rss_mb()
opts = ort.SessionOptions()
opts.intra_op_num_threads = threads
opts.inter_op_num_threads = 1
opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
session = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
loaded = rss_mb()
inp = session.get_inputs()[0]
shape = [d if isinstance(d, int) else 1 for d in inp.shape]  # dynamic batch -> 1
x = np.random.default_rng(0).random(shape, dtype=np.float32)
for _ in range(warmup):
    session.run(None, {inp.name: x})
times = []
for _ in range(runs):
    t = time.perf_counter()
    session.run(None, {inp.name: x})
    times.append((time.perf_counter() - t) * 1000)
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KiB on Linux
t = np.array(times)
print(json.dumps(dict(input_shape=shape, ram_session_mb=loaded - idle, ram_peak_mb=peak - idle,
                      latency_ms_median=float(np.median(t)), latency_ms_p90=float(np.percentile(t, 90)),
                      latency_ms_mean=float(t.mean()))))
"""


def cpu_name():
    """Human-readable CPU model (x86 'model name' or the Arm 'Model' line on a Raspberry Pi)."""
    try:
        fields = dict(line.split(":", 1) for line in open("/proc/cpuinfo") if ":" in line)
        fields = {k.strip(): v.strip() for k, v in fields.items()}
        # x86 has "model name"; a Raspberry Pi has "Model" (board name); the plain "model" field is only a number
        return fields.get("model name") or fields.get("Model") or platform.machine()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def measure(path, threads, warmup, runs):
    """Run the measurement for one model in a new Python process and return its results as a dict."""
    out = subprocess.run([sys.executable, "-c", CHILD, str(path), str(threads), str(warmup), str(runs)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


def main():
    """Benchmark every given model at every thread count and print (and optionally save) a table."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("models", nargs="+", help="ONNX files to measure")
    parser.add_argument("--threads", nargs="+", type=int, default=[1, 4], help="CPU threads to test (default: 1 4)")
    parser.add_argument("--warmup", type=int, default=10, help="untimed runs before measuring (default: 10)")
    parser.add_argument("--runs", type=int, default=50, help="timed runs per setting (default: 50)")
    parser.add_argument("--csv", help="also write the results to this CSV file")
    args = parser.parse_args()

    import onnxruntime
    print(f"CPU: {cpu_name()} | {os.cpu_count()} cores | onnxruntime {onnxruntime.__version__}")
    rows = []
    for path in map(Path, args.models):
        for threads in args.threads:
            r = measure(path, threads, args.warmup, args.runs)
            rows.append(dict(model=path.name, threads=threads, size_mb=round(path.stat().st_size / 1e6, 2),
                             **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}))
    cols = ["model", "threads", "size_mb", "ram_session_mb", "ram_peak_mb", "latency_ms_median", "latency_ms_p90"]
    widths = [max(len(c), *(len(str(r[c])) for r in rows)) for c in cols]
    print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    for r in rows:
        print("  ".join(str(r[c]).ljust(w) for c, w in zip(cols, widths)))
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["cpu"] + list(rows[0]))
            writer.writeheader()
            writer.writerows({"cpu": cpu_name(), **r} for r in rows)


if __name__ == "__main__":
    main()
