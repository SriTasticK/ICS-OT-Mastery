#!/usr/bin/env bash
set -euo pipefail
[[ "$(docker inspect --format '{{.HostConfig.Privileged}}' private-research-lab)" == false ]]
[[ "$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' private-research-lab)" == true ]]
[[ "$(docker inspect --format '{{.Config.User}}' private-research-lab)" == '10001:10001' ]]
[[ "$(docker network inspect --format '{{.Internal}}' private-lab-internal)" == true ]]
[[ "$(docker inspect --format '{{len .NetworkSettings.Networks}}' private-research-lab)" == 1 ]]
# Check the ACTIVE port mapping; a configured mapping can be silently inactive.
[[ "$(docker inspect --format '{{(index (index .NetworkSettings.Ports "8080/tcp") 0).HostIp}}' private-lab-gateway)" == '127.0.0.1' ]]
[[ "$(docker inspect --format '{{len .HostConfig.PortBindings}}' private-lab-gateway)" == 1 ]]
[[ "$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' private-lab-gateway)" == true ]]
curl --fail --silent --max-time 5 http://127.0.0.1:8080/health
printf '\nVerified: active localhost gateway, internal-only app network, non-root app, read-only filesystems, healthy HTTP endpoint.\n'
