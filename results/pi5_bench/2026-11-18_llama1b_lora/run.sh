#!/usr/bin/env bash
# Base Llama 3.2 1B vs LoRA-tuned 1B on the five test photos (English), same app build and options
cd ~/krishirakshak
for m in base:models/llama3_2_1b_instruct_8da4w.pte lora:models/llama3_2_1b_krishirakshak_lora_8da4w.pte; do
  name=${m%%:*}; pte=${m#*:}
  for p in photos/*.jpg; do
    n=$(basename "$p" .jpg)
    /usr/bin/time -f "$name $n %e s wall, peak RSS %M KB" ./krishirakshak --root . --llama-pte "$pte" --lang en "$p" > "bench_lora/${name}_${n}.json" 2>> bench_lora/stderr.log
  done
done
vcgencmd measure_temp; vcgencmd get_throttled
echo DONE
