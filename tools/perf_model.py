"""Performance model for Llama on the Raspberry Pi 5: predicted limits, measured speed, efficiency.

Why: a benchmark number alone ("12.5 tokens/s") does not say whether the application is fast or slow for the
hardware. This script works out what the hardware allows and compares the measurement with it.

The two Llama phases have different limits:

  decode (one token per step)   reads every weight once per token, does about 1 multiply-add per weight byte
                                -> limited by main-memory bandwidth:
                                   time per token >= bytes read per token / read bandwidth
  prefill (whole prompt at once) reads every weight once for ALL prompt tokens, so it does hundreds of
                                multiply-adds per weight byte -> limited by compute:
                                   time >= multiply-adds / peak multiply-adds per second

Efficiency = predicted (best possible) time / measured time. 70-90 % is normal; much lower means time is lost
somewhere (threads, operators running outside the fast backend, thermal throttling); above 100 % means the model
of the hardware or of the weights is wrong and has to be fixed first.

The model of the weights is checked against the real .pte file size: several hypotheses (how the quantization
scales are stored, whether the output layer is quantized) are compared and the closest one is used. For the
exported Llama this answers "is the large output layer (vocabulary x dim) quantized?".

Inputs (all optional except what the report needs):
  --pte       the exported Llama .pte (for the size check)
  --params    params.json of the checkpoint (default: Llama 3.2 1B values)
  --membw     JSON written by the membw benchmark (cpp/tools/membw.cpp) on the device
  --measured  JSON results of `krishirakshak` runs with Llama (the "llama" -> "stats" block is read)

Usage (on the PC, with the files copied back from the Pi):
  python -m tools.perf_model --pte models/llama3_2_1b_instruct_8da4w.pte --membw bench/membw.json \
      --measured bench/*_llama_en.json
"""
import argparse
import glob
import json
import math
from dataclasses import dataclass
from pathlib import Path

# Llama 3.2 1B (original/params.json of meta-llama/Llama-3.2-1B-Instruct)
DEFAULT_PARAMS = {"dim": 2048, "n_layers": 16, "n_heads": 32, "n_kv_heads": 8, "vocab_size": 128256,
                  "ffn_dim_multiplier": 1.5, "multiple_of": 256}

# Raspberry Pi 5: 4 x Cortex-A76 at 2.4 GHz. Two 128-bit NEON pipes; one SDOT does 16 int8 multiply-adds,
# so 32 int8 MACs per cycle per core. This is a theoretical peak (no real kernel reaches it).
PI5 = {"cores": 4, "ghz": 2.4, "int8_macs_per_cycle": 32}


@dataclass
class Shape:
    dim: int
    layers: int
    heads: int
    kv_heads: int
    vocab: int
    hidden: int

    @property
    def head_dim(self):
        return self.dim // self.heads

    @property
    def layer_linear_params(self):
        """q, k, v, o projections + gate, up, down of the feed-forward block, one layer."""
        kv = self.kv_heads * self.head_dim
        return self.dim * self.dim * 2 + self.dim * kv * 2 + self.dim * self.hidden * 3

    @property
    def table_params(self):
        """Embedding table, and the output layer (same shape)."""
        return self.vocab * self.dim


def load_shape(params_path):
    p = dict(DEFAULT_PARAMS)
    if params_path:
        p.update(json.loads(Path(params_path).read_text()))
    # Feed-forward width as computed by the Llama reference code
    hidden = int(2 * 4 * p["dim"] / 3)
    if p.get("ffn_dim_multiplier"):
        hidden = int(p["ffn_dim_multiplier"] * hidden)
    hidden = p["multiple_of"] * math.ceil(hidden / p["multiple_of"])
    return Shape(p["dim"], p["n_layers"], p["n_heads"], p.get("n_kv_heads") or p["n_heads"], p["vocab_size"], hidden)


def bytes_per_weight(bits, group, scale_bytes):
    """Packed weight plus one scale per group (symmetric quantization, no zero point)."""
    return bits / 8 + (scale_bytes / group if bits < 16 else 0)


def weight_bytes(shape, bits, group, scale_bytes, embedding_bits, head):
    """Bytes of each weight group for one hypothesis. head: 'int4' (same as the layers), 'int8' or 'fp32'."""
    per_w = bytes_per_weight(bits, group, scale_bytes)
    head_per_w = {"int4": per_w, "int8": bytes_per_weight(8, group, scale_bytes), "fp32": 4.0}[head]
    norms = (2 * shape.layers + 1) * shape.dim * 4          # RMSNorm weights, fp32
    return {
        "layers": shape.layers * shape.layer_linear_params * per_w,
        "output_layer": shape.table_params * head_per_w,
        "embedding": shape.table_params * bytes_per_weight(embedding_bits, group, scale_bytes),
        "norms": norms,
    }


def choose_hypothesis(shape, args, pte_bytes):
    """Compare the modelled file size with the real one for each storage hypothesis; return them sorted."""
    rows = []
    for scale_bytes in (2, 4):
        for head in ("int4", "int8", "fp32"):
            wb = weight_bytes(shape, args.weight_bits, args.group_size, scale_bytes, args.embedding_bits, head)
            total = sum(wb.values())
            rows.append({"scale_bytes": scale_bytes, "output_layer": head, "model_bytes": total,
                         "error": (total - pte_bytes) / pte_bytes if pte_bytes else None})
    if pte_bytes:
        rows.sort(key=lambda r: abs(r["error"]))
    return rows


def kv_cache_bytes(shape, positions, kv_bytes):
    return 2 * shape.layers * shape.kv_heads * shape.head_dim * positions * kv_bytes


def read_membw(path, threads):
    d = json.loads(Path(path).read_text())
    table = d["read_gbps"]
    key = str(threads) if str(threads) in table else max(table, key=int)
    return table[key] * 1e9, int(key)


def read_measured(patterns):
    rows = []
    for pat in patterns:
        for f in sorted(glob.glob(pat)):
            text = Path(f).read_text()
            try:
                d = json.loads(text)
            except json.JSONDecodeError:            # several JSON objects in one file: take the first complete one
                d = json.JSONDecoder().raw_decode(text.lstrip())[0]
            st = ((d.get("llama") or {}).get("stats")) or d.get("stats")
            if st and st.get("ok", True) and st.get("generated_tokens"):
                rows.append({"file": Path(f).name, **st})
    return rows


def fmt_mb(b):
    return f"{b / 2**20:8.1f} MiB"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pte")
    ap.add_argument("--params")
    ap.add_argument("--membw", help="membw JSON from the device")
    ap.add_argument("--bandwidth-gbps", type=float, help="read bandwidth in GB/s if no membw JSON is given")
    ap.add_argument("--threads", type=int, default=4, help="Llama threads (selects the membw column)")
    ap.add_argument("--measured", nargs="*", default=[], help="krishirakshak result JSON files (globs allowed)")
    ap.add_argument("--weight-bits", type=int, default=4)
    ap.add_argument("--group-size", type=int, default=32)
    ap.add_argument("--embedding-bits", type=int, default=4)
    ap.add_argument("--context", type=int, default=1024, help="KV cache length the .pte was exported with")
    ap.add_argument("--kv-bytes", type=int, default=4, help="bytes per KV cache value (4 = fp32 cache)")
    ap.add_argument("--prompt-tokens", type=int, default=295, help="used when no measurement is given")
    ap.add_argument("--new-tokens", type=int, default=86, help="used when no measurement is given")
    ap.add_argument("--peak-gmacs", type=float, help="peak int8 GMAC/s; default: theoretical Raspberry Pi 5 value")
    ap.add_argument("--json", help="also write the report as JSON to this file")
    args = ap.parse_args()

    shape = load_shape(args.params)
    report = {"shape": shape.__dict__ | {"head_dim": shape.head_dim}}

    # 1. Model size: which storage hypothesis matches the .pte?
    pte_bytes = None
    if args.pte:
        if Path(args.pte).is_file():
            pte_bytes = Path(args.pte).stat().st_size
        else:
            print(f"(no file {args.pte}: skipping the size check)")
    hyps = choose_hypothesis(shape, args, pte_bytes)
    best = hyps[0] if pte_bytes else next(h for h in hyps if h["scale_bytes"] == 2 and h["output_layer"] == "int4")
    wb = weight_bytes(shape, args.weight_bits, args.group_size, best["scale_bytes"], args.embedding_bits,
                      best["output_layer"])
    print("== Llama weights ==")
    print(f"layers {shape.layers}, dim {shape.dim}, heads {shape.heads} (KV heads {shape.kv_heads}), "
          f"feed-forward {shape.hidden}, vocabulary {shape.vocab}")
    for k, v in wb.items():
        print(f"  {k:13s} {fmt_mb(v)}")
    if pte_bytes:
        print(f"  .pte file     {fmt_mb(pte_bytes)}")
        print("  hypotheses (closest first):")
        for h in hyps:
            print(f"    scales {h['scale_bytes']} B, output layer {h['output_layer']:4s}: "
                  f"{fmt_mb(h['model_bytes'])}  ({h['error']:+.1%})")
        if abs(best["error"]) > 0.05:
            print("  WARNING: no hypothesis within 5 % of the file size; the predictions below are approximate")
        if best["output_layer"] == "fp32":
            print("  NOTE: the output layer looks unquantized (fp32); it is read on every token")
    else:
        print("  (no --pte given: assuming 2-byte scales and a quantized output layer)")
    report["weights"] = wb
    report["hypotheses"] = hyps

    # 2. KV cache
    kv_full = kv_cache_bytes(shape, args.context, args.kv_bytes)
    print(f"\n== KV cache ==\n  {args.context} positions x {args.kv_bytes} B: {fmt_mb(kv_full)} "
          f"(with {shape.heads} KV heads instead of {shape.kv_heads} it would be {fmt_mb(kv_full * shape.heads / shape.kv_heads)})")
    report["kv_cache_bytes"] = kv_full

    # 3. Hardware limits
    if args.membw:
        bw, bw_threads = read_membw(args.membw, args.threads)
        bw_src = f"membw, {bw_threads} threads"
    elif args.bandwidth_gbps:
        bw, bw_src = args.bandwidth_gbps * 1e9, "given"
    else:
        bw, bw_src = None, None
    peak = (args.peak_gmacs * 1e9 if args.peak_gmacs
            else PI5["cores"] * PI5["ghz"] * 1e9 * PI5["int8_macs_per_cycle"])
    print("\n== Hardware ==")
    print(f"  read bandwidth: {bw / 1e9:.2f} GB/s ({bw_src})" if bw else "  read bandwidth: unknown (give --membw)")
    print(f"  peak int8 compute: {peak / 1e9:.0f} GMAC/s ({'given' if args.peak_gmacs else 'theoretical Pi 5'})")

    # 4. Predictions per measured run (or for the default prompt)
    measured = read_measured(args.measured)
    cases = measured or [{"file": "(no measurement)", "prompt_tokens": args.prompt_tokens,
                          "generated_tokens": args.new_tokens}]
    print("\n== Predicted limits vs measured ==")
    report["runs"] = []
    for c in cases:
        p, n = int(c["prompt_tokens"]), int(c["generated_tokens"])
        # decode: all weights except the embedding table (one row per token) + the KV cache read so far
        weights_per_token = wb["layers"] + wb["output_layer"] + wb["norms"]
        avg_pos = p + n / 2
        decode_bytes = weights_per_token + kv_cache_bytes(shape, avg_pos, args.kv_bytes)
        # prefill: one multiply-add per weight per prompt token, attention ~ T^2/2 (causal), output layer once
        attn = shape.layers * 2 * shape.heads * shape.head_dim * p * p / 2
        prefill_macs = p * shape.layers * shape.layer_linear_params + attn + shape.table_params
        prefill_s = max(prefill_macs / peak, (weights_per_token / bw) if bw else 0)
        row = {"file": c["file"], "prompt_tokens": p, "generated_tokens": n,
               "decode_bytes_per_token": decode_bytes, "prefill_macs": prefill_macs,
               "predicted_prefill_s": prefill_s}
        print(f"  {c['file']}: prompt {p} tokens, generated {n}")
        print(f"    prefill  {prefill_macs / 1e9:7.1f} GMAC -> >= {prefill_s:6.2f} s", end="")
        if "time_to_first_token_s" in c:
            m = c["time_to_first_token_s"]
            row["measured_prefill_s"], row["prefill_efficiency"] = m, prefill_s / m
            print(f" | measured {m:6.2f} s | efficiency {prefill_s / m:6.1%}", end="")
        print()
        if bw:
            tps = bw / decode_bytes
            row["predicted_tokens_per_s"] = tps
            print(f"    decode   {decode_bytes / 2**20:7.1f} MiB/token -> <= {tps:6.2f} tok/s", end="")
            if "tokens_per_s" in c:
                m = c["tokens_per_s"]
                row["measured_tokens_per_s"], row["decode_efficiency"] = m, m / tps
                print(f" | measured {m:6.2f} tok/s | efficiency {m / tps:6.1%}", end="")
                if m > tps * 1.05:
                    print("  (above the limit: check the bandwidth measurement and the weight model)", end="")
            print()
        report["runs"].append(row)

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
