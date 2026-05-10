from prometheus_client import Counter, Histogram


WORKFLOW_RUNS_TOTAL = Counter(
    "ai_sre_workflow_runs_total",
    "Total number of AI incident workflows executed",
    ["service", "severity", "verdict"]
)


MEMORY_SAVES_TOTAL = Counter(
    "ai_sre_memory_saves_total",
    "Total number of Reflexion memory entries saved",
    ["service"]
)


WORKFLOW_DURATION_SECONDS = Histogram(
    "ai_sre_workflow_duration_seconds",
    "Time taken to complete full AI incident workflow",
    ["service", "severity"]
)


DEPLOY_GATE_DECISIONS_TOTAL = Counter(
    "ai_sre_deploy_gate_decisions_total",
    "Total number of deterministic deploy gate decisions",
    [
        "service",
        "severity",
        "staging_allowed",
        "production_allowed",
        "human_required"
    ]
)


def record_workflow_run(service, severity, verdict):
    WORKFLOW_RUNS_TOTAL.labels(
        service=service,
        severity=severity,
        verdict=verdict
    ).inc()


def record_memory_save(service):
    MEMORY_SAVES_TOTAL.labels(
        service=service
    ).inc()


def record_deploy_gate_decision(service, severity, deploy_gate_result):
    DEPLOY_GATE_DECISIONS_TOTAL.labels(
        service=service,
        severity=severity,
        staging_allowed=str(
            deploy_gate_result.get("staging_allowed", False)
        ).lower(),
        production_allowed=str(
            deploy_gate_result.get("production_allowed", False)
        ).lower(),
        human_required=str(
            deploy_gate_result.get("production_requires_human", True)
        ).lower()
    ).inc()