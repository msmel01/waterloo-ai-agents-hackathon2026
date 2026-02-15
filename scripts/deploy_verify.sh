#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://valentinehotline.com}"
API_URL="${BASE_URL}/api/v1"

echo "Verifying deployment at ${BASE_URL}"

check_status() {
  local label="$1"
  local url="$2"
  local expected="$3"
  local extra_header="${4:-}"

  local status
  if [[ -n "${extra_header}" ]]; then
    status=$(curl -s -o /dev/null -w "%{http_code}" -H "${extra_header}" "${url}")
  else
    status=$(curl -s -o /dev/null -w "%{http_code}" "${url}")
  fi

  if [[ "${status}" == "${expected}" ]]; then
    echo "  [OK] ${label} (${status})"
  else
    echo "  [FAIL] ${label} expected=${expected} got=${status}"
  fi
}

check_status "Public health" "${BASE_URL}/health" "200"
check_status "Public profile" "${API_URL}/public/melika" "200"
check_status "Dashboard auth without key" "${API_URL}/dashboard/stats" "401"

if [[ -n "${DASHBOARD_API_KEY:-}" ]]; then
  check_status "Dashboard auth with key" "${API_URL}/dashboard/stats" "200" "X-Dashboard-Key: ${DASHBOARD_API_KEY}"
else
  echo "  [SKIP] Dashboard key check (set DASHBOARD_API_KEY)"
fi

echo "Rate-limit smoke check (public profile x65)"
for _ in $(seq 1 65); do
  curl -s -o /dev/null "${API_URL}/public/melika" || true
done
final_status=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/public/melika")
echo "  Final status after burst: ${final_status} (expect 429 when limiter is active)"

echo "Verification complete."
