# Codebase-Aware Remediation Flow

This demo shows the incident agent moving from observability symptoms to a concrete patch proposal against a real local codebase.

## Setup

1. Create `.env` from `.env.example`.
2. Set:

```text
CODEBASE_LOCAL_PATH=target_repo
ENABLE_GITHUB_PR=false
```

3. Start the AI backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Start the demo auth service:

```bash
uvicorn demo_service.app:app --reload --host 0.0.0.0 --port 8100
```

5. Start the frontend:

```bash
cd frontend
npm run dev
```

6. Start monitoring:

```bash
docker compose up -d
```

## Interview Demo Script

1. Open http://localhost:3000 and show the command-center dashboard.
2. Confirm service status cards are healthy.
3. Trigger the DB leak from Demo Auth Service Controls:
   - Enable DB Leak
   - Send Login Traffic
4. Open Prometheus at http://localhost:9090/alerts and show `DemoDatabaseConnectionLeak`.
5. Open Alertmanager at http://localhost:9093 and show the active alert.
6. Refresh Recent Workflow Runs in the frontend and open the new run.
7. In Overview, explain the full incident chain and safety posture.
8. In RCA, show that the agent identifies missing database/session cleanup.
9. In Fix Plan, show the proposed cleanup strategy.
10. In Code Search, show suspected files such as:

```text
target_repo/services/auth/login.py
target_repo/services/auth/db.py
```

11. In Patch Diff, show the generated `diff --git` patch that wraps login DB access in `try/finally`.
12. In Tests, show the deterministic target tests and their pass/fail result.
13. In Deploy Gate, explain:
    - staging is allowed only if QA, evaluation, patch apply, and tests pass
    - production is never auto-approved
    - human approval is required
14. In Pull Request, click Prepare PR From Run. With default local config, it should safely say GitHub PR is disabled.
15. Open `generated_patches/` and show the markdown artifact for the run.
16. Open Prometheus and query:

```promql
ai_sre_workflow_runs_total
ai_sre_deploy_gate_decisions_total
```

17. Open Grafana at http://localhost:3001 and show workflow/deploy gate panels.

## What Is Real

- The demo auth service exposes real Prometheus metrics.
- Prometheus and Alertmanager perform the alert loop.
- The backend converts alerts into incidents.
- The Codebase Search Agent scans `target_repo/`.
- The Patch Agent emits a real unified diff.
- The Patch Apply Service copies the codebase into `patch_workspaces/` before applying.
- The Test Runner executes deterministic tests in the patched workspace.
- Run history, test runs, patch artifacts, memory, and approvals persist to local JSON/markdown files.

## Safety Line

The LLM proposes RCA, plans, and patches. Deterministic code applies patches only to safe workspaces, tests them, and gates deployment. Production deployment is always blocked until a human explicitly approves it.
