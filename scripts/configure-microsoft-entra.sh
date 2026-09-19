#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE_OVERRIDE:-${REPO_ROOT}/.env}"
REALM="${KEYCLOAK_REALM_OVERRIDE:-AIPlatform}"
CONTAINER="${KEYCLOAK_CONTAINER_OVERRIDE:-aiplatform-keycloak-1}"
PAYLOAD_PATH="/opt/keycloak/data/tmp/algomotive-microsoft-idp.json"

get_env_value() {
  local key="$1"
  test -f "${ENV_FILE}" || return 1
  grep -E "^${key}=" "${ENV_FILE}" | tail -n 1 | cut -d= -f2-
}

enabled="$(get_env_value MICROSOFT_ENTRA_ENABLED 2>/dev/null || true)"

if [ "${enabled}" != "true" ]; then
  printf '%s\n' "Microsoft Entra federation is disabled."
  printf '%s\n' "Set MICROSOFT_ENTRA_ENABLED=true only after the Entra app registration is ready."
  printf '%s\n' "MICROSOFT_ENTRA_CONFIGURATION_SKIPPED"
  exit 0
fi

tenant_id="$(get_env_value MICROSOFT_ENTRA_TENANT_ID 2>/dev/null || true)"
client_id="$(get_env_value MICROSOFT_ENTRA_CLIENT_ID 2>/dev/null || true)"
client_secret="$(get_env_value MICROSOFT_ENTRA_CLIENT_SECRET 2>/dev/null || true)"

for entry in \
  "MICROSOFT_ENTRA_TENANT_ID:${tenant_id}" \
  "MICROSOFT_ENTRA_CLIENT_ID:${client_id}" \
  "MICROSOFT_ENTRA_CLIENT_SECRET:${client_secret}"
do
  key="${entry%%:*}"
  value="${entry#*:}"
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

printf '%s' "${tenant_id}" |
  grep -Eq '^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$' ||
  {
    printf '%s\n' "ERROR_INVALID_ENTRA_TENANT_ID" >&2
    exit 1
  }

tmp_json="$(mktemp)"

cleanup() {
  rm -f "${tmp_json}"
  docker exec -u 0 "${CONTAINER}" rm -f "${PAYLOAD_PATH}" >/dev/null 2>&1 || true
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

tenant = os.environ["MICROSOFT_ENTRA_TENANT_ID"]

payload = {
    "alias": "microsoft",
    "displayName": "Sign in with Microsoft",
    "providerId": "oidc",
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
        "authorizationUrl": f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        "tokenUrl": f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        "userInfoUrl": "https://graph.microsoft.com/oidc/userinfo",
        "jwksUrl": "https://login.microsoftonline.com/common/discovery/v2.0/keys",
        "issuer": f"https://login.microsoftonline.com/{tenant}/v2.0",
        "clientAuthMethod": "client_secret_post",
        "defaultScope": "openid profile email",
        "prompt": "select_account",
        "syncMode": "IMPORT",
        "useJwksUrl": "true",
        "validateSignature": "true",
    },
}

with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
    handle.write("\n")
PY

python3 - "${tmp_json}" "${tenant_id}" <<'PY'
import json
import sys

path, tenant = sys.argv[1], sys.argv[2]

with open(path, encoding="utf-8") as handle:
    payload = json.load(handle)

config = payload.get("config", {})

assert payload.get("alias") == "microsoft"
assert payload.get("providerId") == "oidc"
assert config.get("authorizationUrl") == f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
assert config.get("tokenUrl") == f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
assert config.get("issuer") == f"https://login.microsoftonline.com/{tenant}/v2.0"
assert config.get("defaultScope") == "openid profile email"

print("GENERATED_MICROSOFT_PAYLOAD_VALID")
PY

docker exec -u 0 "${CONTAINER}" mkdir -p "$(dirname "${PAYLOAD_PATH}")"
docker exec -u 0 "${CONTAINER}" rm -f "${PAYLOAD_PATH}"
docker cp "${tmp_json}" "${CONTAINER}:${PAYLOAD_PATH}" >/dev/null
docker exec -u 0 "${CONTAINER}" sh -lc \
  "chown keycloak:root '${PAYLOAD_PATH}' && chmod 600 '${PAYLOAD_PATH}'"
docker exec "${CONTAINER}" test -r "${PAYLOAD_PATH}"

printf '%s\n%s\n%s\n' "${client_id}" "${client_secret}" "${tenant_id}" |
  docker exec -i "${CONTAINER}" sh -lc '
    set -eu

    IFS= read -r new_client
    IFS= read -r new_secret
    IFS= read -r new_tenant

    test -n "$new_client"
    test -n "$new_secret"
    test -n "$new_tenant"

    admin_user="${KC_BOOTSTRAP_ADMIN_USERNAME:-${KEYCLOAK_ADMIN:-}}"
    admin_pass="${KC_BOOTSTRAP_ADMIN_PASSWORD:-${KEYCLOAK_ADMIN_PASSWORD:-}}"

    test -n "$admin_user"
    test -n "$admin_pass"

    /opt/keycloak/bin/kcadm.sh config credentials \
      --server http://127.0.0.1:8080 \
      --realm master \
      --user "$admin_user" \
      --password "$admin_pass" >/dev/null

    realm="'"${REALM}"'"
    payload="'"${PAYLOAD_PATH}"'"

    if /opt/keycloak/bin/kcadm.sh get \
      "identity-provider/instances/microsoft" \
      -r "$realm" >/dev/null 2>&1
    then
      /opt/keycloak/bin/kcadm.sh update \
        "identity-provider/instances/microsoft" \
        -r "$realm" \
        -f "$payload" >/dev/null
      printf "%s\n" "MICROSOFT_ENTRA_IDP_UPDATED"
    else
      /opt/keycloak/bin/kcadm.sh create \
        "identity-provider/instances" \
        -r "$realm" \
        -f "$payload" >/dev/null
      printf "%s\n" "MICROSOFT_ENTRA_IDP_CREATED"
    fi

    /opt/keycloak/bin/kcadm.sh update \
      "identity-provider/instances/microsoft" \
      -r "$realm" \
      -s "providerId=oidc" \
      -s "enabled=true" \
      -s "trustEmail=true" \
      -s "storeToken=false" \
      -s "config.clientId=${new_client}" \
      -s "config.clientSecret=${new_secret}" \
      -s "config.authorizationUrl=https://login.microsoftonline.com/${new_tenant}/oauth2/v2.0/authorize" \
      -s "config.tokenUrl=https://login.microsoftonline.com/${new_tenant}/oauth2/v2.0/token" \
      -s "config.userInfoUrl=https://graph.microsoft.com/oidc/userinfo" \
      -s "config.jwksUrl=https://login.microsoftonline.com/common/discovery/v2.0/keys" \
      -s "config.issuer=https://login.microsoftonline.com/${new_tenant}/v2.0" \
      -s "config.clientAuthMethod=client_secret_post" \
      -s "config.defaultScope=openid profile email" \
      -s "config.prompt=select_account" \
      -s "config.syncMode=IMPORT" \
      -s "config.useJwksUrl=true" \
      -s "config.validateSignature=true" >/dev/null

    printf "%s\n" "MICROSOFT_CLIENT_AND_ENDPOINTS_SYNCHRONIZED"

    /opt/keycloak/bin/kcadm.sh get \
      "identity-provider/instances/microsoft" \
      -r "$realm" \
      --fields alias,displayName,providerId,enabled,trustEmail,storeToken
  '

printf '%s\n' "MICROSOFT_ENTRA_CONFIGURATION_COMPLETE"
