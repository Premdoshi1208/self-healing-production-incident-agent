# Interview Demo Flow

Use this script to show the full system story clearly and quickly.

## 1. Start All Services

Terminal 1:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
uvicorn demo_service.app:app --reload --host 0.0.0.0 --port 8100
```

Terminal 3:

```bash
cd frontend
npm run dev
```

Terminal 4:

```bash
docker compose up -d
```

Optional verification:

```bash
scripts/verify_project.sh
```

## 2. Open Frontend

Open http://localhost:3000.

Point out:

- Service status cards for backend, demo service, Prometheus, Alertmanager, and Grafana.
- Quick links to backend docs, demo docs, Prometheus, Alertmanager, and Grafana.
- Recent Workflow Runs, Reflexion Memory, Playwright QA, and Demo Auth Service Controls.

## 3. Run Manual Incident Workflow

1. In "Run Incident Workflow", choose "Database Connection Leak".
2. Click "Run Workflow".
3. Wait for the workflow to complete.
4. The latest result appears and the run is saved in history.

Talk track:

> This is not just a chatbot. The backend runs a structured incident workflow: memory retrieval, RCA, fix planning, code patch generation, QA, evaluation, deterministic deploy gate, memory persistence, metrics, and run history.

## 4. Open Agent Trace Drawer

Click "Open Full Agent Trace" or click a card in Recent Workflow Runs.

Show tabs:

- Overview
- Memory
- RCA
- Fix Plan
- Code Patch
- QA
- Deploy Gate
- Evaluation

## 5. Show Deploy Gate

Open the Deploy Gate tab.

Point out:

- `staging_allowed`
- `production_allowed`
- `production_requires_human`
- `policy_engine`
- `decision_summary`
- `blocking_reasons`
- raw JSON
- approval buttons: Approve Staging, Reject Patch, Approve Production

Talk track:

> The LLM can propose a fix, but it cannot deploy. A deterministic policy engine blocks production, and production approval is a separate human action.

## 6. Open Prometheus Metrics

Open http://localhost:9090.

Query:

```promql
ai_sre_workflow_runs_total
ai_sre_deploy_gate_decisions_total
ai_sre_workflow_duration_seconds_count
ai_sre_memory_saves_total
```

Talk track:

> The AI workflow emits operational metrics just like a production service. We can alert on agent behavior, not just app behavior.

## 7. Open Grafana Dashboard

Open http://localhost:3001.

Open the provisioned "AI SRE Agent Observability" dashboard.

Show:

- Total AI Workflow Runs
- PASS Runs
- Memory Saves
- Average Workflow Duration
- Deploy Gate Decisions
- Staging Allowed
- Production Blocked
- Human Approval Required
- Deploy Gate Decisions By Service / Severity

## 8. Trigger Demo DB Leak

Return to the frontend.

In "Demo Auth Service Controls":

1. Click "Enable DB Leak".
2. Click "Send Login Traffic".
3. Watch active DB connections rise.

Talk track:

> This demo service is a real FastAPI service exposing Prometheus metrics. The bug mode intentionally stops releasing fake database connections so Prometheus can detect the leak.

## 9. Show Prometheus Alert

Open http://localhost:9090/alerts.

Wait for:

```text
DemoDatabaseConnectionLeak
```

The alert rule fires when:

```promql
demo_db_active_connections > 8
```

## 10. Show Alertmanager

Open http://localhost:9093.

Confirm the active alert is routed to:

```text
http://host.docker.internal:8000/api/prometheus/webhook
```

## 11. Show New AI Workflow Run From Alert

Return to http://localhost:3000.

Click "Refresh Service Health".

In Recent Workflow Runs, open the newest run.

Show:

- Incident title from Alertmanager annotations.
- Logs and trace summary normalized from alert annotations.
- Patch artifact path.
- Deploy gate decision.
- Approval state.

## 12. Explain Reflexion Memory

Open the Memory tab in the drawer or the Reflexion Memory section.

Talk track:

> After each successful workflow, the system stores a compact operational memory. Future incidents retrieve similar memories before the RCA agent starts reasoning, which makes the workflow feel more like an engineer consulting prior incident playbooks.

## Reset Demo

In "Demo Auth Service Controls", click "Reset All".

Optional:

```bash
docker compose down
```
