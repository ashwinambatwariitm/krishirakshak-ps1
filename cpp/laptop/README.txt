KrishiRakshak - laptop demo (Linux x86_64, or Windows 10/11 with WSL Ubuntu 22.04 or 24.04)
=========================================================================================

The same C++ pipeline and farmer app as on the Raspberry Pi 5: disease and pest detection, severity, the Llama 3.2
1B advisor (LoRA-tuned) and IndicTrans2 translation into 9 Indian languages. Runs offline once set up.
Needs about 3 GB of free memory with Llama (1 GB with --no-llama) and 2 GB of disk.

1. Unpack:            tar -xzf krishirakshak-laptop-x86_64.tar.gz && cd krishirakshak-laptop
2. Models (once):     sudo apt install gh && gh auth login && ./kr_laptop.sh setup
3. Start:             ./kr_laptop.sh
4. Open:              http://localhost:8080   (phone view: F12, then Ctrl+Shift+M in Chrome or Edge)

Without the GitHub CLI, download these files from the repository's releases page into models/ and unpack the
.tar.gz there (tar -xzf ... -C models):
  models-v2  tomato_disease_v5_effb0_6class.onnx, pest_yolov8n_ip102_negatives.onnx
  models-v3  severity_lraspp_mnv3.onnx, indictrans2_model.SRC, indictrans2_en_indic_200M_ct2_int8.tar.gz
  llm-v2     llama3_2_1b_krishirakshak_lora_8da4w.pte
  llm-v1     llama3_2_tokenizer.model

Licences: Llama 3.2 is licensed under the Llama 3.2 Community License (licences/, downloaded with the model);
"Built with Llama". IndicTrans2: MIT (licences/indictrans2_LICENSE).
