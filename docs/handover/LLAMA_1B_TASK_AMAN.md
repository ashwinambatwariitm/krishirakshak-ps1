# Llama 3.2 1B advisor quality - work order and step-by-step guide

| | |
|---|---|
| Requested by | KrishiRakshak core team - contact: Ashwin Ambatwar |
| Assigned to | Aman - Llama advisor quality |
| Issued | Wednesday, 18 November 2026 |
| Proposed checkpoints | First results Thursday 19 November (evening); final results Friday 20 November |
| Why | Phase 1 submission (report, code, demo video) is due Monday 23 November 2026 |
| Hardware needed | A laptop only (Linux or Windows with WSL2). No Raspberry Pi, no photos. |
| Copy commands from | `docs/handover/LLAMA_1B_TASK_AMAN.md` in the repository (long lines are wrapped in the PDF) |

## 1. What the task is

After the vision models identify a disease, the application retrieves verified extracts (ICAR, NIPHM, TNAU) for it
and asks **Llama 3.2 1B Instruct** (running through ExecuTorch on the Raspberry Pi 5) to rewrite them in simple words
for the farmer. Every sentence Llama writes is then checked against the extracts (the "grounding check",
`cpp/src/output_guard.cpp`): a sentence is kept only if at least 75% of its content words appear in ONE source
sentence, it does not reverse an instruction ("do not ..."), does not invent a cause ("caused by ...") and does not
change a number. The application shows the Llama text only if **at least two sentences** survive; otherwise the farmer
sees only the extracts.

Today Llama 1B passes this check for only about half of the diseases. **The task: make the 1B model's answers pass
the check more often without making them less correct** - by improving the prompt (main lever), and optionally the
fine-tuned model (LoRA). Making the check weaker is not allowed.

## 2. Why a laptop is enough (the "simulator")

The application uses greedy decoding (temperature 0). The same `.pte` model file run by the same ExecuTorch runtime on a
laptop CPU produces the same text as on the Pi; only the speed differs. So the laptop is a faithful simulator for answer
quality. The Pi is needed only for timing and memory, which the core team measures after your changes.

The tool `llm/eval_advisor.py` builds exactly the prompt the application builds (diagnosis line + the facts Llama
receives, including the application's retry after a refusal), runs the model, and scores every answer with a Python
copy of the application's check (`llm/grounding.py`, verified to give identical decisions on 34 real answers).

## 3. What "accuracy" means here (the numbers to improve)

| Metric | Meaning | Current (1B, built-in prompt) | Target |
|---|---|---|---|
| Accepted, demo diseases | answers the app would show, out of the 6 demo diseases | 3 / 6 | 5 / 6 or better |
| Accepted, all topics | out of the 27 diseases and pests with 2+ facts | measure on day 1 | 70% or better |
| Refusals | first answer was "I can't ..." (the app retries once) | 2 / 6 | 0 |
| Grounded sentences | sentences kept per answer (more = more useful) | 3.5 on average | higher |
| Distortions | kept sentences that change the meaning of the source (manual review) | must stay 0 | 0 |

Baseline answers of the 6 demo diseases (laptop, 18 November): healthy leaf and septoria leaf spot were refused and the
retry was not grounded; bacterial spot invented causes ("The disease is caused by moist weather"), which the check
correctly removed; early blight, late blight and yellow leaf curl virus were accepted.

## 4. Set-up (about 30 minutes, once)

Requirements: Ubuntu 22.04 or newer (on Windows: WSL2 with Ubuntu), Python 3.10+, git, about 4 GB free RAM and 3 GB
free disk, and access to the GitHub repository `ashwinambatwariitm/krishirakshak-ps1` (ask Ashwin).

**Step 1 - get the code**
```
git clone git@github.com:ashwinambatwariitm/krishirakshak-ps1.git
cd krishirakshak-ps1
git checkout app-handover-llama-3b
git checkout -b llama-1b-quality-aman
```

**Step 2 - Python environment with ExecuTorch** (the exact versions used for the deployed model)
```
python3 -m venv ~/.venvs/et
source ~/.venvs/et/bin/activate
pip install --upgrade pip
pip install --extra-index-url https://download.pytorch.org/whl/cpu torch==2.14.1 torchao==0.18.0 executorch==1.5.1
python -c "import executorch, torch; print('ok', torch.__version__)"
```

**Step 3 - download the model** (private release `llm-v1`: model, tokenizer, Llama licence and notice)
```
# with the GitHub CLI (gh auth login once), or download the files from the Releases page of the repository
gh release download llm-v1 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
cd models && sha256sum -c SHA256SUMS.txt && cd ..
```
Both lines must print `OK`. The model is Llama 3.2 1B Instruct, INT4 (8da4w, XNNPACK), about 860 MB.

**Step 4 - first run** (one disease, about 30 s)
```
python -m llm.eval_advisor --pte models/llama3_2_1b_instruct_8da4w.pte \
    --tokenizer models/llama3_2_tokenizer.model --topics late_blight --out results/llama_eval/smoke
```
It prints `ACCEPT` or `REJECT` with the numbers of grounded and dropped sentences. The line
`E tokenizers ... Error parsing json file` is harmless (the runner first tries another tokenizer format).

**Step 5 - baseline** (write these numbers down; everything is compared with them)
```
python -m llm.eval_advisor --pte models/llama3_2_1b_instruct_8da4w.pte --tokenizer models/llama3_2_tokenizer.model \
    --topics demo --out results/llama_eval/baseline_demo
python -m llm.eval_advisor --pte models/llama3_2_1b_instruct_8da4w.pte --tokenizer models/llama3_2_tokenizer.model \
    --topics all --out results/llama_eval/baseline_all
```
`demo` = the 6 demo diseases (about 3 minutes); `all` = 27 diseases and pests (about 15 minutes).

## 5. Inputs in the repository

| Path | What it is | How to use it |
|---|---|---|
| `llm/eval_advisor.py` | the evaluation tool | `--prompt FILE` to test a prompt variant, `--topics demo / all / a,b,c` |
| `prompts/advise_keep_words.txt` | the current prompt (identical to the built-in prompt of the C++ app) | copy it and edit the copy |
| `results/llama_lora/prompt_facts.json` | for all 43 topics: `llama_facts` (the extracts Llama receives) and `grounding_facts` (all extracts the check accepts as sources), plus the check's word lists | read to understand what Llama sees |
| `app/kb/tomato_kb.json` | the full knowledge base: every extract with its section and source | background |
| `llm/grounding.py` | the grounding check in Python | read the rules; do not change without the core team |
| `cpp/src/output_guard.cpp` | the original check in C++ (runs on the Pi) | reference |
| `cpp/tests/grounding_test.cpp` | real unsafe sentences that must stay rejected, and good rewrites that must pass | add every new unsafe sentence you find |
| `docs/api_examples/analyse_en_early_blight.json` | a full application answer with `llama.raw_text`, `llama.text` and `llama.dropped_sentences` | shows how the answer reaches the farmer |
| `cpp/src/llama_advisor.cpp` | where the C++ app builds the prompt and the refusal retry | changes to the retry prompt go here (core team builds) |
| `training/src/llama_lora_distill.py` | LoRA fine-tuning notebook (Kaggle GPU): 3B teacher, filtered by the check, LoRA on 1B | optional second lever, see section 7 |

Photos are not needed: Llama's input is the diagnosis line and the facts, not the image. For end-to-end tests with
photos, the field test photos are in the PlantDoc dataset (`https://github.com/pratikkayal/PlantDoc-Dataset`, folders
`test/Tomato*`); the core team runs those on the Pi.

## 6. Experiment loop (repeat for every idea)

1. Copy the prompt: `cp prompts/advise_keep_words.txt prompts/aman_v1.txt` and change one thing.
   Format: system text, a line `----USER----`, user text; placeholders `{language}`, `{diagnosis}`, `{facts}`.
2. Run the 6 demo diseases: `python -m llm.eval_advisor ... --prompt prompts/aman_v1.txt --topics demo --out results/llama_eval/aman_v1_demo`
3. Read `results/llama_eval/aman_v1_demo/answers.json`: for each topic `answer` (raw text), `kept` (what the farmer
   would see), `dropped_sentences` and, after a refusal, `first_answer`.
4. **Check every kept sentence against the facts** (`facts` in the same file). A kept sentence that changes the meaning
   (wrong cause, wrong plant part, an instruction made stronger or weaker) is a distortion: note it, add it to
   `cpp/tests/grounding_test.cpp` as a "dropped" case, and tell the core team.
5. If the demo result improves, run `--topics all` to make sure the change helps in general and is not tuned to six
   cases.
6. Record the result in your log (table: variant, change, demo accepted, all accepted, refusals, mean grounded,
   distortions).

## 7. Ideas to try (most promising first)

1. **Refusals.** The 1B model refuses some prompts ("I can't fulfill your request"). Try softer wording of the task,
   removing words that may trigger safety refusals, putting the task in the user message instead of the system
   message, or a different one-shot example. Also try better fallback prompts (the retry in `llama_advisor.cpp`); the
   tool uses the same retry text - edit `fallback_prompt()` in `llm/eval_advisor.py` to test variants.
2. **Format.** Accepted answers still lose many sentences: list markers ("I.", "1."), titles and introductions count
   as dropped sentences. Ask for plain sentences more firmly or show it in the example.
3. **One sentence per source sentence.** Facts often contain several sentences; a rewrite that merges two of them fails
   (each sentence must be supported by ONE source sentence). Ask to rewrite each source sentence separately.
4. **Keep the key words.** The check matches words; rewrites that keep the technical words of the source pass
   ("concentric rings", "margin", "lesions", "crop debris"). Strengthen this in the prompt and the example.
5. **Order and number of facts.** Llama gets up to four extracts (symptoms and cultural practices). Test whether fewer
   or shorter facts give better answers (tell the core team; this is changed in the C++ app).
6. **Length.** The answer is cut at 160 new tokens; a cut sentence is dropped. Shorter answers may pass more often.
7. **LoRA fine-tuning (optional, with Ashwin).** A notebook already distils 3B rewrites (filtered by the check) into
   the 1B model on a Kaggle GPU. If prompting stalls, the best prompt can be used to generate better training data.

Rules: never lower the 0.75 threshold or remove a check to get more answers accepted; never add facts to the prompt
that are not in the knowledge base; keep English only (the application shows reviewed extracts for Hindi).

## 8. Deliverables

| # | Deliverable |
|---|---|
| D1 | The best prompt as `prompts/<name>.txt` and, if better, an improved fallback prompt |
| D2 | `results/llama_eval/<run>/summary.json` and `answers.json` for the baseline and the best variants (demo and all) |
| D3 | A short report `docs/llama_1b_quality.md`: log table of all variants, what helped and why, distortions found |
| D4 | New cases in `cpp/tests/grounding_test.cpp` for any unsafe sentence found (the core team runs the C++ test) |
| D5 | A pull request from branch `llama-1b-quality-aman` |

After the hand-over the core team tries the best prompt on the Pi (`KR_ADVISOR_PROMPT=prompts/<name>.txt`), measures
speed, and makes it the built-in prompt.

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `E tokenizers ... Error parsing json file` | harmless |
| `UnicodeDecodeError` | only with Hindi output; the tool is English only |
| Laptop slow or out of memory | close other programs; the 1B model needs about 1.5 GB; use `--topics a,b` for fewer topics |
| `ModuleNotFoundError: llm` | run from the repository root with `python -m llm.eval_advisor` |
| `sha256sum` reports FAILED | download the file again |
| Different results from run to run | should not happen (greedy decoding); check that the same prompt file and model were used |

## 10. Contact

Questions go to the team WhatsApp group. Technical contact (model, Pi, grounding check): Ashwin Ambatwar.
Llama 3.2 is licensed under the Llama 3.2 Community License, Copyright (c) Meta Platforms, Inc. All Rights Reserved.
