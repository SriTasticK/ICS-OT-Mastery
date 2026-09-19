#!/usr/bin/env bash
# Adds a GPU reviewer and explicitly replaces the web container, preserving data.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ "$(docker network inspect --format '{{.Internal}}' private-lab-internal)" != true ]]; then
  echo 'Start the base lab first. Its network must be internal.' >&2; exit 1
fi
if docker container inspect private-lab-reviewer >/dev/null 2>&1; then
  docker start private-lab-reviewer >/dev/null
else
docker run --detach --name private-lab-reviewer --restart unless-stopped \
  --device nvidia.com/gpu=all --network private-lab-internal --network-alias ollama \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 256 --memory 6g \
  --mount type=volume,src=private-lab-models,dst=/root/.ollama \
  --env OLLAMA_NO_CLOUD=1 --env OLLAMA_HOST=0.0.0.0:11434 \
  --env OLLAMA_CONTEXT_LENGTH=4096 --env OLLAMA_NUM_PARALLEL=1 \
  --env OLLAMA_FLASH_ATTENTION=1 --env OLLAMA_KV_CACHE_TYPE=q8_0 \
  --env OLLAMA_MAX_LOADED_MODELS=1 ollama/ollama@sha256:2c9595c555fd70a28363489ac03bd5bf9e7c5bdf2890373c3a830ffd7252ce6d >/dev/null
fi
# Reusing a reviewer must preserve the same private deployment boundary.
[[ "$(docker inspect --format '{{len .NetworkSettings.Networks}}' private-lab-reviewer)" == 1 ]]
[[ "$(docker inspect --format '{{with index .NetworkSettings.Networks "private-lab-internal"}}yes{{end}}' private-lab-reviewer)" == yes ]]
[[ "$(docker inspect --format '{{len .HostConfig.PortBindings}}' private-lab-reviewer)" == 0 ]]
# Wait for readiness; validate the candidate code rather than the old live app.
for attempt in {1..30}; do
  if docker exec private-lab-reviewer ollama list >/dev/null 2>&1; then break; fi
  sleep 1
done
REVIEW_SKIP_BENCHMARK=0 bash scripts/validate-reviewer.sh
bash scripts/activate-reviewer.sh
