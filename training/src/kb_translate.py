# %% [markdown]
# # KrishiRakshak PS1 - Knowledge base in 9 regional languages (Kaggle GPU)
#
# Translates the verified extracts of app/kb/tomato_kb.json (ICAR, NIPHM, TNAU publications), the spray-row notes,
# topic names and fixed messages into hi te mr kn ta bn gu or pa, once, with tools/translate_kb.py (IndicTrans2
# en-indic 200M on CTranslate2 + a plain-English glossary). The application then shows them from the file in the
# farmer's language. Spray products and doses are never translated; Hindi team translations are kept.
#
# On the GPU the model runs in FP16 (closer to the original model than the INT8 used on the Raspberry Pi); the
# result is stored text, so the best precision is used. Output: /kaggle/working/tomato_kb.json (replaces
# app/kb/tomato_kb.json after review of the diff) and translate_log.txt.
#
# **Kaggle setup:** Accelerator = GPU T4, internet on, attach `ashwinambatwar/krishirakshak-kb-translate-inputs`.

# %%
import glob, os, shutil, subprocess, sys, time
from pathlib import Path

SMOKE = os.environ.get("KR_SMOKE") == "1"
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK = Path(os.environ.get("KR_WORK", "/kaggle/working"))
script = next(INPUT_ROOT.rglob("translate_kb.py"))
inputs = script.parent
model_dir = next(p.parent for p in INPUT_ROOT.rglob("model.bin"))
import hashlib
print("inputs:", inputs, "| model:", model_dir)
print("translate_kb.py sha256:", hashlib.sha256(script.read_bytes()).hexdigest()[:16])   # which version is mounted

# %%
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ctranslate2==4.6.0", "sentencepiece==0.2.1",
                "indictranstoolkit==1.1.1"], check=True)

# CTranslate2's CUDA build needs cuBLAS 12 (and cuDNN 9); Kaggle has them as pip packages installed with PyTorch.
# Kaggle's Python keeps packages in dist-packages (not site-packages), so every package folder is searched.
env = dict(os.environ)
libs = sorted({str(Path(f).parent) for d in sys.path if d for f in glob.glob(f"{d}/nvidia/*/lib/*.so*")})
print("CUDA library folders:", libs if libs else "none found")
env["LD_LIBRARY_PATH"] = ":".join(libs + [env.get("LD_LIBRARY_PATH", "")])
subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv"])
PROBE = ("import ctranslate2; n = ctranslate2.get_cuda_device_count(); "
         "print('CUDA devices for CTranslate2:', n, ctranslate2.get_supported_compute_types('cuda') if n else '')")


def gpu_ok():
    probe = subprocess.run([sys.executable, "-c", PROBE], env=env, capture_output=True, text=True)
    print(probe.stdout, probe.stderr[-1500:], flush=True)
    return probe.returncode == 0 and "devices for CTranslate2: 0" not in probe.stdout


# CTranslate2 4.6 is built for CUDA 12 (libcublas.so.12). Newer Kaggle images ship CUDA 13 libraries only, so the
# CUDA 12 cuBLAS is installed into its own folder (Kaggle's CUDA 13 setup is not touched) and put first in the path.
if not gpu_ok():
    cu12 = Path("/tmp/cu12")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--target", str(cu12), "nvidia-cublas-cu12==12.*",
                    "nvidia-cuda-runtime-cu12==12.*"], check=True)
    extra = sorted({str(Path(f).parent) for f in glob.glob(f"{cu12}/nvidia/*/lib/*.so*")})
    print("CUDA 12 library folders:", extra)
    env["LD_LIBRARY_PATH"] = ":".join(extra + [env["LD_LIBRARY_PATH"]])
    gpu_ok()

# %% [markdown]
# ## Translate (GPU FP16; CPU INT8 if the GPU cannot be used)

# %%
out = WORK / "tomato_kb.json"
base = [sys.executable, str(script), "--kb", str(inputs / "tomato_kb.json"), "--out", str(out),
        "--model-dir", str(model_dir), "--spm", str(inputs / "indictrans2_model.SRC")]
if (inputs / "ui_en.json").exists():   # interface labels of the farmer app -> app/web/js/i18n_regional.js
    base += ["--ui", str(inputs / "ui_en.json"), "--ui-js", str(WORK / "i18n_regional.js")]
if SMOKE:
    base += ["--limit", "5", "--langs", "mr", "ta"]
t0 = time.time()
with open(WORK / "translate_log.txt", "w") as log:
    run = subprocess.run(base + ["--device", "cuda", "--compute-type", "float16"], env=env, stdout=log,
                         stderr=subprocess.STDOUT)
    if run.returncode != 0:
        log.flush()
        print("GPU run failed:\n" + open(WORK / "translate_log.txt").read()[-3000:], flush=True)
        print("falling back to the CPU", flush=True)
        log.write("\n--- CPU fallback ---\n"); log.flush()
        run = subprocess.run(base + ["--device", "cpu", "--compute-type", "int8", "--threads", str(os.cpu_count())],
                             env=env, stdout=log, stderr=subprocess.STDOUT)
print(open(WORK / "translate_log.txt").read()[-3000:])
print(f"total {time.time() - t0:.0f} s, exit code {run.returncode}")
assert run.returncode == 0 and out.exists(), "translation failed"

# %% [markdown]
# ## Coverage check

# %%
import json
kb = json.loads(out.read_text())
langs = kb["translations"]["languages"]
ext = [c for c in kb["chunks"] if c.get("en")]
for lang in langs:
    have = sum(1 for c in ext if c.get(lang))
    names = sum(1 for t in kb["topics"].values() if lang in t["name"])
    print(f"{lang}: extracts {have}/{len(ext)}, topic names {names}/{len(kb['topics'])}")
shutil.copy(inputs / "indictrans2_LICENSE", WORK / "indictrans2_LICENSE")
