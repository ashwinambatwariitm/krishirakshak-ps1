# %% [markdown]
# # KrishiRakshak PS1 - LoRA fine-tuning of Llama 3.2 1B: rewrite verified extracts faithfully (Kaggle GPU)
#
# Goal: teach Llama 3.2 1B the one job it has in the application - rewrite the retrieved ICAR / NIPHM / TNAU extracts
# in simple words while keeping their key terms, so that its sentences pass the grounding check of the application
# (cpp/src/output_guard.cpp). Facts stay in the knowledge base (retrieved at run time, with sources); the model is not
# taught treatments.
#
# Distillation with a verifier:
# 1. Teacher: Llama 3.2 3B Instruct rewrites the facts of each topic with the application's prompt
#    (prompts/advise_keep_words.txt, identical to the built-in prompt).
# 2. Filter: every teacher sentence goes through the same grounding check as the application (llm/grounding.py, a
#    copy verified against the C++ check); only grounded sentences become training targets.
# 3. Student: LoRA on Llama 3.2 1B Instruct (attention and feed-forward projections), trained on those targets.
# 4. Evaluation on the six demo diseases, which are held out of training: share of answers the application would
#    accept, base 1B vs fine-tuned 1B, same prompts.
# 5. The LoRA weights are merged into the 1B checkpoint, which is exported with the same ExecuTorch settings as the
#    deployed model (INT4 8da4w, XNNPACK) and checked with the application's runner.
#
# The model code is ExecuTorch's own Llama implementation, which reads Meta's original checkpoint directly, so the
# merged weights go into the same export path as the base model without any format conversion.
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, attach the private datasets
# `ashwinambatwar/llama32-1b-instruct-original`, `ashwinambatwar/llama32-3b-instruct-original` and
# `ashwinambatwar/krishirakshak-lora-inputs` (prompt_facts.json, grounding.py, advise_keep_words.txt).
# Set PILOT = True for a quick check of every step (a few examples, a few training steps, no export).

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
PILOT = True
SMOKE = os.environ.get("KR_SMOKE") == "1"   # local logic test without any model (prompts, data selection, filter)
PACKAGES = ["torch==2.14.1", "torchao==0.18.0", "executorch==1.5.1"]   # same versions as the deployed export
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *PACKAGES], check=True)

# %%
import itertools, json, math, random, re, resource, shutil, time
from pathlib import Path

import torch

INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "llama_lora"
WORK_DIR.mkdir(parents=True, exist_ok=True)
SEED = 42
random.seed(SEED); torch.manual_seed(SEED)

# Six demo diseases (the Phase 1 classifier): evaluation only, never used for training
HOLDOUT = ["healthy", "early_blight", "late_blight", "septoria_leaf_spot", "bacterial_spot", "yellow_leaf_curl_virus"]
VARIANTS_PER_TOPIC = 2 if PILOT else 12       # training prompts per topic (fact subsets, order, confidence, spread)
EVAL_VARIANTS = 1 if PILOT else 3             # evaluation prompts per held-out disease
MAX_NEW_TOKENS = 40 if PILOT else 160         # the application allows 160
MAX_TRAIN_TOPICS = 3 if PILOT else None
LORA_RANK, LORA_ALPHA = 16, 32
LORA_TARGETS = ("wq", "wk", "wv", "wo", "w1", "w2", "w3")
LR, EPOCHS, GRAD_ACCUM = 2e-4, (1 if PILOT else 3), (1 if PILOT else 8)
MAX_STEPS = 4 if PILOT else None
MIN_GROUNDED = 2                              # the application needs two grounded sentences (kMinGroundedSentences)
EOT, EOS = 128009, 128001
CONTEXT = 1024
OUT_NAME = "llama3_2_1b_krishirakshak_lora_8da4w.pte"   # Llama 3.2 licence: derived model names start with "Llama"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32   # T4 has no bfloat16 compute
print("torch", torch.__version__, "| device", DEVICE, torch.cuda.get_device_name(0) if DEVICE == "cuda" else "")
if DEVICE == "cuda":  # fail fast on a GPU this torch build cannot use
    torch.nn.functional.conv2d(torch.randn(1, 3, 8, 8, device="cuda"), torch.randn(2, 3, 3, 3, device="cuda")).sum().item()

def save_json(obj, name):
    with open(WORK_DIR / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# %% [markdown]
# ## Locate the checkpoints and the inputs

# %%
def find_checkpoint(dim):
    """Folder with consolidated.00.pth + params.json of the model with this hidden size (1B: 2048, 3B: 3072)."""
    for d, _, files in os.walk(INPUT_ROOT, followlinks=True):
        if "consolidated.00.pth" in files and "params.json" in files:
            if json.load(open(Path(d) / "params.json")).get("dim") == dim:
                return Path(d)
    return None

def find_file(name):
    for d, _, files in os.walk(INPUT_ROOT, followlinks=True):
        if name in files:
            return Path(d) / name
    raise FileNotFoundError(f"{name} not found - attach ashwinambatwar/krishirakshak-lora-inputs")

STUDENT_DIR, TEACHER_DIR = find_checkpoint(2048), find_checkpoint(3072)
FACTS_FILE, PROMPT_FILE = find_file("prompt_facts.json"), find_file("advise_keep_words.txt")
sys.path.insert(0, str(find_file("grounding.py").parent))
from grounding import Grounding  # noqa: E402  (copy of llm/grounding.py)
print("student:", STUDENT_DIR, "| teacher:", TEACHER_DIR, "| facts:", FACTS_FILE)
if not SMOKE:
    assert STUDENT_DIR and TEACHER_DIR, "attach the 1B and 3B checkpoint datasets"

FACTS = json.load(open(FACTS_FILE, encoding="utf-8"))
GROUND = Grounding(FACTS["grounding"])
TOPICS = {t["topic"]: t for t in FACTS["topics"]}

# %% [markdown]
# ## Prompts exactly as the application builds them (pipeline.cpp, llama_advisor.cpp)

# %%
PROMPT_TEXT = PROMPT_FILE.read_text(encoding="utf-8")
SYSTEM_T, USER_T = PROMPT_TEXT.split("----USER----")

def fill(template, diagnosis, facts_block):
    """Same as the KR_ADVISOR_PROMPT loader: placeholders replaced, leading/trailing new lines removed."""
    s = template.replace("{language}", "English").replace("{diagnosis}", diagnosis).replace("{facts}", facts_block)
    return s.strip("\n")

def facts_block(facts):
    return "".join(f"{i}. {f}\n" for i, f in enumerate(facts, 1))

def diagnosis_line(t, confidence, spread):
    if t["kind"] == "pest":
        return f"An insect pest was found on the tomato plant: {t['name']}."
    line = f"Diagnosis: {t['name']} on a tomato leaf (model confidence {confidence}%)."
    if spread:
        line += f" Estimated spread on the photographed leaf: {spread}."
    if t["urgent"]:
        line += " This disease is urgent: it spreads very fast."
    if t["reliability"] == "low":
        line += " The photo result is not certain; the farmer should confirm with the local KVK."
    return line

def chat(system, user):
    return ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system + "<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n\n" + user + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")

def make_prompt(t, facts, confidence=92, spread="medium"):
    d = diagnosis_line(t, confidence, spread)
    return chat(fill(SYSTEM_T, d, facts_block(facts)), fill(USER_T, d, facts_block(facts)))

def candidate_facts(t):
    """Extracts of the sections Llama receives (symptoms, cultural), in retrieval order."""
    return [f["text"] for f in t["grounding_facts"] if f["section"] in ("symptoms", "cultural")]

def prompt_variants(t, n, rng):
    """The application's own prompt first, then other fact subsets / orders, confidences and spread levels."""
    facts = candidate_facts(t)
    out = [(list(t["llama_facts"]), 92, "medium")]
    subsets = [list(c) for k in range(2, min(4, len(facts)) + 1) for c in itertools.combinations(facts, k)]
    rng.shuffle(subsets)
    for s in subsets:
        if len(out) >= n:
            break
        rng.shuffle(s)
        out.append((s, rng.choice([71, 78, 85, 90, 94, 97]), rng.choice(["low", "medium", "high", ""])))
    while len(out) < n and len(facts) >= 2:   # topics with few facts: vary only the diagnosis line
        out.append((list(t["llama_facts"]), rng.choice([71, 85, 94, 99]), rng.choice(["low", "high", ""])))
    return out[:n]

usable = [k for k, t in TOPICS.items() if t["kind"] in ("disease", "pest") and len(t["llama_facts"]) >= 2]
train_topics = [k for k in usable if k not in HOLDOUT][:MAX_TRAIN_TOPICS]
rng = random.Random(SEED)
TRAIN_PROMPTS = [(k, f, make_prompt(TOPICS[k], f, c, s)) for k in train_topics
                 for f, c, s in prompt_variants(TOPICS[k], VARIANTS_PER_TOPIC, rng)]
EVAL_PROMPTS = [(k, f, make_prompt(TOPICS[k], f, c, s)) for k in HOLDOUT
                for f, c, s in prompt_variants(TOPICS[k], EVAL_VARIANTS, random.Random(SEED + 1))]
print(f"training topics {len(train_topics)}, training prompts {len(TRAIN_PROMPTS)}, evaluation prompts {len(EVAL_PROMPTS)}")
print(EVAL_PROMPTS[0][2][-700:])

def judge(topic, text):
    """Grounded text and sentence count, plus the application's accept rule (>= 2 grounded sentences)."""
    facts = [f["text"] for f in TOPICS[topic]["grounding_facts"]]
    kept, n, dropped = GROUND.keep_grounded(text, facts)
    return {"kept": kept, "kept_sentences": n, "dropped": dropped, "accepted": n >= MIN_GROUNDED and len(kept) <= 1200}

# %% [markdown]
# ## Model helpers (ExecuTorch's Llama code, Meta checkpoint)

# %%
if not SMOKE:
    from executorch.examples.models.llama.llama_transformer import construct_transformer
    from executorch.examples.models.llama.model_args import ModelArgs
    from pytorch_tokenizers import get_tokenizer
    TOKENIZER = get_tokenizer(str(STUDENT_DIR / "tokenizer.model"))

def encode(text):
    return TOKENIZER.encode(text, bos=False, eos=False, allowed_special="all")

def build_model(ckpt_dir, kv_cache, state=None):
    """Llama from params.json and the original checkpoint (or a given state dict), on the GPU in DTYPE."""
    params = json.load(open(ckpt_dir / "params.json"))
    # enable_dynamic_shape as in the exported model: the prompt goes in at once from position 0 (prefill), then
    # one token per step; without it the cache path expects one position per token (static-shape export)
    args = ModelArgs(max_seq_len=CONTEXT, max_context_len=CONTEXT, use_kv_cache=kv_cache,
                     generate_full_logits=not kv_cache, enable_dynamic_shape=kv_cache, **params)
    model = construct_transformer(args)
    if state is None:
        state = torch.load(ckpt_dir / "consolidated.00.pth", map_location="cpu", mmap=True, weights_only=True)
    missing, unexpected = model.load_state_dict(state, strict=False)
    # only buffers created by the model (KV cache, RoPE tables, masks) may be missing; every weight must load
    assert not unexpected and not [k for k in missing if k.endswith(".weight")], (missing[:5], unexpected[:5])
    return model.to(DEVICE, DTYPE).eval()

def logits_of(out):
    return out[0] if isinstance(out, tuple) else out

@torch.no_grad()
def generate(model, prompt, max_new=MAX_NEW_TOKENS):
    """Greedy decoding with the KV cache (temperature 0, as in the application); stops at the end-of-turn token."""
    ids = encode(prompt)
    out = logits_of(model(torch.tensor([ids], device=DEVICE), {"input_pos": torch.tensor([0], device=DEVICE)}))
    new, pos = [], len(ids)
    for _ in range(max_new):
        nxt = int((out[0, -1] if out.dim() == 3 else out[0]).argmax())
        if nxt in (EOT, EOS) or pos >= CONTEXT - 1:
            break
        new.append(nxt)
        out = logits_of(model(torch.tensor([[nxt]], device=DEVICE), {"input_pos": torch.tensor([pos], device=DEVICE)}))
        pos += 1
    return TOKENIZER.decode(new).strip()

def run_all(model, prompts, label):
    rows, t0 = [], time.time()
    for i, (topic, facts, prompt) in enumerate(prompts):
        text = generate(model, prompt)
        rows.append({"topic": topic, "facts": facts, "text": text, **judge(topic, text)})
        if i % 20 == 0:
            print(f"[{label}] {i + 1}/{len(prompts)} {time.time() - t0:.0f}s | accepted so far "
                  f"{sum(r['accepted'] for r in rows)}/{len(rows)}", flush=True)
    return rows

# %% [markdown]
# ## 1. Teacher (3B) rewrites, filtered by the grounding check -> training targets

# %%
if SMOKE:  # no model: the facts themselves stand in for the teacher text (they pass the check by construction)
    teacher_rows = [{"topic": k, "facts": f, "text": " ".join(f), **judge(k, " ".join(f))} for k, f, _ in TRAIN_PROMPTS]
else:
    teacher = build_model(TEACHER_DIR, kv_cache=True)
    teacher_rows = run_all(teacher, TRAIN_PROMPTS, "teacher 3B")
    del teacher; torch.cuda.empty_cache()

EXAMPLES = []
for (topic, facts, prompt), r in zip(TRAIN_PROMPTS, teacher_rows):
    if r["kept_sentences"] >= MIN_GROUNDED:
        EXAMPLES.append({"topic": topic, "prompt": prompt, "target": r["kept"]})
print(f"teacher answers accepted: {sum(r['accepted'] for r in teacher_rows)}/{len(teacher_rows)}; "
      f"training examples (grounded sentences only): {len(EXAMPLES)}")
with open(WORK_DIR / "train.jsonl", "w", encoding="utf-8") as f:
    for e in EXAMPLES:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
save_json(teacher_rows, "teacher_outputs.json")
for e in EXAMPLES[:3]:
    print("TARGET", e["topic"], ":", e["target"][:300])

# %% [markdown]
# ## 2. Base 1B on the held-out demo diseases (before fine-tuning)

# %%
if not SMOKE:
    student = build_model(STUDENT_DIR, kv_cache=True)
    base_eval = run_all(student, EVAL_PROMPTS, "base 1B")
    del student; torch.cuda.empty_cache()
    save_json(base_eval, "eval_base_1b.json")

# %% [markdown]
# ## 3. LoRA training of the 1B model on the filtered targets

# %%
class LoRALinear(torch.nn.Module):
    """y = W x + (alpha / r) * B A x, with W frozen; B starts at zero so training starts from the base model."""
    def __init__(self, base, r, alpha):
        super().__init__()
        self.base, self.scale = base, alpha / r
        self.A = torch.nn.Parameter(torch.randn(r, base.in_features, device=base.weight.device) / math.sqrt(base.in_features))
        self.B = torch.nn.Parameter(torch.zeros(base.out_features, r, device=base.weight.device))
    def forward(self, x):
        return self.base(x) + ((x.float() @ self.A.t()) @ self.B.t() * self.scale).to(x.dtype)

def add_lora(model):
    wrapped = {}
    for name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if child_name in LORA_TARGETS and isinstance(child, torch.nn.Linear):
                lora = LoRALinear(child, LORA_RANK, LORA_ALPHA)
                setattr(module, child_name, lora)
                wrapped[f"{name}.{child_name}" if name else child_name] = lora
    return wrapped

def tokenize_example(e):
    p, t = encode(e["prompt"]), encode(e["target"]) + [EOT]
    ids = (p + t)[:CONTEXT]
    labels = ([-100] * len(p) + t)[:CONTEXT]      # loss only on the answer
    return torch.tensor(ids), torch.tensor(labels)

if not SMOKE:
    model = build_model(STUDENT_DIR, kv_cache=False)
    for p_ in model.parameters():
        p_.requires_grad_(False)
    LORA = add_lora(model)
    trainable = [p_ for m in LORA.values() for p_ in (m.A, m.B)]
    print(f"LoRA on {len(LORA)} linear layers, {sum(p_.numel() for p_ in trainable) / 1e6:.1f} M trainable parameters")
    opt = torch.optim.AdamW(trainable, lr=LR, weight_decay=0.0)
    data = [tokenize_example(e) for e in EXAMPLES]
    total = EPOCHS * len(data) // GRAD_ACCUM if MAX_STEPS is None else MAX_STEPS
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 10) * 0.5 * (1 + math.cos(math.pi * min(s, total) / max(1, total))))
    model.train(); step, losses, t0 = 0, [], time.time()
    for epoch in range(EPOCHS):
        random.Random(SEED + epoch).shuffle(data)
        for i, (ids, labels) in enumerate(data):
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=DEVICE == "cuda"):
                logits = logits_of(model(ids[None].to(DEVICE)))
            loss = torch.nn.functional.cross_entropy(logits[0, :-1].float(), labels[1:].to(DEVICE), ignore_index=-100)
            (loss / GRAD_ACCUM).backward()
            losses.append(float(loss))
            if (i + 1) % GRAD_ACCUM == 0:
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                opt.step(); sched.step(); opt.zero_grad(set_to_none=True); step += 1
                if step % 10 == 0 or PILOT:
                    print(f"epoch {epoch} step {step}/{total} loss {sum(losses[-GRAD_ACCUM:]) / GRAD_ACCUM:.3f} "
                          f"{time.time() - t0:.0f}s", flush=True)
                if MAX_STEPS and step >= MAX_STEPS:
                    break
        if MAX_STEPS and step >= MAX_STEPS:
            break
    save_json({"losses": losses}, "train_losses.json")

# %% [markdown]
# ## 4. Merge the LoRA weights into the checkpoint and evaluate the fine-tuned 1B on the held-out diseases

# %%
if not SMOKE:
    merged = torch.load(STUDENT_DIR / "consolidated.00.pth", map_location="cpu", weights_only=True)
    with torch.no_grad():
        for name, m in LORA.items():
            key = name + ".weight"
            delta = (m.B.float() @ m.A.float() * m.scale).cpu()
            merged[key] = (merged[key].float() + delta).to(merged[key].dtype)   # stays bfloat16, like the original
    del model, LORA, opt; torch.cuda.empty_cache()
    tuned = build_model(STUDENT_DIR, kv_cache=True, state=merged)
    tuned_eval = run_all(tuned, EVAL_PROMPTS, "LoRA 1B")
    del tuned; torch.cuda.empty_cache()
    save_json(tuned_eval, "eval_lora_1b.json")

    summary = []
    for label, rows in (("base 1B", base_eval), ("LoRA 1B", tuned_eval)):
        summary.append({"model": label, "answers": len(rows), "accepted": sum(r["accepted"] for r in rows),
                        "mean_grounded_sentences": round(sum(r["kept_sentences"] for r in rows) / len(rows), 2),
                        "mean_dropped_sentences": round(sum(len(r["dropped"]) for r in rows) / len(rows), 2)})
    print(json.dumps(summary, indent=1))
    for b, t in zip(base_eval, tuned_eval):
        print(f"\n== {b['topic']}\n BASE  ({b['kept_sentences']} grounded): {b['text'][:350]}\n LoRA  ({t['kept_sentences']} grounded): {t['text'][:350]}")

    CKPT_OUT = Path("/tmp/llama_lora_merged")
    CKPT_OUT.mkdir(parents=True, exist_ok=True)
    torch.save(merged, CKPT_OUT / "consolidated.00.pth")
    shutil.copy(STUDENT_DIR / "params.json", CKPT_OUT / "params.json")
    shutil.copy(STUDENT_DIR / "tokenizer.model", WORK_DIR / "llama3_2_tokenizer.model")
    del merged

# %% [markdown]
# ## 5. Export with the deployed settings and check the .pte with the application's runner

# %%
if not SMOKE and not PILOT:
    export_args = [
        "base.model_class=llama3_2", f"base.checkpoint={CKPT_OUT / 'consolidated.00.pth'}",
        f"base.params={CKPT_OUT / 'params.json'}",
        'base.metadata="{\\"get_bos_id\\":128000, \\"get_eos_ids\\":[128009, 128001]}"',
        "model.use_kv_cache=True", "model.use_sdpa_with_kv_cache=True", "model.dtype_override=fp32",
        f"export.max_seq_length={CONTEXT}", f"export.max_context_length={CONTEXT}",
        "backend.xnnpack.enabled=True", "backend.xnnpack.extended_ops=True",
        "quantization.qmode=8da4w", "quantization.group_size=32", 'quantization.embedding_quantize="4,32"',
        f"export.output_name={OUT_NAME}"]
    t0 = time.time()
    with open(WORK_DIR / "export.log", "w") as log:
        proc = subprocess.run([sys.executable, "-m", "executorch.extension.llm.export.export_llm", *export_args],
                              cwd=WORK_DIR, stdout=log, stderr=subprocess.STDOUT)
    print(f"export exit code {proc.returncode} after {(time.time() - t0) / 60:.0f} min, peak RAM "
          f"{resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 2**20:.1f} GB")
    assert proc.returncode == 0, "export failed - see export.log"

    import executorch.extension.llm.custom_ops.custom_ops  # noqa: F401  (operators used by the .pte)
    import executorch.kernels.quantized  # noqa: F401
    from executorch.extension.llm.runner import GenerationConfig, TextLLMRunner
    runner = TextLLMRunner(str(WORK_DIR / OUT_NAME), str(WORK_DIR / "llama3_2_tokenizer.model"))
    pte_eval = []
    for topic, facts, prompt in EVAL_PROMPTS:
        pieces = []
        runner.reset()
        runner.generate(prompt, GenerationConfig(echo=False, max_new_tokens=MAX_NEW_TOKENS, temperature=0.0,
                                                 num_bos=0, num_eos=0), token_callback=pieces.append)
        text = "".join(pieces).replace("<|eot_id|>", "").strip()
        pte_eval.append({"topic": topic, "text": text, **judge(topic, text)})
    save_json(pte_eval, "eval_lora_1b_pte_int4.json")
    summary.append({"model": "LoRA 1B, exported INT4 .pte", "answers": len(pte_eval),
                    "accepted": sum(r["accepted"] for r in pte_eval),
                    "mean_grounded_sentences": round(sum(r["kept_sentences"] for r in pte_eval) / len(pte_eval), 2)})
    print(json.dumps(summary[-1], indent=1))

if not SMOKE:
    save_json({"summary": summary, "holdout_topics": HOLDOUT, "train_topics": train_topics,
               "train_examples": len(EXAMPLES), "lora": {"rank": LORA_RANK, "alpha": LORA_ALPHA, "targets": LORA_TARGETS,
                                                          "lr": LR, "epochs": EPOCHS, "grad_accum": GRAD_ACCUM},
               "pilot": PILOT, "packages": PACKAGES}, "summary.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
