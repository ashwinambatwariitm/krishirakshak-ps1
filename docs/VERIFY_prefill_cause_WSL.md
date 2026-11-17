# Prefill cause measurements on the WSL build machine (branch llama-prefix-cache)

- Branch: `llama-prefix-cache`, commit `a7c1377`; existing build `build/x86-llm` (built from `a7c1377`, ExecuTorch 1.5.1)
- Machine: development PC (Intel i5-12500H, WSL2, Ubuntu 22.04, 12 GB RAM for WSL)
- Date: 17 November 2026
- Prompt files from the previous run, still present: `/tmp/prompt_late.txt` (295 tokens), `/tmp/prompt_ask.txt`
  (383 tokens), `/tmp/prompt_early.txt` (243 tokens, not used here)
- M4 = `models/llama3_2_1b_instruct_8da4w.pte`, T = `models/llama3_2_tokenizer.model`
- No code was changed and nothing was committed to `llama-prefix-cache`, `pi-perf-model` or `main`. This report is the
  only commit, on branch `verify/prefill-cause-wsl`.

## Summary

| Step | Result |
|---|---|
| 1. FP32 model, same splits | **Skipped: no FP32 `.pte` exists** (none was exported; not exported now, as instructed) |
| 2. INT4 model, very short second chunk | Done, exit 0 for both commands; tables below |
| 3. FP32 model, short second chunk | **Skipped: no FP32 `.pte` exists** |

Answers:

- FP32 `max_abs_diff` close to 0 or similar to INT4? **Not measured**: there is no FP32 `.pte` on this machine.
- INT4 `max_abs_diff` with a second chunk of 1 - 15 tokens: **it depends on the chunk length.** With 1 or 2 tokens
  it is exactly 0.000000 on both prompts; with 4, 8 and 15 tokens it is 1.01 - 1.89, i.e. in the same range as the
  longer splits of the previous report (about 1 - 2.6). `same_top1` is yes in every row.

## FP32 model (steps 1 and 3) - not available

```
$ ls -la /mnt/c/krishirakshak_store/llama_export/*.pte
ls: cannot access '/mnt/c/krishirakshak_store/llama_export/*.pte': No such file or directory
```

The only `.pte` on the machine is the INT4 model in `models/` (860,434,816 bytes); a search for `*fp32*.pte` under the
home folder and `/mnt/c/krishirakshak_store` found nothing. The FP32 baseline export (`llm/export_llama.sh fp32`) was
planned but never run. Steps 1 and 3 were skipped, so no peak memory figure for the FP32 model is reported.

## Step 2 - INT4 model, very short second chunk (full output)

```
$ build/x86-llm/prefill_check $M4 $T /tmp/prompt_late.txt 294 293 291 287 280
prompt tokens 295, single prefill top1 40 (margin 2.0284)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   294           1     0.000000        40         40      2.0284       yes
   293           2     0.000000        40         40      2.0284       yes
   291           4     1.894438        40         40      2.0284       yes
   287           8     1.784642        40         40      2.0284       yes
   280          15     1.255545        40         40      2.0284       yes
exit 0
```

```
$ build/x86-llm/prefill_check $M4 $T /tmp/prompt_ask.txt 382 381 379 375
prompt tokens 383, single prefill top1 8586 (margin 0.2578)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   382           1     0.000000      8586       8586      0.2578       yes
   381           2     0.000000      8586       8586      0.2578       yes
   379           4     1.012055      8586       8586      0.2578       yes
   375           8     1.139595      8586       8586      0.2578       yes
exit 0
```

## All INT4 rows with max_abs_diff = 0 so far (this run and the previous report)

| prompt | k | rest_tokens | max_abs_diff |
|---|---|---|---|
| late | 294 | 1 | 0.000000 |
| late | 293 | 2 | 0.000000 |
| ask | 382 | 1 | 0.000000 |
| ask | 381 | 2 | 0.000000 |
| ask | 192 | 191 | 0.000000 (previous report) |
| ask | 97 | 286 | 0.000000 (previous report) |

Every other split measured so far (second chunk of 4 - 285 tokens on the late and early prompts, 4 - 250 tokens on
the ask prompt) gives 0.95 - 2.61.

## Observations (no conclusions drawn beyond the data)

- A second chunk of 1 or 2 tokens reproduces the single prefill exactly, so continuing from a KV cache filled by an
  earlier call is exact in those cases (a normal decode step after a prefill is the 1-token case).
- From 4 tokens on, the result differs by about 1 - 1.9 logit units, with no trend towards 0 as the second chunk gets
  shorter (15 -> 8 -> 4 tokens: 1.26, 1.78, 1.89 on the late prompt).
- The two exact matches of the previous report on the ask prompt (second chunk of 191 and 286 tokens) do not follow
  the "1 or 2 tokens" pattern; this run does not explain them.
- 3 tokens was not measured (not in the requested split points).
