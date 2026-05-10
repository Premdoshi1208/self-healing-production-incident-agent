#!/bin/bash

echo "========================================"
echo " Self-Healing Incident Agent Verification"
echo "========================================"

check_url () {
  NAME=$1
  URL=$2

  if curl -s --max-time 5 "$URL" > /dev/null; then
    echo "✅ $NAME reachable: $URL"
  else
    echo "❌ $NAME NOT reachable: $URL"
  fi
}

check_path () {
  NAME=$1
  PATH_TO_CHECK=$2

  if [ -e "$PATH_TO_CHECK" ]; then
    echo "✅ $NAME exists: $PATH_TO_CHECK"
  else
    echo "❌ $NAME missing: $PATH_TO_CHECK"
  fi
}

echo ""
echo "Checking services..."
check_url "AI Backend Health" "http://127.0.0.1:8000/health"
check_url "AI Backend Metrics" "http://127.0.0.1:8000/metrics"
check_url "Demo Auth Service Health" "http://127.0.0.1:8100/health"
check_url "Demo Auth Service Metrics" "http://127.0.0.1:8100/metrics"
check_url "Frontend" "http://localhost:3000"
check_url "Prometheus" "http://localhost:9090"
check_url "Alertmanager" "http://localhost:9093"
check_url "Grafana" "http://localhost:3001"

echo ""
echo "Checking backend API endpoints..."
check_url "Runs Summary" "http://127.0.0.1:8000/api/runs/summary"
check_url "Recent Runs" "http://127.0.0.1:8000/api/runs/recent"
check_url "Recent Memory" "http://127.0.0.1:8000/api/memory/recent"
check_url "Codebase Status" "http://127.0.0.1:8000/api/codebase/status"
check_url "Alert Dedup Store" "http://127.0.0.1:8000/api/prometheus/dedup"

echo ""
echo "Checking project folders..."
check_path "Target Repo" "target_repo"
check_path "Generated Patches Folder" "generated_patches"
check_path "Patch Workspaces Folder" "patch_workspaces"
check_path "Monitoring Config" "monitoring/prometheus/prometheus.yml"
check_path "Alert Rules" "monitoring/prometheus/alert_rules.yml"
check_path "Alertmanager Config" "monitoring/alertmanager/alertmanager.yml"
check_path "Docker Compose" "docker-compose.yml"
check_path "README" "README.md"
check_path "Demo Flow Doc" "docs/demo_flow.md"

echo ""
echo "Checking Prometheus targets..."
if curl -s --max-time 5 "http://localhost:9090/api/v1/targets" | grep -q "demo-auth-service"; then
  echo "✅ Prometheus knows demo-auth-service target"
else
  echo "❌ Prometheus demo-auth-service target not found"
fi

if curl -s --max-time 5 "http://localhost:9090/api/v1/targets" | grep -q "ai-sre-backend"; then
  echo "✅ Prometheus knows ai-sre-backend target"
else
  echo "❌ Prometheus ai-sre-backend target not found"
fi

echo ""
echo "Verification complete."
echo "If any item failed, make sure backend, demo service, frontend, Docker monitoring stack are all running."
