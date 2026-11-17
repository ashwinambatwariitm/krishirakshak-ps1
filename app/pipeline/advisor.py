"""Advisory stage: Llama 3.2 1B Instruct running on the device through ExecuTorch (the "G" of the RAG system).

Note: the Python package app/ is the reference implementation (used as the test oracle for the C++ vision code,
tools/cpp_parity.py). The deployed application is the C++ binary in cpp/, whose advisor uses a stricter
rephrase-only prompt and the sentence-level grounding check in cpp/src/output_guard.cpp.

Llama receives the diagnosis and the verified extracts retrieved from the knowledge base (ICAR, NIPHM, TNAU) and
writes a short explanation in English or Hindi. It does not diagnose and does not write spray doses: spray options
are shown to the farmer exactly as published, in a separate table with their source. Every answer passes the output
check in guard.py; if it fails, the application shows the verified extracts without the Llama text.

The model is a .pte file exported once on a PC (llm/export_llama.sh) and loaded from local disk; nothing is
downloaded at run time. If the .pte file is missing, the advisor runs in "template" mode (extracts only), so the rest
of the application can be developed and tested without it.
"""
import time
from pathlib import Path

LANG_NAME = {"en": "English", "hi": "Hindi"}

SYSTEM_PROMPT = (
    "You are KrishiRakshak, an assistant for tomato farmers in India. "
    "Use ONLY the FACTS given by the user. Do not add any other fact. "
    "Do not name any pesticide or chemical and do not give any dose or quantity: the spray options are shown to the "
    "farmer separately. Write in simple {language} for a farmer, in 3 to 5 short sentences. "
    "Do not use lists, headings or English words if the language is Hindi."
)

FOLLOWUP_SYSTEM_PROMPT = (
    "You are KrishiRakshak, an assistant for tomato farmers in India. "
    "Answer the farmer's question using ONLY the FACTS given by the user. "
    "If the FACTS do not answer the question, say that you do not know and suggest asking the local KVK. "
    "Copy any product name and dose exactly as written in the FACTS. "
    "Write in simple {language}, in at most 4 short sentences."
)


def llama3_chat(system, user):
    """Llama 3 instruct chat format (the tokenizer turns the special tokens into their ids)."""
    return ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system + "<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n\n" + user + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")


def facts_block(facts):
    """Numbered list of the non-spray extracts given to Llama (spray rows are left out on purpose)."""
    lines = [f"{i}. {c['text']}" for i, c in enumerate((c for c in facts if c["section"] != "chemical"), start=1)]
    return "\n".join(lines)


class LlamaAdvisor:
    """Wraps the ExecuTorch TextLLMRunner. Load once at start-up; generate() is called per request."""

    def __init__(self, pte_path, tokenizer_path, max_new_tokens=160, temperature=0.0):
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.runner = None
        self.load_seconds = None
        self.pte_path, self.tokenizer_path = Path(pte_path), Path(tokenizer_path)
        if self.pte_path.exists() and self.tokenizer_path.exists():
            # Imported here so the vision-only mode works without ExecuTorch installed.
            # The two imports register the LLM operators used by the exported graph (custom SDPA attention,
            # quantized 4-bit embedding); without them loading the 'forward' method fails.
            import executorch.extension.llm.custom_ops.custom_ops  # noqa: F401
            import executorch.kernels.quantized  # noqa: F401
            from executorch.extension.llm.runner import TextLLMRunner
            start = time.perf_counter()
            self.runner = TextLLMRunner(str(self.pte_path), str(self.tokenizer_path))
            self.load_seconds = time.perf_counter() - start

    @property
    def available(self):
        return self.runner is not None

    def generate(self, prompt):
        """Run Llama on one prompt; returns (text, stats dict with time to first token and tokens per second)."""
        from executorch.extension.llm.runner import GenerationConfig
        pieces, stats_holder = [], {}
        config = GenerationConfig(echo=False, max_new_tokens=self.max_new_tokens, temperature=self.temperature,
                                  num_bos=0, num_eos=0)
        self.runner.reset()                       # clear the KV cache of the previous request
        start = time.perf_counter()
        self.runner.generate(prompt, config, token_callback=pieces.append,
                             stats_callback=lambda s: stats_holder.update(s=s))
        total = time.perf_counter() - start
        text = "".join(pieces).replace("<|eot_id|>", "").strip()
        s = stats_holder.get("s")
        stats = {"total_s": round(total, 2)}
        if s is not None:
            gen_ms = max(1, s.inference_end_ms - s.first_token_ms)
            stats.update(prompt_tokens=s.num_prompt_tokens, generated_tokens=s.num_generated_tokens,
                         time_to_first_token_s=round((s.first_token_ms - s.inference_start_ms) / 1000, 2),
                         tokens_per_s=round(s.num_generated_tokens * 1000 / gen_ms, 1))
        return text, stats

    def advise(self, diagnosis_line, facts, lang):
        """Explanation of a diagnosis from the retrieved extracts."""
        system = SYSTEM_PROMPT.format(language=LANG_NAME[lang])
        user = f"{diagnosis_line}\n\nFACTS:\n{facts_block(facts)}\n\nExplain this to the farmer and say what to do first."
        return self.generate(llama3_chat(system, user))

    def answer(self, question, facts, lang):
        """Answer to a follow-up question from the retrieved extracts (spray rows included, doses copied)."""
        system = FOLLOWUP_SYSTEM_PROMPT.format(language=LANG_NAME[lang])
        lines = "\n".join(f"{i}. {c['text']}" for i, c in enumerate(facts, start=1))
        user = f"QUESTION: {question}\n\nFACTS:\n{lines}"
        return self.generate(llama3_chat(system, user))
