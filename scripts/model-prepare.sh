#!/usr/bin/env bash
# Explicit, one-time connected download. No learner data is mounted here.
# Runtime reviewers use only the internal network and have no published ports.
set -euo pipefail
model_image=ollama/ollama@sha256:2c9595c555fd70a28363489ac03bd5bf9e7c5bdf2890373c3a830ffd7252ce6d
model_name=qwen3:4b-instruct-2507-q4_K_M
if ! command -v nvidia-smi >/dev/null || ! nvidia-smi --query-gpu=name --format=csv,noheader; then
  echo 'No functioning NVIDIA GPU found; keep structured review.' >&2; exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo 'Docker access is required. Try sudo bash scripts/model-prepare.sh.' >&2; exit 1
fi
if ! command -v nvidia-container-cli >/dev/null; then
  echo 'NVIDIA Container Toolkit is missing. Keep structured review until Docker GPU access is configured; see LAB.md.' >&2
  exit 1
fi
docker pull "$model_image"
# Prove Docker GPU access before downloading model weights.
docker run --rm --device nvidia.com/gpu=all --network none --entrypoint nvidia-smi "$model_image" --query-gpu=name,memory.free --format=csv,noheader
docker volume create private-lab-models >/dev/null
# Dedicated transient container has internet only to download weights. No ports.
docker run --rm --name private-lab-model-download --device nvidia.com/gpu=all \
  --security-opt no-new-privileges:true \
  --mount type=volume,src=private-lab-models,dst=/root/.ollama \
  --env OLLAMA_NO_CLOUD=1 --entrypoint /bin/sh "$model_image" -c \
  'ollama serve >/tmp/ollama-setup.log 2>&1 & server=$!; trap "kill $server 2>/dev/null || true" EXIT; i=0; until ollama list >/dev/null 2>&1; do i=$((i+1)); [ "$i" -lt 30 ] || exit 1; sleep 1; done; ollama pull qwen3:4b-instruct-2507-q4_K_M'
echo "Downloaded $model_name. Runtime will have no internet route."
echo 'Next: sudo bash scripts/gpu-start.sh'
