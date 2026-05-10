# Self-Healing Production Incident Agent

An AI SRE command center that turns production alerts into RCA, fix plans, patch artifacts, QA signals, deterministic deploy-gate decisions, human approvals, metrics, and reusable Reflexion memory.

## Architecture

```text
Demo Auth Service :8100
  exposes /metrics and controlled bug modes
        |
        v
Prometheus :9090 ----> Alertmanager :9093
        |                    |
        |                    v
        |        AI Backend Webhook :8000/api/prometheus/webhook
        |                    |
        v                    v
Grafana :3001       Incident Workflow
                     Memory Retrieval
                     RCA Agent
                     Fix Planner Agent
                     Codebase Search Agent
                     Code Context Builder
                     Real Patch Diff Agent
                     Patch Artifact
                     Safe Workspace Patch Apply
                     Deterministic Test Runner
                     QA Agent
                     Evaluation Layer
                     Deterministic Deploy Gate
                     Human Approval Store
                     Reflexion Memory
                     Patch Artifact
                     Prometheus Metrics
                     Run History
                            |
                            v
Frontend Dashboard :3000
```

## Problem It Solves

Production incident response is usually scattered across alerts, logs, traces, dashboards, pull requests, runbooks, and chat. This project demonstrates a safer pattern for AI-assisted operations: the LLM investigates and proposes, while deterministic policy and human approval decide what can ship.

## Key Features

- FastAPI AI backend with manual incident runs and Alertmanager webhook ingestion.
- Real Prometheus metrics for workflow runs, duration, memory saves, and deploy gate decisions.
- Demo auth service with real metrics and controlled DB leak, slow login, and random error modes.
- Prometheus alert rules that detect the demo DB connection leak and send Alertmanager webhooks.
- Next.js dashboard with service health, demo controls, run history search, trace drawer, deploy gate tab, approvals, and latest QA result.
- Reflexion memory persisted to JSON for future incident context.
- Codebase-aware search over a configured local repo with suspected files, matched terms, reasons, and previews.
- Real unified diffs saved as generated patch artifacts in `generated_patches/`.
- Safe patch application to isolated `patch_workspaces/` copies, never directly to the source repo.
- Deterministic test runner for patched workspaces with results saved to `backend/storage/test_runs.json`.
- Playwright E2E test setup plus `POST /api/qa/run-playwright`.
- Optional GitHub PR preparation stub that is safe when credentials are missing.
- Human approval API for staging approval, rejection, and explicit production approval.

## Codebase-Aware Remediation

The workflow can inspect a real target codebase instead of only reasoning from logs and metrics.

Local repo mode:

```text
CODEBASE_LOCAL_PATH=target_repo
```

When configured, the Codebase Search Agent scans the local repo, ignores noisy folders such as `.git`, `node_modules`, `.venv`, `dist`, and `build`, then ranks suspected files from incident, log, trace, and RCA keywords. The Code Context Builder reads only the top files and caps excerpt size so the LLM never receives an entire repo dump.

GitHub mode:

```text
GITHUB_TOKEN=
GITHUB_REPO=owner/repo
GITHUB_DEFAULT_BRANCH=main
ENABLE_GITHUB_PR=false
```

GitHub PR creation is disabled unless `ENABLE_GITHUB_PR=true` and credentials are present. The endpoint prepares branch, title, body, and patch metadata for human-controlled PR creation. It does not deploy or push automatically.

Patch artifacts:

- Each workflow saves a markdown artifact under `generated_patches/`.
- Artifacts include incident metadata, RCA, fix plan, codebase search, generated unified diff, patch apply result, test result, QA, evaluation, and deploy gate.
- Real patches are applied only to `patch_workspaces/<run_id>/`, never to `CODEBASE_LOCAL_PATH`.

Deploy Gate behavior:

- Staging requires QA approval, evaluation verdict `PASS`, score `>= 0.85`, successful patch apply if a real diff exists, and passing deterministic tests if tests ran.
- Production is always blocked by default.
- `production_requires_human` is always `true`.

## Tech Stack

- Backend: FastAPI, Python 3.9, LangChain OpenAI client, Pydantic, Prometheus client.
- Frontend: Next.js 14, React, Tailwind CSS, lucide-react.
- Monitoring: Prometheus, Alertmanager, Grafana, Docker Compose.
- QA: Playwright.
- Persistence: JSON stores for workflow runs, memory, approvals, and test runs.

## Real vs Simulated

Real:
- FastAPI services, Prometheus scraping, Alertmanager webhook delivery, Grafana dashboards.
- End-to-end alert loop from demo service metrics to AI workflow history.
- Deterministic deploy gate and human approval persistence.
- Codebase search, unified diff artifact persistence, isolated patch apply, deterministic target tests, and Playwright test execution.

Simulated:
- The generated code patch is saved for review, not applied to production automatically.
- The demo auth service intentionally contains controllable failure modes.
- GitHub PR creation is a safe stub unless future credentials and branch logic are added.

Safety note: the LLM never deploys directly. Production is always blocked by the deterministic deploy gate and requires a human approval record.

## Environment

Create a `.env` from `.env.example`:

```bash
cp .env.example .env
```

Variables:

```text
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=deepseek/deepseek-chat-v3-0324
OPENAI_TIMEOUT=20
OPENAI_MAX_RETRIES=0
GITHUB_TOKEN=
GITHUB_REPO=
GITHUB_DEFAULT_BRANCH=main
CODEBASE_LOCAL_PATH=target_repo
ENABLE_GITHUB_PR=false
```

If `OPENAI_API_KEY` is missing or invalid, workflow runs fail closed with structured error details and deployment remains blocked.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend
npm install
npx playwright install chromium
cd ..
```

## Run Locally

Terminal 1, AI backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2, demo auth service:

```bash
uvicorn demo_service.app:app --reload --host 0.0.0.0 --port 8100
```

Terminal 3, frontend:

```bash
cd frontend
npm run dev
```

Terminal 4, monitoring:

```bash
docker compose up -d
```

Open:

- Frontend: http://localhost:3000
- Backend docs: http://127.0.0.1:8000/docs
- Demo service docs: http://127.0.0.1:8100/docs
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3001

## Verify

```bash
scripts/verify_project.sh
```

The script checks backend, demo service, frontend, Prometheus, Alertmanager, Grafana, both `/metrics` endpoints, and Prometheus targets for `ai-sre-backend` and `demo-auth-service`.

## Demo Flow 1: Manual Incident

1. Open http://localhost:3000.
2. Choose a fake incident in "Run Incident Workflow".
3. Click "Run Workflow".
4. Open the agent trace drawer.
5. Show RCA, fix plan, code patch, QA, evaluation, deploy gate, patch artifact, and approval buttons.

## Demo Flow 2: Prometheus Simulator

1. Open the dashboard.
2. In "Prometheus Alert Simulator", choose an alert template.
3. Click "Send Alert".
4. The backend webhook converts the payload into an incident and runs the full workflow.
5. Refresh Recent Workflow Runs and open the new trace.

## Demo Flow 3: Real DB Leak Alert Loop

1. Open the dashboard and confirm service health.
2. In "Demo Auth Service Controls", click "Enable DB Leak".
3. Click "Send Login Traffic".
4. Open Prometheus alerts at http://localhost:9090/alerts and wait for `DemoDatabaseConnectionLeak`.
5. Open Alertmanager at http://localhost:9093 and confirm the alert is active.
6. Alertmanager sends the webhook to the AI backend.
7. Refresh the dashboard and open the new workflow run.
8. Show the Code Search tab finding `target_repo/services/auth/login.py` or `target_repo/services/auth/db.py`.
9. Show the Patch Diff tab with a standard `diff --git` patch.
10. Show the Tests tab proving the patch was applied to a safe workspace and validated.
11. Show the Deploy Gate tab approving staging only when deterministic checks pass and still requiring human approval for production.
12. Query Prometheus:

```promql
ai_sre_workflow_runs_total
ai_sre_deploy_gate_decisions_total
```

13. Open Grafana and review workflow plus deploy gate panels.

## Demo Flow 4: Codebase-Aware Remediation

1. Set `CODEBASE_LOCAL_PATH=target_repo` in `.env`.
2. Run the manual `Database Connection Leak` incident or trigger the real demo service DB leak.
3. The Codebase Search Agent ranks auth/database files from `target_repo/`.
4. The Real Patch Agent generates a unified diff that wraps login database access in `try/finally`.
5. The Patch Apply Service copies `target_repo/` into `patch_workspaces/` and applies the diff there.
6. The Test Runner runs the target repo tests and stores the result in `backend/storage/test_runs.json`.
7. The deploy gate allows staging only if QA, evaluation, patch apply, and tests pass.
8. The Pull Request tab can call `POST /api/github/pr/from-run/{run_id}` and will safely report disabled unless GitHub is configured.

## QA

Run E2E tests from the frontend folder:

```bash
cd frontend
npm run test:e2e
```

Or run through the backend:

```bash
curl -X POST http://127.0.0.1:8000/api/qa/run-playwright
```

Test results are saved to `backend/storage/test_runs.json`. The workflow saves target-repo test results in `test_result` and can also expose latest Playwright QA runs through the dashboard.

## Human Approval API

```bash
curl http://127.0.0.1:8000/api/approvals
curl http://127.0.0.1:8000/api/approvals/pending
curl -X POST http://127.0.0.1:8000/api/approvals/{run_id}/approve-staging
curl -X POST http://127.0.0.1:8000/api/approvals/{run_id}/reject
curl -X POST http://127.0.0.1:8000/api/approvals/{run_id}/approve-production
```

## GitHub PR Stub

```bash
curl -X POST http://127.0.0.1:8000/api/github/pr/from-run/{run_id}
```

Without `ENABLE_GITHUB_PR=true`, `GITHUB_TOKEN`, and `GITHUB_REPO`, the endpoint returns a clear disabled message. With credentials, it prepares branch and PR metadata for a future safe implementation.

## Screenshots

Add screenshots here after recording the demo:

- `docs/screenshots/dashboard.png`
- `docs/screenshots/agent-trace.png`
- `docs/screenshots/prometheus-alert.png`
- `docs/screenshots/grafana-deploy-gate.png`

## Project Structure

```text
backend/
  agents/
  api/routes/
  core/
  evaluation/
  memory/
  observability/
  services/
  storage/
  workflows/
demo_service/
frontend/
monitoring/
generated_patches/
target_repo/
docs/
scripts/
README.md
.env.example
docker-compose.yml
```

## Future Work

- Apply generated patches to isolated branches and open real PRs after human review.
- Add authenticated users and role-based approval permissions.
- Store run history in Postgres or MongoDB instead of JSON.
- Add OpenTelemetry traces and log ingestion from real services.
- Add CI that runs backend tests, Playwright tests, and dashboard provisioning checks.
