#!/usr/bin/env bash
# Add the localhost ingress without granting the app an external network.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
[[ "$(docker network inspect --format '{{.Internal}}' private-lab-internal)" == true ]]
docker build --file Dockerfile.gateway --tag private-lab-gateway:local .
if docker network inspect private-lab-ingress >/dev/null 2>&1; then
  [[ "$(docker network inspect --format '{{index .Options "com.docker.network.bridge.enable_ip_masquerade"}}' private-lab-ingress)" == false ]]
else
  docker network create --opt com.docker.network.bridge.enable_ip_masquerade=false private-lab-ingress >/dev/null
fi
if docker container inspect private-lab-gateway >/dev/null 2>&1; then
  docker stop private-lab-gateway >/dev/null
  docker rm private-lab-gateway >/dev/null
fi
docker run --detach --name private-lab-gateway --restart unless-stopped \
  --network private-lab-ingress --network private-lab-internal \
  --publish 127.0.0.1:8080:8080 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m --cap-drop ALL \
  --security-opt no-new-privileges:true --pids-limit 64 --memory 128m \
  private-lab-gateway:local >/dev/null
for attempt in {1..30}; do
  if curl --fail --silent --max-time 2 http://127.0.0.1:8080/health >/dev/null; then
    echo 'Gateway verified: http://127.0.0.1:8080'
    exit 0
  fi
  sleep 1
done
echo 'Gateway not reachable. Inspect docker logs private-lab-gateway.' >&2
exit 1
