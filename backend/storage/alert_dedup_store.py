import hashlib
import json
import os
from datetime import datetime, timedelta

ALERT_DEDUP_FILE = "backend/storage/alert_dedup.json"


def _now():
    return datetime.utcnow()


def _parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def load_alert_dedup_store():
    if not os.path.exists(ALERT_DEDUP_FILE):
        return {}

    try:
        with open(ALERT_DEDUP_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}


def save_alert_dedup_store(store):
    os.makedirs(os.path.dirname(ALERT_DEDUP_FILE), exist_ok=True)

    with open(ALERT_DEDUP_FILE, "w") as file:
        json.dump(store, file, indent=4)


def build_alert_fingerprint(alert):
    if alert.get("fingerprint"):
        return alert["fingerprint"]

    labels = alert.get("labels") or {}
    annotations = alert.get("annotations") or {}

    fingerprint_source = {
        "alertname": labels.get("alertname"),
        "service": labels.get("service"),
        "job": labels.get("job"),
        "instance": labels.get("instance"),
        "severity": labels.get("severity"),
        "summary": annotations.get("summary"),
        "description": annotations.get("description")
    }

    encoded = json.dumps(
        fingerprint_source,
        sort_keys=True,
        default=str
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def should_process_alert(alert, cooldown_seconds=300):
    """
    Returns:
    - should_process: bool
    - fingerprint: str
    - reason: str

    Prevents repeated workflow runs for the same firing alert.
    """

    fingerprint = build_alert_fingerprint(alert)
    store = load_alert_dedup_store()

    existing = store.get(fingerprint)

    if existing:
        last_processed_at = _parse_timestamp(
            existing.get("last_processed_at")
        )

        if last_processed_at:
            cooldown_until = last_processed_at + timedelta(
                seconds=cooldown_seconds
            )

            if _now() < cooldown_until:
                return (
                    False,
                    fingerprint,
                    "Duplicate alert skipped during cooldown window."
                )

    store[fingerprint] = {
        "last_processed_at": _now().isoformat(),
        "alertname": (alert.get("labels") or {}).get("alertname"),
        "service": (alert.get("labels") or {}).get("service"),
        "severity": (alert.get("labels") or {}).get("severity"),
        "status": alert.get("status")
    }

    save_alert_dedup_store(store)

    return True, fingerprint, "Alert accepted for processing."


def clear_alert_dedup_store():
    save_alert_dedup_store({})
    return {
        "cleared": True,
        "message": "Alert deduplication store cleared."
    }