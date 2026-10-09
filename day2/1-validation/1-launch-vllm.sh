#!/bin/sh

OMP_NUM_THREADS=4 uv run vllm serve /root/autodl-tmp/qwen35-4b-finetuned-ffmpeglog \
	--host 0.0.0.0 \
	--port 8000 \
	--max-model-len 8192 \
	--trust-remote-code \
	--language-model-only \
	--served-model-name ffmodel
