"""Coordinator: runs the whole offline pipeline for one photo and returns one structured result.

    photo -> quality gate -> disease classifier + pest detector (ONNX Runtime)
          -> decision (answer / uncertain) -> estimated severity
          -> retrieval of verified extracts (SQLite) -> Llama explanation (ExecuTorch) -> output check
          -> result dictionary (shown by the Flask user interface, or printed as JSON by run_pipeline.py)

All models are loaded once in Pipeline.__init__ and stay in memory; requests run one after the other
(vision first, then Llama), which keeps peak memory low on the Raspberry Pi 5.
"""
import os
import time
from pathlib import Path

# The application must never reach the internet: make any accidental Hugging Face access fail immediately.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from .advisor import LlamaAdvisor            # noqa: E402
from .guard import check_output              # noqa: E402
from .knowledge import KnowledgeBase         # noqa: E402
from .quality import check_quality           # noqa: E402
from .severity import SeverityModel      # noqa: E402
from .pest_severity import pest_severity      # noqa: E402
from .vision import DiseaseClassifier, PestDetector   # noqa: E402

REPO = Path(__file__).resolve().parents[2]

DEFAULT_CONFIG = {
    "disease_onnx": REPO / "models" / "tomato_disease_v5_effb0_6class.onnx",
    "disease_spec": REPO / "results" / "int8_ptq" / "tomato_disease_v5_effb0_6class.json",
    "pest_onnx": REPO / "models" / "pest_yolov8n_ip102_negatives.onnx",
    "pest_spec": REPO / "results" / "int8_ptq" / "pest_yolov8n_ip102_negatives.json",
    "pest_labels": REPO / "results" / "pest_yolov8n_with_negatives" / "pest_labels.json",
    "pest_config": REPO / "results" / "pest_yolov8n_with_negatives" / "pest_config.json",
    "kb_db": REPO / "app" / "kb" / "tomato_kb.sqlite",
    "kb_json": REPO / "app" / "kb" / "tomato_kb.json",
    # KR_LLAMA_PTE selects another .pte (e.g. models/llama3_2_3b_instruct_8da4w.pte); the tokenizer is shared
    "llama_pte": Path(os.environ["KR_LLAMA_PTE"]) if os.environ.get("KR_LLAMA_PTE")
                 else REPO / "models" / "llama3_2_1b_krishirakshak_lora_8da4w.pte",   # LoRA-tuned 1B (default)
    "llama_tokenizer": REPO / "models" / "llama3_2_tokenizer.model",
    "severity_onnx": REPO / "models" / "severity_lraspp_mnv3.onnx",
    "severity_spec": REPO / "results" / "severity" / "severity_spec.json",
    "disease_threshold": 0.85,     # results/disease_v5_threshold/threshold.json
    "threads": 4,                  # Raspberry Pi 5: four Cortex-A76 cores
    "use_llama": True,
}


class Pipeline:
    """Loads every model once; analyse() handles one photo, follow_up() one question."""

    def __init__(self, **overrides):
        cfg = {**DEFAULT_CONFIG, **overrides}
        self.cfg = cfg
        t0 = time.perf_counter()
        self.disease = DiseaseClassifier(cfg["disease_onnx"], cfg["disease_spec"], cfg["threads"])
        self.pest = PestDetector(cfg["pest_onnx"], cfg["pest_spec"], cfg["pest_labels"], cfg["pest_config"],
                                 cfg["threads"])
        if not Path(cfg["kb_db"]).exists() or Path(cfg["kb_db"]).stat().st_mtime < Path(cfg["kb_json"]).stat().st_mtime:
            from app.kb.build_kb import build      # (re)build the SQLite file from the reviewed JSON
            build(cfg["kb_json"], cfg["kb_db"])
        self.kb = KnowledgeBase(cfg["kb_db"], cfg["kb_json"])
        self.severity = SeverityModel(cfg["severity_onnx"], cfg["severity_spec"])
        self.advisor = LlamaAdvisor(cfg["llama_pte"], cfg["llama_tokenizer"]) if cfg["use_llama"] else None
        self.load_seconds = round(time.perf_counter() - t0, 2)

    @property
    def llama_ready(self):
        return self.advisor is not None and self.advisor.available

    def info(self):
        """Model and runtime description for the user interface and the report."""
        return {"disease_model": self.disease.name, "pest_model": self.pest.name,
                "llama": self.cfg["llama_pte"].name if self.llama_ready else "not loaded (template mode)",
                "kb_version": self.kb.meta["version"], "kb_reviewed": self.kb.meta["content_reviewed"],
                "load_seconds": self.load_seconds}

    def analyse(self, image_rgb, lang="en"):
        """Full pipeline for one RGB photo; returns a JSON-serialisable result dictionary."""
        timings = {}
        result = {"lang": lang, "timings_ms": timings}

        t = time.perf_counter()
        quality = check_quality(image_rgb)
        timings["quality"] = _ms(t)
        result["quality"] = quality
        if not quality["ok"]:
            result["status"] = "retake_photo"
            result["messages"] = [self.kb.messages["quality"][issue][lang] for issue in quality["issues"]]
            return result

        t = time.perf_counter()
        ranking = self.disease.predict(image_rgb)
        timings["disease"] = _ms(t)
        t = time.perf_counter()
        pests = self.pest.predict(image_rgb)
        timings["pest"] = _ms(t)

        top = ranking[0]
        answered = top["probability"] >= self.cfg["disease_threshold"]
        topic = top["class"] if answered else None
        result["disease"] = {"top": ranking[:3], "answered": answered, "topic": topic,
                             "name": self.kb.topic_name(topic, lang) if topic else None,
                             "reliability": self.kb.topics[topic]["model_reliability"] if topic else None,
                             "urgent": bool(topic and self.kb.topics[topic]["urgent"])}
        for p in pests:
            p["topic"] = self.kb.pest_topic(p["species_id"], p["species_reliable"])
            p["name"] = self.kb.topic_name(p["topic"], lang)
        result["pests"] = pests
        # Pest severity of this photo (one level per pest topic, with the published scouting method)
        result["pest_severity"] = pest_severity(pests, self.kb, image_rgb.shape[1], image_rgb.shape[0], lang)

        if topic and topic != "healthy":
            t = time.perf_counter()
            result["severity"] = self.severity.estimate(image_rgb, topic)
            timings["severity"] = _ms(t)

        # Verified extracts: the diagnosed disease first, then each distinct pest topic
        t = time.perf_counter()
        topics = ([topic] if topic else []) + sorted({p["topic"] for p in pests})
        result["advice_blocks"] = [{"topic": tp, "name": self.kb.topic_name(tp, lang),
                                    "chunks": self.kb.retrieve_for_diagnosis(tp, lang)} for tp in topics]
        timings["retrieval"] = _ms(t)

        messages = []
        if not answered:
            messages.append(self.kb.message("uncertain", lang))
        if topic and self.kb.topics[topic]["model_reliability"] == "low":
            messages.append(self.kb.message("expert_confirm", lang))
        if any(not p["species_reliable"] for p in pests):
            messages.append(self.kb.message("pest_species_uncertain", lang))
        if any(c["section"] == "chemical" for b in result["advice_blocks"] for c in b["chunks"]):
            messages.append(self.kb.message("chemical_rule", lang))
        result["messages"] = messages
        result["status"] = "answered" if topics else "uncertain"

        # Llama explanation of the main finding (the disease, or the first pest when the disease is uncertain)
        result["llama"] = None
        if self.llama_ready and result["advice_blocks"]:
            block = result["advice_blocks"][0]
            line = self._diagnosis_line(result, block["topic"], lang)
            t = time.perf_counter()
            text, stats = self.advisor.advise(line, block["chunks"], lang)
            timings["llama"] = _ms(t)
            ok, reasons = check_output(text, block["chunks"], lang, diagnosed_topic=block["topic"])
            result["llama"] = {"text": text if ok else None, "accepted": ok, "rejected_reasons": reasons,
                               "raw_text": text, "stats": stats}
        timings["total"] = sum(v for v in timings.values())
        return result

    def follow_up(self, question, topic=None, lang="en"):
        """Answer a typed follow-up question from the knowledge base (BM25 retrieval + Llama)."""
        facts = self.kb.search(question, topic=topic, k=4, lang=lang)
        out = {"question": question, "facts": facts, "answer": None, "accepted": False}
        if not facts:
            out["answer"] = self.kb.message("uncertain", lang)
            return out
        if self.llama_ready:
            text, stats = self.advisor.answer(question, facts, lang)
            ok, reasons = check_output(text, facts, lang)
            out.update(answer=text if ok else None, accepted=ok, rejected_reasons=reasons, raw_text=text,
                       stats=stats)
        return out

    def _diagnosis_line(self, result, topic, lang):
        """One-line structured summary given to Llama (in English; the FACTS are in the answer language)."""
        d = result["disease"]
        if d["answered"] and topic == d["topic"]:
            line = (f"Diagnosis: {self.kb.topic_name(topic, 'en')} on a tomato leaf "
                    f"(model confidence {d['top'][0]['probability']:.0%}).")
            # Severity from the validated lesion model only (the colour rule used before is no longer used)
            sev = result.get("severity")
            if sev and sev.get("validated"):
                line += f" Estimated spread on the photographed leaf: {sev['level']}."
            if d["urgent"]:
                line += " This disease is urgent: it spreads very fast."
            if d["reliability"] == "low":
                line += " The photo result is not certain; the farmer should confirm with the local KVK."
        else:
            line = f"An insect pest was found on the tomato plant: {self.kb.topic_name(topic, 'en')}."
            for ps in result.get("pest_severity", []):
                if ps["topic"] == topic:
                    line += f" Insects of this kind counted in the photo: {ps['count']} ({ps['level']} for one photo)."
        return line


def _ms(t0):
    return round((time.perf_counter() - t0) * 1000, 1)
