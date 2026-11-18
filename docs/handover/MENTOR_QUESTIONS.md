# KrishiRakshak (PS1) - questions for mentor guidance

| | |
|---|---|
| Team | KrishiRakshak - Bharat AI-SoC Challenge 2026-27, Problem Statement 1 (Agriculture and Food Security) |
| Date | 18 November 2026 (Phase 1 submission due Monday, 23 November 2026) |
| Contact | Ashwin Ambatwar |
| Request | Guidance on the questions below - a short call or written answers. Questions 1, 2, 4 and 6 matter most for the remaining days. |

## Where the project stands

Everything runs offline on a **Raspberry Pi 5 (8 GB, CPU only)**, in one C++ program:

| Part | What it does | Result so far |
|---|---|---|
| Disease classifier | EfficientNet-B0, 6 tomato classes incl. healthy (ONNX Runtime, INT8 mixed precision) | 98.7% on lab photos (PlantVillage); 76% on real field photos (PlantDoc); with an "uncertain" threshold it answers 70% of field photos at 88% accuracy |
| Pest detector | YOLOv8n, 102 IP102 insect species, trained with insect-free leaves to avoid false alarms | IP102 mAP50 0.57; insects found 92%; false alarms 0.3% (lab) / 5% (field) |
| Advice | 681 verified extracts from ICAR, NIPHM and TNAU publications (English and Hindi), each with its source; spray options copied exactly | draft, not yet reviewed by an expert |
| Llama | Llama 3.2 1B Instruct through ExecuTorch (INT4, XNNPACK); rewrites the retrieved extracts in simple words; every sentence is checked against the sources before it is shown | 1B: about 13 tokens/s, about 15 s per answer; 3B: about 4.7 tokens/s, about 45 s |
| App | mobile web app served by the Pi over its own Wi-Fi hotspot, opened in the farmer's phone browser | in development, ready Friday |

## Questions

1. **Role of Llama.** Llama only rewrites the retrieved, verified extracts; a grounding check removes any sentence not supported by a source, and if too little remains the farmer sees the extracts only. Is this a strong enough demonstration of "Llama for advisory / reasoning", or do judges expect Llama to play a bigger role (for example answering free questions)?
2. **Llama 3.2 1B or 3B on the Pi.** 1B runs at about 13 tokens/s (about 15 s per answer); 3B at about 4.7 tokens/s (about 45 s) with better wording. Which matters more to the jury for the demo - response time or answer quality? Is about 45 s acceptable for a farmer use case?
3. **Hindi.** Llama 1B produced unreliable Hindi, so for Hindi the app shows reviewed Hindi extracts and no Llama text. Is that acceptable for the "multiple local languages" requirement in Phase 1?
4. **Evaluating the LLM part.** We report the share of answers that pass the grounding check, grounded sentences per answer, refusals, and manually checked distortions. Is this the kind of evaluation judges expect, or should we add standard metrics or a small human rating study?
5. **Fine-tuning.** We are distilling Llama 3B outputs (filtered by the grounding check) into a LoRA-tuned Llama 1B. Is a fine-tuned or distilled variant valued enough in judging to be worth the time before 23 November?
6. **Vision accuracy.** On real field photos the 6-class model reaches 76% (88% on the 70% of photos it answers, "uncertain" otherwise; 99.6% on lab photos). Is this adequate for Phase 1, or should we prioritise collecting our own field photos?
7. **App form.** The app is a mobile web app served by the Pi over its own Wi-Fi hotspot and opened in the phone browser, fully offline. Does this count as a mobile app for PS1, or is a native Android app expected?
8. **Arm optimisation.** Vision runs INT8 (mixed precision) with ONNX Runtime and Llama INT4 with XNNPACK (KleidiAI kernels on Arm). Is CPU-only on the Pi 5 fine, or would using an NPU (AI HAT+ / Hailo) earn more credit?
9. **Expert review.** Can the mentors connect us with an agronomist or KVK expert to review the advice content and the Hindi translations (currently marked as a draft)?
10. **Submission.** Expected structure and length of the technical report, length of the demo video, and whether the repository must be public for judging (ours is private; model files are in private GitHub releases).

Thank you for your time and guidance.
