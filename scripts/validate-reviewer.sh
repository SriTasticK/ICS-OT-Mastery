#!/usr/bin/env bash
# Evaluate synthetic fixtures in an ephemeral client with no learner data mounted.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
docker build --tag private-research-lab:reviewer-candidate .
docker run --rm -i --network private-lab-internal \
  --read-only --cap-drop ALL --security-opt no-new-privileges:true \
  --memory 256m --pids-limit 32 --env "REVIEW_SKIP_BENCHMARK=${REVIEW_SKIP_BENCHMARK:-1}" \
  --env "LAB_REVIEW_MODEL=${LAB_REVIEW_MODEL:-qwen3:4b-instruct-2507-q4_K_M}" \
  --entrypoint /app/.venv/bin/python private-research-lab:reviewer-candidate - \
  < scripts/check-reviewer.py
# Exercise submission, rendered feedback, and unlock against a disposable database.
docker run --rm --network private-lab-internal \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --cap-drop ALL --security-opt no-new-privileges:true --memory 256m --pids-limit 32 \
  --mount "type=bind,src=$PWD/scripts,dst=/checks,readonly" \
  --env PYTHONPATH=/app --env "LAB_REVIEW_MODEL=${LAB_REVIEW_MODEL:-qwen3:4b-instruct-2507-q4_K_M}" \
  --entrypoint /app/.venv/bin/python private-research-lab:reviewer-candidate /checks/check-reviewer-flow.py
