"""Check which operators of an exported .pte run inside the XNNPACK delegate and which run outside it.

Why: on the Raspberry Pi the XNNPACK delegate (NEON / KleidiAI kernels) is fast. An operator the delegate did not
take runs on ExecuTorch's generic CPU kernels instead, which can be many times slower. One heavy operator left
outside (a matrix multiplication, the output layer, attention) can cost more than everything else together, and
nothing in the application output shows it. This script reads the program header of the .pte (not the weights)
and prints, per method (e.g. "forward"):

  - the delegate calls per backend, with the size of each backend's payload (weights packed for it)
  - every operator executed outside a delegate, with how often it is called
  - a warning for heavy operators outside a delegate (matmul / linear / conv / attention / embedding)

Usage (in the Python environment used for the export, see llm/export_llama.sh):
    python -m llm.inspect_pte models/llama3_2_1b_instruct_8da4w.pte
    python -m llm.inspect_pte models/llama3_2_1b_instruct_8da4w.pte --json results/llama_pte_ops.json

Small operators outside the delegate are expected (KV cache update, custom attention, slicing, type conversion).
"""
import argparse
import json
from collections import Counter
from pathlib import Path

# Operator names that do real work per weight; outside a delegate they are a performance problem.
# The embedding lookup is not in the list: it reads one table row per token, however large the table is.
HEAVY = ("mm", "matmul", "linear", "addmm", "bmm", "conv", "sdpa", "attention", "gemm")
# Except for the KV-cache attention kernel the Llama export adds on purpose (it reads the cache in place)
EXPECTED_OUTSIDE = ("custom_sdpa", "update_cache")


def load_program(pte_path):
    """Parse only the flatbuffer header of the .pte; the weight segments are not loaded."""
    # Internal helpers of executorch.exir (1.5.x); the public deserialize_pte_binary would load all weights too
    from executorch.exir._serialize._flatbuffer_program import _flatbuffer_to_program
    from executorch.exir._serialize._program import _get_extended_header

    data = Path(pte_path).read_bytes()
    header = _get_extended_header(data)
    program_size = header.program_size if header is not None else len(data)
    return _flatbuffer_to_program(data[:program_size]), len(data)


def delegate_payload_bytes(program, delegate):
    ref = delegate.processed
    if int(ref.location) == 1:          # DataLocation.SEGMENT
        return program.segments[ref.index].size
    return len(program.backend_delegate_data[ref.index].data)


def op_name(op):
    return f"{op.name}.{op.overload}" if op.overload else op.name


def inspect(program):
    methods = []
    for plan in program.execution_plan:
        kernel_calls, delegate_calls = Counter(), Counter()
        for chain in plan.chains:
            for instr in chain.instructions:
                args = instr.instr_args
                kind = type(args).__name__
                if kind == "KernelCall":
                    kernel_calls[op_name(plan.operators[args.op_index])] += 1
                elif kind == "DelegateCall":
                    delegate_calls[plan.delegates[args.delegate_index].id] += 1
        payload = Counter()
        for d in plan.delegates:
            payload[d.id] += delegate_payload_bytes(program, d)
        heavy = [op for op in kernel_calls
                 if any(h in op.lower() for h in HEAVY) and not any(e in op for e in EXPECTED_OUTSIDE)]
        methods.append({"method": plan.name, "delegate_calls": dict(delegate_calls),
                        "delegate_payload_bytes": dict(payload), "outside_delegate": dict(kernel_calls.most_common()),
                        "heavy_outside_delegate": heavy})
    return methods


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pte")
    ap.add_argument("--json", help="also write the result to this file")
    args = ap.parse_args()

    program, file_bytes = load_program(args.pte)
    methods = inspect(program)
    segment_bytes = sum(s.size for s in program.segments)
    print(f"{args.pte}: {file_bytes / 2**20:.1f} MiB, {len(program.segments)} data segments "
          f"({segment_bytes / 2**20:.1f} MiB)")
    # Recent exports keep the weights out of the delegate payload, as named tensors the backend loads at start-up
    named = program.named_data or []
    if named:
        # identical tensors share one segment, so count each segment once
        named_bytes = sum(program.segments[i].size for i in {n.segment_index for n in named})
        print(f"  weights stored as named data: {len(named)} tensors, {named_bytes / 2**20:.1f} MiB "
              "(loaded by the delegate; not counted in its payload below)")
    problems = 0
    for m in methods:
        if not m["delegate_calls"] and not m["outside_delegate"]:
            continue                    # metadata methods (get_max_seq_len, ...) have no operators
        print(f"\nmethod {m['method']}")
        for backend, n in m["delegate_calls"].items():
            print(f"  delegate {backend}: {n} calls, payload {m['delegate_payload_bytes'][backend] / 2**20:.1f} MiB")
        print(f"  outside a delegate: {sum(m['outside_delegate'].values())} calls")
        for op, n in m["outside_delegate"].items():
            mark = "  <-- heavy operator outside the delegate" if op in m["heavy_outside_delegate"] else ""
            print(f"    {n:5d} x {op}{mark}")
        calls = sum(m["delegate_calls"].values())
        if calls > 1:
            # Each switch between the delegate and the generic kernels synchronises the thread pool; an operator
            # the delegate does not support (often the mean of a normalisation layer) splits the graph there.
            print(f"  note: the graph is split into {calls} delegate calls per run of this method")
        problems += len(m["heavy_outside_delegate"])
    print("\nOK: every heavy operator runs in a delegate" if problems == 0
          else f"\nWARNING: {problems} heavy operator type(s) run outside the delegate (see above)")
    if args.json:
        Path(args.json).write_text(json.dumps({"pte": args.pte, "file_bytes": file_bytes, "methods": methods},
                                              indent=1))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
