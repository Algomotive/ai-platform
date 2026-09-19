#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${REPO_ROOT}/.env}"

# shellcheck source=scripts/common.sh
source "${SCRIPT_DIR}/common.sh"

enabled="$(get_env MICROSOFT_ENTRA_ENABLED 2>/dev/null || true)"

if [ "${enabled}" != "true" ]; then
  printf '%s\n' "Microsoft Entra federation is disabled."
  printf '%s\n' "Set MICROSOFT_ENTRA_ENABLED=true only after the Entra app registration is ready."
  printf '%s\n' "MICROSOFT_ENTRA_CONFIGURATION_SKIPPED"
  exit 0
fi

tenant_id="$(get_env MICROSOFT_ENTRA_TENANT_ID 2>/dev/null || true)"
client_id="$(get_env MICROSOFT_ENTRA_CLIENT_ID 2>/dev/null || true)"
client_secret="$(get_env MICROSOFT_ENTRA_CLIENT_SECRET 2>/dev/null || true)"
realm="$(get_env KEYCLOAK_REALM 2>/dev/null || true)"

for item in \
  "MICROSOFT_ENTRA_TENANT_ID:${tenant_id}" \
  "MICROSOFT_ENTRA_CLIENT_ID:${client_id}" \
  "MICROSOFT_ENTRA_CLIENT_SECRET:${client_secret}" \
  "KEYCLOAK_REALM:${realm}"
do
  key="${item%%:*}"
  value="${item#*:}"
  if [ -z "${value}" ]; then
    printf 'ERROR_REQUIRED_VALUE_MISSING=%s\n' "${key}" >&2
    exit 1
  fi
done

case "${tenant_id}" in
  common|organizations|consumers)
    printf '%s\n' "ERROR_SINGLE_TENANT_ID_REQUIRED" >&2
    exit 1
    ;;
esac

case "${tenant_id}" in
  *[!0-9A-Fa-f-]*|"")
    printf '%s\n' "ERROR_INVALID_ENTRA_TENANT_ID" >&2
    exit 1
    ;;
esac

tmp_json="$(mktemp)"
cleanup() {
  rm -f "${tmp_json}"
  docker exec aiplatform-keycloak-1 rm -f /tmp/algomotive-microsoft-idp.json >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

chmod 600 "${tmp_json}"

MICROSOFT_ENTRA_TENANT_ID="${tenant_id}" \
MICROSOFT_ENTRA_CLIENT_ID="${client_id}" \
MICROSOFT_ENTRA_CLIENT_SECRET="${client_secret}" \
python3 - "${tmp_json}" <<'PY'
import json
import os
import sys

payload = {
    "alias": "microsoft",
    "displayName": "Sign in with Microsoft",
    "providerId": "microsoft",
    "enabled": True,
    "updateProfileFirstLoginMode": "on",
    "trustEmail": True,
    "storeToken": False,
    "addReadTokenRoleOnCreate": False,
    "authenticateByDefault": False,
    "linkOnly": False,
    "firstBrokerLoginFlowAlias": "first broker login",
    "config": {
        "clientId": os.environ["MICROSOFT_ENTRA_CLIENT_ID"],
        "clientSecret": os.environ["MICROSOFT_ENTRA_CLIENT_SECRET"],
        "tenant": os.environ["MICROSOFT_ENTRA_TENANT_ID"],
        "defaultScope": "openid profile email",
        "syncMode": "IMPORT",
        "useJwksUrl": "true",
    },
}

with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")
PY

docker cp "${tmp_json}" aiplatform-keycloak-1:/tmp/algomotive-microsoft-idp.json >/dev/null

docker exec aiplatform-keycloak-1 sh -lc '
  set -eu

  admin_user="${KC_BOOTSTRAP_ADMIN_USERNAME:-${KEYCLOAK_ADMIN:-}}"
  admin_pass="${KC_BOOTSTRAP_ADMIN_PASSWORD:-${KEYCLOAK_ADMIN_PASSWORD:-}}"

  test -n "$admin_user"
  test -n "$admin_pass"

  /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://127.0.0.1:8080 \
    --realm master \
    --user "$admin_user" \
    --password "$admin_pass" >/dev/null

  realm="'"${realm}"'"

  if /opt/keycloak/bin/kcadm.sh get \
    "identity-provider/instances/microsoft" \
    -r "$realm" >/dev/null 2>&1
  then
    /opt/keycloak/bin/kcadm.sh update \
      "identity-provider/instances/microsoft" \
      -r "$realm" \
      -f /tmp/algomotive-microsoft-idp.json >/dev/null
    printf "%s\n" "MICROSOFT_ENTRA_IDP_UPDATED"
  else
    /opt/keycloak/bin/kcadm.sh create \
      "identity-provider/instances" \
      -r "$realm" \
      -f /tmp/algomotive-microsoft-idp.json >/dev/null
    printf "%s\n" "MICROSOFT_ENTRA_IDP_CREATED"
  fi

  /opt/keycloak/bin/kcadm.sh get \
    "identity-provider/instances/microsoft" \
    -r "$realm" \
    --fields alias,displayName,providerId,enabled,trustEmail,storeToken
'

printf '%s\n' "MICROSOFT_ENTRA_CONFIGURATION_COMPLETE"
