/*
 * prefill_check.cpp - is prefilling a prompt in two parts the same as prefilling it at once?
 *
 * The prompt prefix cache (cpp/src/llama_advisor.cpp) prefills the fixed start of the prompt once and later the
 * rest of the prompt at a non-zero cache position. This tool measures, for one prompt, how far the logits after
 * the last prompt token move when the prompt is split at token k (tokens [0,k) at position 0, then [k,n) at
 * position k) compared with one prefill of all n tokens:
 *
 *   k  rest_tokens  max_abs_diff  top1_full  top1_split  margin_full  same_top1
 *
 * margin_full = difference between the best and second-best logit of the single prefill: when max_abs_diff is
 * small but larger than the margin, greedy decoding can pick another token (rounding, not a bug). A large
 * max_abs_diff points to a real error in the split computation.
 *
 * Usage:  prefill_check model.pte tokenizer.model prompt.txt [k1 k2 ...]
 *   prompt.txt: the full prompt text (write it with KR_DUMP_PROMPT=prompt.txt krishirakshak ...)
 *   k values:   split points in tokens; default: a range of points so that the rest is shorter and longer than
 *               192 tokens (the attention kernel changes its query block size at 192 tokens)
 * Built only with ExecuTorch (target prefill_check).
 */
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"   // runner building blocks are marked experimental

#include <executorch/extension/llm/runner/constants.h>
#include <executorch/extension/llm/runner/io_manager/io_manager.h>
#include <executorch/extension/llm/runner/llm_runner_helper.h>
#include <executorch/extension/llm/runner/stats.h>
#include <executorch/extension/llm/runner/text_decoder_runner.h>
#include <executorch/extension/llm/sampler/sampler.h>
#include <executorch/extension/module/module.h>
#include <executorch/extension/tensor/tensor.h>
#include <pytorch/tokenizers/tokenizer.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace llm = ::executorch::extension::llm;
using ::executorch::extension::from_blob;
using ::executorch::extension::Module;
using ::executorch::runtime::Error;

namespace {

// Runs tokens[begin, end) at cache position `begin`; returns the logits of the last token (copied).
std::vector<float> runChunk(llm::TextDecoderRunner& runner, std::vector<uint64_t>& tokens, size_t begin, size_t end) {
    std::vector<uint64_t> chunk(tokens.begin() + begin, tokens.begin() + end);
    auto t = from_blob(chunk.data(), {1, static_cast<int>(chunk.size())}, ::executorch::aten::ScalarType::Long);
    auto res = runner.step(t, static_cast<int64_t>(begin));
    if (!res.ok()) {
        std::fprintf(stderr, "step failed at begin=%zu\n", begin);
        std::exit(1);
    }
    const auto& logits = res.get();
    if (logits.scalar_type() != ::executorch::aten::ScalarType::Float) {
        std::fprintf(stderr, "logits are not float32\n");
        std::exit(1);
    }
    const size_t vocab = logits.size(logits.dim() - 1);
    const float* p = logits.const_data_ptr<float>() + (logits.numel() - vocab);   // last position
    return std::vector<float>(p, p + vocab);
}

struct Top2 {
    size_t best, second;
};

Top2 top2(const std::vector<float>& v) {
    size_t a = 0, b = 1;
    if (v[b] > v[a]) std::swap(a, b);
    for (size_t i = 2; i < v.size(); ++i) {
        if (v[i] > v[a]) { b = a; a = i; }
        else if (v[i] > v[b]) b = i;
    }
    return {a, b};
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 4) {
        std::fprintf(stderr, "usage: prefill_check model.pte tokenizer.model prompt.txt [k ...]\n");
        return 2;
    }
    std::ifstream in(argv[3]);
    std::stringstream ss;
    ss << in.rdbuf();
    const std::string prompt = ss.str();

    auto tokenizer = llm::load_tokenizer(argv[2]);
    if (!tokenizer) return 1;
    Module module(argv[1], Module::LoadMode::MmapUseMlockIgnoreErrors);
    auto meta = llm::get_llm_metadata(tokenizer.get(), &module);
    if (meta.error() != Error::Ok) return 1;
    llm::IOManager io(module);
    llm::Stats stats;
    llm::TextDecoderRunner runner(&module, &io, "forward",
                                  std::make_unique<llm::Sampler>(static_cast<int32_t>(meta.get().at(llm::kVocabSize)),
                                                                 0.0f),
                                  &stats);
    if (runner.load() != Error::Ok || io.load() != Error::Ok) return 1;

    auto enc = tokenizer->encode(prompt, 0, 0);
    if (!enc.ok()) return 1;
    std::vector<uint64_t> tokens = enc.get();
    const size_t n = tokens.size();

    std::vector<size_t> splits;
    for (int i = 4; i < argc; ++i) splits.push_back(std::strtoul(argv[i], nullptr, 10));
    if (splits.empty()) {
        for (size_t rest : {40, 100, 150, 172, 191, 192, 200, 250})
            if (rest + 1 < n) splits.push_back(n - rest);
    }

    const auto full = runChunk(runner, tokens, 0, n);
    const Top2 tf = top2(full);
    std::printf("prompt tokens %zu, single prefill top1 %zu (margin %.4f)\n", n, tf.best, full[tf.best] - full[tf.second]);
    std::printf("%6s %11s %12s %9s %10s %11s %9s\n", "k", "rest_tokens", "max_abs_diff", "top1_full", "top1_split",
                "margin_full", "same_top1");
    for (size_t k : splits) {
        if (k == 0 || k >= n) continue;
        runChunk(runner, tokens, 0, k);                 // prefix at position 0
        const auto split = runChunk(runner, tokens, k, n);   // rest at position k
        float maxDiff = 0.0f;
        for (size_t i = 0; i < full.size(); ++i) maxDiff = std::max(maxDiff, std::fabs(full[i] - split[i]));
        const Top2 ts = top2(split);
        std::printf("%6zu %11zu %12.6f %9zu %10zu %11.4f %9s\n", k, n - k, maxDiff, tf.best, ts.best,
                    full[tf.best] - full[tf.second], tf.best == ts.best ? "yes" : "NO");
    }
    return 0;
}
