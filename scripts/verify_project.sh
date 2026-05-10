#!/usr/bin/env bash

set -u

PASS_COUNT=0
FAIL_COUNT=0

check_url() {
  local label="$1"
  local url="$2"

  if curl -fsS --max-time 15 "$url" >/tmp/ai_sre_verify_response 2>/tmp/ai_sre_verify_error; then
    printf "PASS %-32s %s\n" "$label" "$url"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf "FAIL %-32s %s\n" "$label" "$url"
    sed 's/^/     /' /tmp/ai_sre_verify_error
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_path() {
  local label="$1"
  local path="$2"

  if [ -e "$path" ]; then
    printf "PASS %-32s %s\n" "$label" "$path"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf "FAIL %-32s %s\n" "$label" "$path"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_prometheus_targets() {
  local url="http://127.0.0.1:9090/api/v1/targets"

  if ! curl -fsS --max-time 5 "$url" >/tmp/ai_sre_targets.json 2>/tmp/ai_sre_verify_error; then
    printf "FAIL %-32s %s\n" "Prometheus targets API" "$url"
    sed 's/^/     /' /tmp/ai_sre_verify_error
    FAIL_COUNT=$((FAIL_COUNT + 1))
    return
  fi

  python3 - <<'PY'
import json
import sys

with open("/tmp/ai_sre_targets.json", "r") as file:
    data = json.load(file)

active_targets = data.get("data", {}).get("activeTargets", [])
health_by_job = {}

for target in active_targets:
    labels = target.get("labels", {})
    job = labels.get("job")
    health = target.get("health")
    if job:
        health_by_job[job] = health

required = ["ai-sre-backend", "demo-auth-service"]
missing = [job for job in required if health_by_job.get(job) != "up"]

if missing:
    print("missing_or_down=" + ",".join(missing))
    sys.exit(1)

print("all_required_targets_up")
PY

  if [ "$?" -eq 0 ]; then
    printf "PASS %-32s ai-sre-backend and demo-auth-service are UP\n" "Prometheus targets"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf "FAIL %-32s expected ai-sre-backend and demo-auth-service UP\n" "Prometheus targets"
    sed 's/^/     /' /tmp/ai_sre_targets.json | head -20
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

printf "\nSelf-Healing Production Incident Agent verification\n"
printf "===================================================\n\n"

check_url "Backend health" "http://127.0.0.1:8000/health"
check_url "Backend metrics" "http://127.0.0.1:8000/metrics"
check_url "Demo service health" "http://127.0.0.1:8100/health"
check_url "Demo service metrics" "http://127.0.0.1:8100/metrics"
check_url "Frontend" "http://localhost:3000"
check_url "Prometheus" "http://127.0.0.1:9090/-/ready"
check_url "Alertmanager" "http://127.0.0.1:9093/-/ready"
check_url "Grafana" "http://127.0.0.1:3001/api/health"
check_url "Codebase status API" "http://127.0.0.1:8000/api/codebase/status"
check_url "Patch artifacts API" "http://127.0.0.1:8000/api/patches"
check_path "generated_patches folder" "generated_patches"
check_path "target_repo folder" "target_repo"
check_prometheus_targets

printf "\nSummary: %s passed, %s failed\n" "$PASS_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi

exit 0
