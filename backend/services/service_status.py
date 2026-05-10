import httpx


SERVICE_CHECKS = [
    {
        "name": "Backend",
        "key": "backend",
        "url": "http://127.0.0.1:8000/health",
        "link": "http://127.0.0.1:8000/docs"
    },
    {
        "name": "Demo Service",
        "key": "demo_service",
        "url": "http://127.0.0.1:8100/health",
        "link": "http://127.0.0.1:8100/docs"
    },
    {
        "name": "Prometheus",
        "key": "prometheus",
        "url": "http://127.0.0.1:9090/-/ready",
        "link": "http://127.0.0.1:9090"
    },
    {
        "name": "Alertmanager",
        "key": "alertmanager",
        "url": "http://127.0.0.1:9093/-/ready",
        "link": "http://127.0.0.1:9093"
    },
    {
        "name": "Grafana",
        "key": "grafana",
        "url": "http://127.0.0.1:3001/api/health",
        "link": "http://127.0.0.1:3001"
    }
]


def check_url(client, item):
    try:
        response = client.get(item["url"])
        healthy = 200 <= response.status_code < 400

        payload = None
        try:
            payload = response.json()
        except ValueError:
            payload = response.text[:300]

        return {
            **item,
            "status": "up" if healthy else "down",
            "http_status": response.status_code,
            "details": payload
        }
    except Exception as error:
        return {
            **item,
            "status": "down",
            "http_status": None,
            "details": f"{type(error).__name__}: {error}"
        }


def get_service_statuses():
    with httpx.Client(timeout=2.0, follow_redirects=False) as client:
        services = [check_url(client, item) for item in SERVICE_CHECKS]

        try:
            targets_response = client.get("http://127.0.0.1:9090/api/v1/targets")
            targets = targets_response.json()
        except Exception as error:
            targets = {
                "status": "error",
                "error": f"{type(error).__name__}: {error}"
            }

    return {
        "services": services,
        "prometheus_targets": targets
    }
