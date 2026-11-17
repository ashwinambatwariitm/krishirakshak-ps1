/*
 * onnx_session.hpp - thin RAII wrapper around an ONNX Runtime CPU session with one input and one output.
 *
 * One Ort::Env is shared by the whole process. Each model gets its own session with its own intra-op thread
 * count, so the disease classifier and the pest detector can run at the same time on separate cores
 * (2 + 2 threads = the four Cortex-A76 cores of the Raspberry Pi 5).
 */
#pragma once

#include <onnxruntime_cxx_api.h>

#include <memory>
#include <string>
#include <vector>

namespace kr {

inline Ort::Env& ortEnv() {
    static Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "krishirakshak");
    return env;
}

class OnnxSession {
public:
    OnnxSession(const std::string& modelPath, int intraOpThreads) {
        Ort::SessionOptions opt;
        opt.SetIntraOpNumThreads(intraOpThreads);
        opt.SetInterOpNumThreads(1);
        opt.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
        session_ = std::make_unique<Ort::Session>(ortEnv(), modelPath.c_str(), opt);
        Ort::AllocatorWithDefaultOptions alloc;
        inputName_ = session_->GetInputNameAllocated(0, alloc).get();
        outputName_ = session_->GetOutputNameAllocated(0, alloc).get();
    }

    // Runs the model on one NCHW float tensor; returns the first output tensor (owned by ONNX Runtime).
    Ort::Value run(std::vector<float>& input, const std::vector<int64_t>& shape) {
        auto mem = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
        Ort::Value tensor = Ort::Value::CreateTensor<float>(mem, input.data(), input.size(), shape.data(),
                                                            shape.size());
        const char* in[] = {inputName_.c_str()};
        const char* out[] = {outputName_.c_str()};
        auto outputs = session_->Run(Ort::RunOptions{nullptr}, in, &tensor, 1, out, 1);
        return std::move(outputs.front());
    }

private:
    std::unique_ptr<Ort::Session> session_;
    std::string inputName_, outputName_;
};

}  // namespace kr
