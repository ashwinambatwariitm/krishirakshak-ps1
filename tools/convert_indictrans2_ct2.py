"""Convert the HF IndicTrans2 en-indic 200M checkpoint to a CTranslate2 model.

CTranslate2's Transformers converter rejects IndicTransConfig, but the model is a
plain fairseq pre-norm Transformer whose HF module names match fairseq's. The
TransformerSpec is therefore built here and filled with CT2's own fairseq weight
mappers. Checked: per-token log-probabilities of the converted FP32 model match
the Hugging Face model within 6e-6 (forced decoding of the same outputs).
The official fairseq/CT2 archive (ai4bharat/BPCC) is gated; this route needs only
the public Hugging Face checkpoint ai4bharat/indictrans2-en-indic-dist-200M.

Usage: python tools/convert_indictrans2_ct2.py MODEL_DIR OUT_DIR [--quantization int8]
(MODEL_DIR = local snapshot of the Hugging Face checkpoint; output ~210 MB for int8)
"""
import argparse
import json
import os
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--quantization", default=None,
                    help="int8, int8_float32, float16 ... (default: keep float32)")
    args = ap.parse_args()

    os.environ.setdefault("HF_MODULES_CACHE", "/tmp/indictrans2_modules")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["USE_TF"] = "0"
    os.environ["USE_FLAX"] = "0"

    import torch
    from transformers import AutoModelForSeq2SeqLM
    from ctranslate2.converters import fairseq as fq
    from ctranslate2.converters.converter import Converter
    from ctranslate2.specs import common_spec, transformer_spec

    model_dir = Path(args.model_dir)
    cfg = json.loads((model_dir / "config.json").read_text())
    # Guard the assumptions this mapping relies on.
    assert cfg["encoder_normalize_before"] and cfg["decoder_normalize_before"]
    assert cfg["activation_function"] == "gelu" and cfg["layernorm_embedding"]
    assert cfg["scale_embedding"] and cfg["share_decoder_input_output_embed"]
    assert cfg["encoder_attention_heads"] == cfg["decoder_attention_heads"]

    def vocab(name):
        # dict.*.json maps token -> id; CT2 wants the list in id order, <pad> as <blank>.
        d = json.loads((model_dir / name).read_text())
        tokens = [None] * len(d)
        for tok, idx in d.items():
            tokens[idx] = tok
        assert None not in tokens, name
        return ["<blank>" if t == "<pad>" else t for t in tokens]

    class IndicTransConverter(Converter):
        def _load(self):
            spec = transformer_spec.TransformerSpec.from_config(
                (cfg["encoder_layers"], cfg["decoder_layers"]),
                cfg["encoder_attention_heads"],
                pre_norm=True,
                activation=common_spec.Activation.GELU,  # exact erf GELU, as HF "gelu"
                layernorm_embedding=True,
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                str(model_dir), trust_remote_code=True, local_files_only=True,
                torch_dtype=torch.float32).eval()
            enc, dec = model.model.encoder, model.model.decoder
            # Adapter: give the HF decoder the fairseq attribute names CT2 expects.
            dec.output_projection = model.lm_head
            dec.project_in_dim = None
            dec.project_out_dim = None
            with torch.no_grad():
                fq.set_transformer_encoder(spec.encoder, enc)
                fq.set_transformer_decoder(spec.decoder, dec)
            spec.register_source_vocabulary(vocab("dict.SRC.json"))
            spec.register_target_vocabulary(vocab("dict.TGT.json"))
            # Same special-token convention as CT2's fairseq converter and the HF
            # generation_config: decoder starts with </s>, source gets </s> appended.
            spec.config.decoder_start_token = spec.config.eos_token
            spec.config.add_source_eos = True
            return spec

    out = IndicTransConverter().convert(args.out_dir, quantization=args.quantization, force=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
