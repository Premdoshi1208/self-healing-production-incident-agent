from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body

from backend.workflows.incident_workflow import run_incident_workflow
from backend.storage.alert_dedup_store import (
    should_process_alert,
    load_alert_dedup_store,
    clear_alert_dedup_store
)

router = APIRouter()


def as_list(value, fallback):
    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        if ";" in value:
            return [
                item.strip()
                for item in value.split(";")
                if item.strip()
            ]

        return [value]

    return fallback


def safe_dict(value):
    if isinstance(value, dict):
        return value

    return {}


def convert_alert_to_incident(alert: Dict[str, Any]):
    labels = safe_dict(alert.get("labels"))
    annotations = safe_dict(alert.get("annotations"))

    metric_snapshot = annotations.get("metric_snapshot", {})

    if not isinstance(metric_snapshot, dict):
        metric_snapshot = {}

    alertname = labels.get("alertname", "Production Alert")
    service = labels.get(
        "service",
        labels.get("job", "unknown-service")
    )

    severity = labels.get("severity", "unknown")

    logs = as_list(
        annotations.get("logs"),
        [
            annotations.get(
                "description",
                "No logs available from alert payload."
            )
        ]
    )

    trace_summary = as_list(
        annotations.get("trace_summary"),
        [
            "Prometheus/Alertmanager alert received through webhook.",
            f"Alert name: {alertname}",
            f"Service: {service}"
        ]
    )

    starts_at = alert.get("startsAt") or alert.get("starts_at")
    ends_at = alert.get("endsAt") or alert.get("ends_at")

    incident = {
        "id": int(datetime.utcnow().timestamp()),
        "title": annotations.get(
            "summary",
            alertname
        ),
        "severity": severity,
        "service": service,
        "description": annotations.get(
            "description",
            "No description provided."
        ),
        "metrics": {
            "alert_status": alert.get("status", "unknown"),
            "alertname": alertname,
            "severity": severity,
            "service": service,
            "job": labels.get("job"),
            "instance": labels.get("instance"),
            "started_at": starts_at,
            "ended_at": ends_at,
            "fingerprint": alert.get("fingerprint"),
            "generator_url": alert.get("generatorURL"),
            **metric_snapshot
        },
        "logs": logs,
        "trace_summary": trace_summary
    }

    return incident


@router.post("/prometheus/webhook")
def receive_prometheus_alert(payload: Dict[str, Any] = Body(...)):
    alerts = payload.get("alerts", [])

    if not isinstance(alerts, list):
        alerts = []

    workflow_results = []
    skipped_alerts = []
    processed_alerts = []

    for alert in alerts:
        if not isinstance(alert, dict):
            skipped_alerts.append({
                "reason": "Alert payload was not an object.",
                "alert": str(alert)
            })
            continue

        status = alert.get("status", payload.get("status", "unknown"))

        if status != "firing":
            skipped_alerts.append({
                "reason": "Alert is not firing.",
                "status": status,
                "alertname": safe_dict(alert.get("labels")).get("alertname")
            })
            continue

        should_process, fingerprint, reason = should_process_alert(alert)

        if not should_process:
            skipped_alerts.append({
                "reason": reason,
                "fingerprint": fingerprint,
                "alertname": safe_dict(alert.get("labels")).get("alertname")
            })
            continue

        incident = convert_alert_to_incident(alert)

        result = run_incident_workflow(
            incident
        )

        processed_alerts.append({
            "fingerprint": fingerprint,
            "alertname": safe_dict(alert.get("labels")).get("alertname"),
            "service": incident["service"],
            "severity": incident["severity"]
        })

        workflow_results.append(result)

    return {
        "message": "Prometheus webhook processed successfully",
        "alerts_received": len(alerts),
        "alerts_processed": len(processed_alerts),
        "alerts_skipped": len(skipped_alerts),
        "processed_alerts": processed_alerts,
        "skipped_alerts": skipped_alerts,
        "workflow_results": workflow_results
    }


@router.get("/prometheus/dedup")
def get_alert_dedup_store():
    store = load_alert_dedup_store()

    return {
        "total_entries": len(store),
        "entries": store
    }


@router.post("/prometheus/dedup/clear")
def clear_alert_dedup():
    return clear_alert_dedup_store()