Perfect. Next we fill the final docs.

## 1. Paste this into `README.md`

````markdown
# Self-Healing Production Incident Agent

An end-to-end AI SRE platform that detects production incidents, performs root cause analysis, searches the codebase, generates a patch, runs deterministic tests, applies a deployment safety gate, stores Reflexion memory, and exposes observability through Prometheus and Grafana.

## One-line pitch

A production-style autonomous incident remediation agent that turns Prometheus alerts into RCA, codebase-aware fixes, tested patch diffs, deploy-gate decisions, and human-reviewable remediation artifacts.

## Why this project matters

Most AI agent projects stop at chat or simple tool calling. This project demonstrates a realistic production workflow:


Production issue
↓
Prometheus detects symptoms
↓
Alertmanager sends webhook
↓
AI incident workflow starts
↓
RCA Agent diagnoses failure
↓
Codebase Agent finds faulty files
↓
Patch Agent generates a real diff
↓
Patch is applied in a safe workspace
↓
Tests run deterministically
↓
QA validates
↓
Evaluation scores the run
↓
Deploy Gate allows staging but blocks production
↓
Human approval remains required
↓
Memory stores learning for future incidents
↓
Prometheus/Grafana track system health


## Core features

* Real FastAPI backend for AI incident orchestration
* Real demo auth service exposing Prometheus metrics
* Prometheus scraping backend and demo service metrics
* Alertmanager webhook triggering AI workflow automatically
* Codebase-aware remediation against a local target repo
* Code search agent that identifies suspected files/functions
* Patch generation as unified git diff
* Safe patch application in isolated workspace
* Deterministic test runner
* QA validation agent
* Evaluation layer with hidden-label and heuristic modes
* Deterministic deploy gate
* Human approval workflow
* Reflexion memory for incident learning
* Run history and patch artifact storage
* Grafana observability dashboard
* Interactive Next.js command-center frontend

## Architecture


Demo Auth Service
  └── /metrics
        ↓
Prometheus
        ↓
Alertmanager
        ↓
FastAPI AI Backend Webhook
        ↓
Incident Workflow
        ├── Memory Retrieval
        ├── RCA Agent
        ├── Fix Planner
        ├── Codebase Search
        ├── Code Context Builder
        ├── Real Patch Generator
        ├── Patch Artifact Writer
        ├── Safe Patch Applier
        ├── Test Runner
        ├── QA Agent
        ├── Evaluation Layer
        ├── Deploy Gate
        ├── Reflexion Memory
        └── Run History
        ↓
Frontend Dashboard + Grafana
```

## Tech stack

### Backend

* Python
* FastAPI
* LangChain / LLM-compatible agent calls
* Prometheus client
* JSON-backed local persistence
* Deterministic patch/test/deploy-gate services

### Frontend

* Next.js
* React
* Tailwind CSS
* Lucide React icons
* Interactive agent trace drawer

### Monitoring

* Prometheus
* Alertmanager
* Grafana
* Docker Compose

### Demo service

* FastAPI auth service
* Simulated DB connection pool
* Real Prometheus metrics
* Toggleable bug modes

## What is real vs simulated

### Real

* FastAPI backend
* Prometheus metrics endpoint
* Prometheus scraping
* Alertmanager webhook delivery
* Demo auth service metrics
* Codebase search over local files
* Patch diff generation
* Patch artifact saving
* Safe workspace patch application
* Deterministic tests
* Deploy gate logic
* Frontend trace visualization
* Grafana dashboard

### Simulated/demo

* The production app is a local demo auth service
* The target repo is a small local sample repo
* GitHub PR creation can be disabled unless configured
* Production deployment is intentionally blocked and requires human approval

This is a production-style local demo, not a deployed enterprise system.

## Safety model

The LLM is never allowed to directly deploy to production.

The system follows this safety pattern:

```text
LLM proposes
Deterministic tools apply/test
Deploy Gate decides staging eligibility
Human approval required for production
```

Production is always blocked by default:

```text
production_allowed = false
production_requires_human = true
```

## How to run

### 1. Backend

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
source ".venv/bin/activate"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health:

```text
http://127.0.0.1:8000/health
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

---

### 2. Demo auth service

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
source ".venv/bin/activate"
uvicorn demo_service.app:app --reload --host 0.0.0.0 --port 8100
```

Demo service health:

```text
http://127.0.0.1:8100/health
```

Demo service docs:

```text
http://127.0.0.1:8100/docs
```

---

### 3. Frontend

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent/frontend"
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

### 4. Monitoring stack

Make sure Docker Desktop is running.

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
docker compose up -d
```

Open:

```text
Prometheus:    http://localhost:9090
Alertmanager:  http://localhost:9093
Grafana:       http://localhost:3001
```

Grafana login:

```text
username: admin
password: admin
```

## Demo flow 1: Manual AI incident workflow

1. Open frontend:

```text
http://localhost:3000
```

2. Select an incident.
3. Click **Run Workflow**.
4. Open the latest run.
5. Inspect tabs:

```text
RCA
Fix Plan
Code Search
Patch Diff
Tests
QA
Evaluation
Deploy Gate
Pull Request
```

Expected result:

```text
Code Search finds login.py/db.py
Patch Diff generates try/finally cleanup
Tests pass
Deploy Gate allows staging
Production remains blocked
Human approval required
```

## Demo flow 2: Prometheus-style alert simulator

1. Open frontend.
2. Go to **Prometheus Alert Simulator**.
3. Choose `Database Connection Pool Exhausted`.
4. Click **Send Alert**.
5. The backend receives a webhook and starts the AI workflow.
6. Open the latest run and inspect the trace drawer.

## Demo flow 3: Real demo service DB leak

1. Open frontend.
2. Go to **Demo Auth Service Controls**.
3. Click **Enable DB Leak**.
4. Click **Send Login Traffic**.
5. Prometheus detects:

```text
demo_db_active_connections > 8
```

6. Open Prometheus alerts:

```text
http://localhost:9090/alerts
```

7. Confirm `DemoDatabaseConnectionLeak` is firing.
8. Open Alertmanager:

```text
http://localhost:9093
```

9. Confirm Alertmanager received the alert.
10. Backend webhook starts the AI workflow.
11. Frontend shows a new run.
12. Open the run and inspect:

```text
Code Search
Patch Diff
Tests
Deploy Gate
```

## Important Prometheus queries

```promql
demo_db_active_connections
```

```promql
ai_sre_workflow_runs_total
```

```promql
ai_sre_deploy_gate_decisions_total
```

```promql
ai_sre_memory_saves_total
```

```promql
ai_sre_workflow_duration_seconds_count
```

## Alert deduplication

Repeated Alertmanager webhooks for the same firing alert are deduplicated.

Expected behavior:

```text
First alert → workflow runs
Repeated same alert → skipped during cooldown
```

Dedup endpoint:

```text
GET /api/prometheus/dedup
POST /api/prometheus/dedup/clear
```

## Codebase-aware remediation

The system searches a local target repo:

```text
target_repo/
```

For a DB leak incident, it identifies files like:

```text
target_repo/services/auth/login.py
target_repo/services/auth/db.py
target_repo/tests/test_login.py
```

It then generates a patch like:

```diff
conn = get_connection()
try:
    user = conn.query_user(username)
    ...
finally:
    conn.close()
```

The patch is applied in:

```text
patch_workspaces/
```

The original target repo is not directly modified.

## Patch artifacts

Generated patch artifacts are saved in:

```text
generated_patches/
```

Each artifact contains:

* incident summary
* RCA
* fix plan
* code search result
* patch diff
* test result
* QA validation
* evaluation
* deploy gate result

## Deploy Gate

The deploy gate is deterministic.

It checks:

* QA approval
* evaluation verdict
* evaluation score
* patch apply status
* test status
* severity
* human approval requirement

Example result:

```json
{
  "staging_allowed": true,
  "production_allowed": false,
  "production_requires_human": true,
  "decision_summary": "Patch is approved for staging deployment. Production deployment still requires human approval."
}
```

## Human approval

Production deployment is never automatic.

Approval objects track:

```text
pending
approved_staging
rejected
approved_production
```

The frontend shows approval status in the run drawer.

## Future improvements

* Real GitHub PR creation with token
* Kubernetes staging deployment
* PostgreSQL/MongoDB instead of JSON storage
* Authentication and RBAC
* Webhook signing
* CI/CD integration
* Cloud deployment
* More realistic service topology
* OpenTelemetry distributed tracing
* More advanced test selection
* Cost and token tracking per agent step

## Final project story

This project demonstrates an end-to-end autonomous SRE remediation loop:

```text
A real demo service develops a DB connection leak.
Prometheus detects the issue.
Alertmanager sends the alert to the AI backend.
The AI performs RCA.
The Codebase Agent finds the faulty login code.
The Patch Agent generates a real diff.
The patch is applied safely in a workspace.
Tests pass.
QA validates.
Evaluation scores the run.
Deploy Gate allows staging but blocks production.
Human approval remains required.
Memory stores the learning.
Grafana and the frontend show the full trace.
```

````

## 2. Paste this into `docs/demo_flow.md`

```markdown
# Demo Flow — Self-Healing Production Incident Agent

Use this script when showing the project to recruiters, founders, or interviewers.

## 1. Start all services

### Backend

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
source ".venv/bin/activate"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
````

### Demo auth service

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
source ".venv/bin/activate"
uvicorn demo_service.app:app --reload --host 0.0.0.0 --port 8100
```

### Frontend

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent/frontend"
npm run dev
```

### Monitoring

```bash
cd "/Users/mac/Desktop/Self-Healing Production Agent"
docker compose up -d
```

## 2. Open main pages

```text
Frontend:      http://localhost:3000
Backend docs:  http://127.0.0.1:8000/docs
Demo docs:     http://127.0.0.1:8100/docs
Prometheus:    http://localhost:9090
Alertmanager:  http://localhost:9093
Grafana:       http://localhost:3001
```

## 3. Verify Prometheus targets

Open:

```text
http://localhost:9090/targets
```

Confirm both are UP:

```text
ai-sre-backend
demo-auth-service
```

## 4. Manual workflow demo

In frontend:

1. Select a sample incident.
2. Click **Run Workflow**.
3. Wait for completion.
4. Open the latest run.

Show these tabs:

```text
RCA
Fix Plan
Code Search
Patch Diff
Tests
QA
Evaluation
Deploy Gate
```

Explain:

```text
The agent diagnoses the issue, finds relevant code, generates a patch, applies it safely, runs tests, and uses a deterministic deploy gate.
```

## 5. Real Prometheus DB leak demo

### Reset first

```bash
curl -X POST http://127.0.0.1:8100/simulate/reset
curl -X POST http://127.0.0.1:8000/api/prometheus/dedup/clear
```

### Trigger DB leak

```bash
curl -X POST http://127.0.0.1:8100/simulate/db-leak/on
```

Generate traffic:

```bash
for i in {1..15}; do
  curl -X POST http://127.0.0.1:8100/login
  echo ""
done
```

## 6. Show Prometheus metric

Open Prometheus:

```text
http://localhost:9090
```

Query:

```promql
demo_db_active_connections
```

Expected:

```text
Value rises to 9 or 10
```

## 7. Show Prometheus alert

Open:

```text
http://localhost:9090/alerts
```

Show:

```text
DemoDatabaseConnectionLeak FIRING
```

Explain:

```text
Prometheus detected a real metric condition from the demo auth service.
```

## 8. Show Alertmanager

Open:

```text
http://localhost:9093
```

Show:

```text
DemoDatabaseConnectionLeak
```

Explain:

```text
Alertmanager received the alert and sent it to the AI backend webhook.
```

## 9. Show backend workflow logs

In backend terminal, show:

```text
POST /api/prometheus/webhook
STARTING INCIDENT WORKFLOW
```

Then show steps:

```text
RCA
Fix Plan
Codebase Search
Patch Diff
Patch Apply
Tests
QA
Evaluation
Deploy Gate
Memory
Metrics
Run History
```

## 10. Show frontend latest run

Open frontend:

```text
http://localhost:3000
```

Click **Refresh**.

Open the newest run:

```text
Database Connection Leak
auth-service
critical
```

Show:

### Code Search

Expected files:

```text
services/auth/login.py
services/auth/db.py
tests/test_login.py
```

### Patch Diff

Expected fix:

```text
Wrap DB usage in try/finally and close connection in all paths.
```

### Tests

Expected:

```text
3 passed, 0 failed
```

### Deploy Gate

Expected:

```text
staging_allowed: true
production_allowed: false
production_requires_human: true
```

## 11. Show deduplication

Send the same webhook twice or wait for Alertmanager repeat.

Expected:

```text
First alert: processed
Second same alert: skipped during cooldown
```

Check:

```text
http://127.0.0.1:8000/api/prometheus/dedup
```

Explain:

```text
This prevents the same firing alert from spamming the AI workflow repeatedly.
```

## 12. Show Grafana

Open:

```text
http://localhost:3001
```

Show dashboard panels:

```text
Workflow runs
Deploy gate decisions
Memory saves
Workflow duration
Runs by service
```

## 13. Final explanation

Say:

```text
This project demonstrates a production-style AI SRE agent. A real service emits metrics, Prometheus detects an incident, Alertmanager triggers the AI backend, the agent performs RCA, searches the codebase, generates a patch, applies it safely, runs tests, evaluates the result, blocks production through a deterministic deploy gate, and stores Reflexion memory for future incidents.
```

## 14. Reset after demo

```bash
curl -X POST http://127.0.0.1:8100/simulate/reset
```

Optional:

```bash
curl -X POST http://127.0.0.1:8000/api/prometheus/dedup/clear
```

````

After this, run:

```bash
git add README.md docs/demo_flow.md
git commit -m "Add final README and demo flow documentation"
````
