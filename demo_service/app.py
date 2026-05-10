import random
import time
from threading import Lock

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)


app = FastAPI(
    title="Demo Auth Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Prometheus Metrics
# -----------------------------

LOGIN_REQUESTS_TOTAL = Counter(
    "demo_auth_login_requests_total",
    "Total number of login requests"
)

LOGIN_ERRORS_TOTAL = Counter(
    "demo_auth_login_errors_total",
    "Total number of login errors"
)

LOGIN_LATENCY_SECONDS = Histogram(
    "demo_auth_login_latency_seconds",
    "Login request latency in seconds"
)

DB_ACTIVE_CONNECTIONS = Gauge(
    "demo_db_active_connections",
    "Current active database connections"
)

DB_POOL_EXHAUSTED_TOTAL = Counter(
    "demo_db_pool_exhausted_total",
    "Total number of database pool exhaustion events"
)

BUG_MODE_ENABLED = Gauge(
    "demo_service_bug_mode_enabled",
    "Whether bug simulation mode is enabled",
    ["bug_type"]
)


# -----------------------------
# Fake DB Pool
# -----------------------------

class FakeDatabasePool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.active_connections = 0
        self.lock = Lock()

    def acquire(self):
        with self.lock:
            if self.active_connections >= self.max_connections:
                DB_POOL_EXHAUSTED_TOTAL.inc()
                raise RuntimeError("Database connection pool exhausted")

            self.active_connections += 1
            DB_ACTIVE_CONNECTIONS.set(self.active_connections)

            return {
                "connection_id": random.randint(1000, 9999)
            }

    def release(self):
        with self.lock:
            if self.active_connections > 0:
                self.active_connections -= 1

            DB_ACTIVE_CONNECTIONS.set(self.active_connections)

    def reset(self):
        with self.lock:
            self.active_connections = 0
            DB_ACTIVE_CONNECTIONS.set(0)


db_pool = FakeDatabasePool(max_connections=10)


# -----------------------------
# Bug Simulation State
# -----------------------------

bug_state = {
    "db_leak": False,
    "slow_login": False,
    "random_errors": False
}


def update_bug_metrics():
    BUG_MODE_ENABLED.labels(bug_type="db_leak").set(1 if bug_state["db_leak"] else 0)
    BUG_MODE_ENABLED.labels(bug_type="slow_login").set(1 if bug_state["slow_login"] else 0)
    BUG_MODE_ENABLED.labels(bug_type="random_errors").set(1 if bug_state["random_errors"] else 0)


update_bug_metrics()


# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def root():
    return {
        "message": "Demo Auth Service is running",
        "purpose": "This service intentionally exposes real metrics for Prometheus monitoring."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "active_db_connections": db_pool.active_connections,
        "bug_state": bug_state
    }


@app.post("/login")
def login():
    LOGIN_REQUESTS_TOTAL.inc()

    start_time = time.time()
    connection = None

    try:
        connection = db_pool.acquire()

        if bug_state["slow_login"]:
            time.sleep(2.5)
        else:
            time.sleep(0.15)

        if bug_state["random_errors"] and random.random() < 0.35:
            LOGIN_ERRORS_TOTAL.inc()
            raise HTTPException(
                status_code=500,
                detail="Random simulated login failure"
            )

        return {
            "status": "success",
            "message": "Login completed",
            "connection_id": connection["connection_id"],
            "active_db_connections": db_pool.active_connections
        }

    except RuntimeError as error:
        LOGIN_ERRORS_TOTAL.inc()

        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    finally:
        duration = time.time() - start_time
        LOGIN_LATENCY_SECONDS.observe(duration)

        # This is the intentional bug:
        # If db_leak is ON, connections are NOT released.
        if connection is not None and not bug_state["db_leak"]:
            db_pool.release()


@app.post("/simulate/db-leak/on")
def enable_db_leak():
    bug_state["db_leak"] = True
    update_bug_metrics()

    return {
        "message": "DB leak simulation enabled",
        "bug_state": bug_state
    }


@app.post("/simulate/db-leak/off")
def disable_db_leak():
    bug_state["db_leak"] = False
    db_pool.reset()
    update_bug_metrics()

    return {
        "message": "DB leak simulation disabled and pool reset",
        "bug_state": bug_state
    }


@app.post("/simulate/slow-login/on")
def enable_slow_login():
    bug_state["slow_login"] = True
    update_bug_metrics()

    return {
        "message": "Slow login simulation enabled",
        "bug_state": bug_state
    }


@app.post("/simulate/slow-login/off")
def disable_slow_login():
    bug_state["slow_login"] = False
    update_bug_metrics()

    return {
        "message": "Slow login simulation disabled",
        "bug_state": bug_state
    }


@app.post("/simulate/random-errors/on")
def enable_random_errors():
    bug_state["random_errors"] = True
    update_bug_metrics()

    return {
        "message": "Random error simulation enabled",
        "bug_state": bug_state
    }


@app.post("/simulate/random-errors/off")
def disable_random_errors():
    bug_state["random_errors"] = False
    update_bug_metrics()

    return {
        "message": "Random error simulation disabled",
        "bug_state": bug_state
    }


@app.post("/simulate/reset")
def reset_simulation():
    bug_state["db_leak"] = False
    bug_state["slow_login"] = False
    bug_state["random_errors"] = False

    db_pool.reset()
    update_bug_metrics()

    return {
        "message": "All simulations reset",
        "bug_state": bug_state,
        "active_db_connections": db_pool.active_connections
    }


@app.post("/simulate/login-traffic")
def send_login_traffic(count: int = Query(default=12, ge=1, le=100)):
    successes = 0
    failures = 0
    last_error = None

    for _ in range(count):
        try:
            login()
            successes += 1
        except HTTPException as error:
            failures += 1
            last_error = error.detail

    return {
        "message": f"Sent {count} login requests",
        "successes": successes,
        "failures": failures,
        "last_error": last_error,
        "active_db_connections": db_pool.active_connections,
        "bug_state": bug_state
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
