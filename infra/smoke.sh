#!/usr/bin/env bash
# Post-deploy check: health -> login -> check -> history -> audit chain.
#   SMOKE_EMAIL=... SMOKE_PASSWORD=... ./smoke.sh https://hakiki.example.com [--insecure]
set -euo pipefail

BASE="${1:?base url required}"
CURL=(curl -fsS --max-time 20)
[[ "${2:-}" == "--insecure" ]] && CURL+=(-k)
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

step() { printf '%s ... ' "$1"; }
ok() { echo ok; }

step "health"
"${CURL[@]}" "$BASE/health" | grep -q '"ok"'; ok

step "security headers"
headers="$("${CURL[@]}" -I "$BASE/")"
for header in strict-transport-security content-security-policy x-content-type-options; do
  grep -qi "^$header:" <<<"$headers" || { echo "missing $header" >&2; exit 1; }
done
ok

step "login"
"${CURL[@]}" -c "$JAR" -X POST "$BASE/v1/auth/login" -H 'content-type: application/json' \
  -d "{\"email\":\"${SMOKE_EMAIL:?}\",\"password\":\"${SMOKE_PASSWORD:?}\"}" >/dev/null
grep -q hakiki_session "$JAR"; ok

step "check a claim"
verdict="$("${CURL[@]}" -b "$JAR" -X POST "$BASE/v1/claims/check" -H 'content-type: application/json' \
  -d '{"claim_ref":"smoke-'"$(date +%s)"'","patient_id":"SMOKE-PATIENT","facility_id":"fac-12","service_code":"svc-CS-01","fund":"SHIF","date_of_service":"2026-10-14","amount_kes":45000,"member_status":"active"}' \
  | jq -r .verdict)"
[[ "$verdict" == "WILL_FAIL" ]] || { echo "unexpected verdict $verdict" >&2; exit 1; }
ok

step "history"
"${CURL[@]}" -b "$JAR" "$BASE/v1/claims?_start=0&_end=1" | jq -e 'length >= 1' >/dev/null; ok

step "audit chain"
"${CURL[@]}" -b "$JAR" "$BASE/v1/audit/verify" | jq -e '.valid == true' >/dev/null; ok

echo "smoke test passed"
