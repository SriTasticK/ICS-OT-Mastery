#!/usr/bin/env bash
# Called only after synthetic validation. Preserve the existing app for rollback.
set -euo pipefail
model_name=${LAB_REVIEW_MODEL:-qwen3:4b-instruct-2507-q4_K_M}
[[ "$(docker network inspect --format '{{.Internal}}' private-lab-internal)" == true ]]
processor=$(docker exec private-lab-reviewer ollama ps)
printf '%s\n' "$processor"
[[ "$processor" =~ 100%[[:space:]]+GPU ]] || { echo 'Full GPU residency required.' >&2; exit 1; }
backup_container="private-research-lab-before-reviewer-$(date -u +%Y%m%dT%H%M%SZ)"
docker exec private-research-lab /app/.venv/bin/python -c 'import sqlite3,time; s=sqlite3.connect("/data/lab.sqlite3"); t=sqlite3.connect("/data/before-reviewer-"+str(time.time_ns())+".sqlite3"); s.backup(t); t.close(); s.close()'
docker stop private-research-lab >/dev/null
docker rename private-research-lab "$backup_container"
activated=false
rollback() {
  if [[ "$activated" != true ]]; then
    docker rm -f private-research-lab >/dev/null 2>&1 || true
    docker rename "$backup_container" private-research-lab
    docker start private-research-lab >/dev/null
    echo 'Activation failed; previous app restored.' >&2
  fi
}
trap rollback EXIT
docker run --detach --name private-research-lab --restart unless-stopped \
  --network private-lab-internal --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL --security-opt no-new-privileges:true --pids-limit 96 --memory 512m --cpus 2 \
  --mount type=volume,src=private-lab-data,dst=/data \
  --env LAB_DATA=/data --env LAB_HOSTS=localhost,127.0.0.1 \
  --env LAB_REVIEW_MODE=local-ai --env LAB_REVIEW_URL=http://ollama:11434 \
  --env "LAB_REVIEW_MODEL=$model_name" private-research-lab:reviewer-candidate >/dev/null
for attempt in {1..45}; do
  if docker exec private-research-lab /app/.venv/bin/python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8080/health",timeout=2)' >/dev/null 2>&1 && curl --fail --silent --max-time 2 http://127.0.0.1:8080/health >/dev/null; then
    docker tag private-research-lab:reviewer-candidate private-research-lab:local
    activated=true
    echo "GPU reviewer enabled. Previous container retained: $backup_container"
    exit 0
  fi
  sleep 1
done
exit 1
