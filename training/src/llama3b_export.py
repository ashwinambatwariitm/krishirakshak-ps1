# %% [markdown]
# # KrishiRakshak PS1 - Llama 3.2 3B Instruct -> ExecuTorch .pte (INT4 8da4w, XNNPACK) on Kaggle CPU
#
# Same export settings as the 1B model (`llm/export_llama.sh`): 8-bit dynamic activations with 4-bit weights
# (group size 32), 4-bit embeddings, KV cache + SDPA, XNNPACK backend, context 1024. The export runs here because the
# FP32 3B model needs more memory during export than the 16 GB development PC has (the local run was stopped at
# 9.4 GB resident while lowering to XNNPACK). A Kaggle CPU session has about 30 GB.
#
# Where the Meta checkpoint (`original/consolidated.00.pth`, `params.json`, `tokenizer.model`) comes from, in order:
# 1. any attached input that contains it: the Kaggle model `metaresearch/llama-3.2` (PyTorch, 3b-instruct; accept the
#    Llama 3.2 licence on its Kaggle page first) or a private dataset with the `original/` folder;
# 2. otherwise Hugging Face, with a Kaggle secret `HF_TOKEN` attached to this notebook (Add-ons > Secrets) for an
#    account that has access to `meta-llama/Llama-3.2-3B-Instruct`.
#
# At the end the new .pte generates one English and one Hindi answer with ExecuTorch's TextLLMRunner (the same runner
# the application uses), so a broken export is caught here and not after a 2 GB download. Speed on Kaggle's x86 CPU
# is printed for reference only; the deployment numbers come from the Raspberry Pi 5.

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"          # local test: skip the export, test an existing .pte instead
# Pinned to the versions of the local export environment, so the .pte matches the runtime built for the Pi
PACKAGES = ["torch==2.14.1", "torchao==0.18.0", "executorch==1.5.1"]
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--extra-index-url",
                    "https://download.pytorch.org/whl/cpu", *PACKAGES], check=True)

# %%
import json, re, resource, shutil, time
from pathlib import Path

INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working"))
DOWNLOAD_DIR = Path("/tmp/Llama-3.2-3B-Instruct")   # outside the saved output; only the .pte and tokenizer are kept
HF_REPO = "meta-llama/Llama-3.2-3B-Instruct"
EXPECTED_DIM = int(os.environ.get("KR_EXPECTED_DIM", 3072))  # hidden size of the 3B model (1B: 2048)
CONTEXT = 1024
PTE_NAME = os.environ.get("KR_PTE_NAME", "llama3_2_3b_instruct_8da4w.pte")
WORK_DIR.mkdir(parents=True, exist_ok=True)
print(subprocess.run(["free", "-g"], capture_output=True, text=True).stdout, "CPU cores:", os.cpu_count())

# %% [markdown]
# ## Locate the Meta checkpoint (attached input first, Hugging Face second)

# %%
def find_checkpoint(root):
    """Folder holding consolidated.00.pth + params.json of the expected model size under root, or None."""
    for dirpath, _, files in os.walk(root, followlinks=True):
        if "consolidated.00.pth" in files and "params.json" in files:
            params = json.load(open(Path(dirpath) / "params.json"))
            if params.get("dim") == EXPECTED_DIM:
                return Path(dirpath)
            print(f"skipping {dirpath}: dim {params.get('dim')} is not the expected {EXPECTED_DIM}")
    return None

CKPT_DIR = find_checkpoint(INPUT_ROOT) if INPUT_ROOT.exists() else None
if CKPT_DIR is None:
    try:
        from kaggle_secrets import UserSecretsClient
        token = UserSecretsClient().get_secret("HF_TOKEN")
    except Exception as e:
        raise RuntimeError("No Llama 3.2 3B checkpoint is attached and no HF_TOKEN secret is available. Either attach "
                           "the Kaggle model metaresearch/llama-3.2 (PyTorch, 3b-instruct) after accepting its licence, "
                           "or add a Kaggle secret HF_TOKEN and attach it to this notebook.") from e
    from huggingface_hub import snapshot_download
    snapshot_download(HF_REPO, allow_patterns=["original/*"], local_dir=str(DOWNLOAD_DIR), token=token)
    CKPT_DIR = DOWNLOAD_DIR / "original"
TOKENIZER = CKPT_DIR / "tokenizer.model"
assert TOKENIZER.exists(), f"tokenizer.model missing in {CKPT_DIR}"
print("checkpoint:", CKPT_DIR, "|", json.load(open(CKPT_DIR / "params.json")))
for f in sorted(CKPT_DIR.iterdir()):
    print(f"  {f.name:28s} {f.stat().st_size / 1e9:6.2f} GB")

# %% [markdown]
# ## Export (INT4 8da4w, XNNPACK) - about an hour on 4 CPU cores

# %%
EXPORT_ARGS = [
    "base.model_class=llama3_2",
    f"base.checkpoint={CKPT_DIR / 'consolidated.00.pth'}",
    f"base.params={CKPT_DIR / 'params.json'}",
    'base.metadata="{\\"get_bos_id\\":128000, \\"get_eos_ids\\":[128009, 128001]}"',
    "model.use_kv_cache=True", "model.use_sdpa_with_kv_cache=True", "model.dtype_override=fp32",
    f"export.max_seq_length={CONTEXT}", f"export.max_context_length={CONTEXT}",
    "backend.xnnpack.enabled=True", "backend.xnnpack.extended_ops=True",
    "quantization.qmode=8da4w", "quantization.group_size=32", 'quantization.embedding_quantize="4,32"',
    f"export.output_name={PTE_NAME}",
]
PTE = WORK_DIR / PTE_NAME
LOG = WORK_DIR / "export_3b.log"
if SMOKE:
    print("smoke test: export skipped; testing", PTE)
else:
    t0 = time.time()
    with open(LOG, "w") as log:  # export_llm writes the .pte to the current directory
        proc = subprocess.run([sys.executable, "-m", "executorch.extension.llm.export.export_llm", *EXPORT_ARGS],
                              cwd=WORK_DIR, stdout=log, stderr=subprocess.STDOUT)
    peak_gb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 2**20
    print(f"export exit code {proc.returncode} after {(time.time() - t0) / 60:.0f} min, peak RAM {peak_gb:.1f} GB")
    print("".join(open(LOG).readlines()[-25:]))
    if proc.returncode != 0:
        raise RuntimeError(f"export failed (exit code {proc.returncode}); see {LOG.name}. Exit code -9 means the session "
                           "ran out of memory.")
assert PTE.exists(), f"{PTE} was not written"
shutil.copy(TOKENIZER, WORK_DIR / "llama3_2_tokenizer.model")
shutil.copy(CKPT_DIR / "params.json", WORK_DIR / "llama3_2_3b_params.json")  # model shape, for tools/perf_model.py
print(f"{PTE.name}: {PTE.stat().st_size / 1e9:.2f} GB")

# %% [markdown]
# ## Check the .pte: one English and one Hindi answer with the application's runner

# %%
# The two imports register the operators the graph uses (custom SDPA attention, 4-bit embedding)
import executorch.extension.llm.custom_ops.custom_ops  # noqa: F401
import executorch.kernels.quantized  # noqa: F401
from executorch.extension.llm.runner import GenerationConfig, TextLLMRunner

def llama3_chat(system, user):
    """Llama 3 instruct chat format (the tokenizer turns the special tokens into their ids)."""
    return ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system + "<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n\n" + user + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")

FACTS = ("1. Late blight spreads fast in cool, wet weather.\n"
         "2. Remove and destroy infected leaves; do not leave them in the field.\n"
         "3. Avoid overhead watering and keep space between plants for air flow.")
CASES = {"en": "English", "hi": "Hindi"}
t0 = time.time()
runner = TextLLMRunner(str(PTE), str(WORK_DIR / "llama3_2_tokenizer.model"))
load_s = time.time() - t0
checks = []
for lang, language in CASES.items():
    system = (f"You are an agricultural advisor for small farmers in India. Answer in {language}, in 3-4 short "
              "sentences, using only the FACTS given. Do not name any pesticide.")
    user = f"Diagnosis: late blight on a tomato leaf (model confidence 92%).\n\nFACTS:\n{FACTS}\n\nWhat should the farmer do first?"
    pieces, stats = [], {}
    runner.reset()
    runner.generate(llama3_chat(system, user), GenerationConfig(echo=False, max_new_tokens=120, temperature=0.0,
                                                                num_bos=0, num_eos=0),
                    token_callback=pieces.append, stats_callback=lambda s: stats.update(s=s))
    text = "".join(pieces).replace("<|eot_id|>", "").strip()
    s = stats["s"]
    tok_s = s.num_generated_tokens * 1000 / max(1, s.inference_end_ms - s.first_token_ms)
    # Hindi output must be mostly Devanagari; English output must be mostly Latin letters
    letters = [c for c in text if c.isalpha()]
    devanagari = sum(0x0900 <= ord(c) <= 0x097F for c in letters) / max(1, len(letters))  # Devanagari block
    ok = len(text) > 40 and (devanagari > 0.5 if lang == "hi" else devanagari < 0.1)
    checks.append(dict(lang=lang, ok=ok, prompt_tokens=s.num_prompt_tokens, generated_tokens=s.num_generated_tokens,
                       time_to_first_token_s=round((s.first_token_ms - s.inference_start_ms) / 1000, 2),
                       tokens_per_s_kaggle_x86=round(tok_s, 1), text=text))
    print(f"--- {language}: {'OK' if ok else 'CHECK'} | {s.num_generated_tokens} tokens, {tok_s:.1f} tok/s (Kaggle x86)\n{text}\n")

peak_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20
json.dump({"pte": PTE.name, "pte_gb": round(PTE.stat().st_size / 1e9, 3), "load_s": round(load_s, 1),
           "runner_peak_rss_gb": round(peak_gb, 2), "export_settings": EXPORT_ARGS[4:], "packages": PACKAGES,
           "checks": checks}, open(WORK_DIR / "llama3b_check.json", "w"), indent=2, ensure_ascii=False)
assert all(c["ok"] for c in checks), "a generation check failed - read the answers above before using this .pte"
print(subprocess.run(["sha256sum", str(PTE), str(WORK_DIR / "llama3_2_tokenizer.model")],
                     capture_output=True, text=True).stdout)
print(sorted(p.name for p in WORK_DIR.iterdir()))
