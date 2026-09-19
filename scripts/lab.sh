#!/usr/bin/env bash
# Docker CLI equivalent of compose.yaml. Run from any directory.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
lab_container=private-research-lab
lab_network=private-lab-internal
lab_volume=private-lab-data
if ! docker info >/dev/null 2>&1; then
  echo 'Docker is unavailable to this user. On this machine, run: sudo bash scripts/lab.sh start' >&2
  exit 1
fi
case "${1:-start}" in
  start)
    if docker container inspect "$lab_container" >/dev/null 2>&1; then
      echo 'A lab container already exists. Use status, stop, or rebuild explicitly.' >&2
      exit 1
    fi
    docker build --tag private-research-lab:local .
    if docker network inspect "$lab_network" >/dev/null 2>&1; then
      if [[ "$(docker network inspect --format '{{.Internal}}' "$lab_network")" != true ]]; then
        echo 'Refusing an existing non-internal network.' >&2; exit 1
      fi
    else
      docker network create --internal "$lab_network" >/dev/null
    fi
    docker volume create "$lab_volume" >/dev/null
    docker run --detach --name "$lab_container" --restart unless-stopped \
      --network "$lab_network" \
      --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
      --cap-drop ALL --security-opt no-new-privileges:true \
      --pids-limit 96 --memory 512m --cpus 2 \
      --mount "type=volume,src=$lab_volume,dst=/data" \
      --env LAB_DATA=/data --env LAB_HOSTS=localhost,127.0.0.1 \
      --env LAB_REVIEW_MODE=structured private-research-lab:local >/dev/null
    lab_ready=false
    for attempt in {1..30}; do
      if [[ "$(docker inspect --format '{{.State.Health.Status}}' "$lab_container")" == healthy ]]; then
        lab_ready=true
        break
      fi
      sleep 1
    done
    if [[ "$lab_ready" != true ]]; then
      echo 'Container started but is not healthy yet. Inspect docker logs private-research-lab.' >&2
      exit 1
    fi
    bash scripts/gateway.sh
    echo 'Lab started: http://127.0.0.1:8080'
    echo 'Retrieve the one-time setup token: sudo docker exec private-research-lab cat /data/setup-token'
    ;;
  status)
    docker inspect --format 'Status={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{end}} Ports={{json .HostConfig.PortBindings}}' "$lab_container"
    docker network inspect --format 'Internal network={{.Internal}}' "$lab_network"
    docker inspect --format 'Gateway active ports={{json .NetworkSettings.Ports}}' private-lab-gateway
    ;;
  stop) docker stop private-lab-gateway "$lab_container" ;;
  resume) docker start "$lab_container" private-lab-gateway ;;
  rebuild)
    # Keep the persistent data volume. Explicit rebuild replaces only this container.
    docker build --tag private-research-lab:local .
    if docker container inspect "$lab_container" >/dev/null 2>&1; then
      docker stop "$lab_container" >/dev/null
      docker rm "$lab_container" >/dev/null
    fi
    exec bash scripts/lab.sh start
    ;;
  backup)
    lab_backup="lab-backup-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
    docker exec "$lab_container" /app/.venv/bin/python -c 'import sqlite3; source=sqlite3.connect("/data/lab.sqlite3"); target=sqlite3.connect("/tmp/lab-backup.sqlite3"); source.backup(target); target.close(); source.close()'
    docker cp "$lab_container:/tmp/lab-backup.sqlite3" "$lab_backup" >/dev/null
    chmod 600 "$lab_backup"
    echo "Backup written to $lab_backup (contains private research and account data)."
    ;;
  *) echo 'Usage: bash scripts/lab.sh {start|status|stop|resume|rebuild|backup}' >&2; exit 2 ;;
esac
