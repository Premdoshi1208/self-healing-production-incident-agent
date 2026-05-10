FAKE_INCIDENTS = [

    {
        "id": 1,
        "title": "Database Connection Leak",
        "severity": "critical",
        "service": "auth-service",

        "description": (
            "API latency increased dramatically and users are "
            "experiencing login delays."
        ),

        "metrics": {
            "cpu_usage": "92%",
            "memory_usage": "88%",
            "p95_latency": "3200ms",
            "error_rate": "18%"
        },

        "logs": [
            "Database connection pool exhausted",
            "Timeout while querying users table",
            "Too many active database sessions"
        ],

        "trace_summary": [
            "POST /login → db.query()",
            "Database session remained active",
            "Repeated connection retries detected"
        ],

        # Hidden evaluation fields
        "expected_root_cause": (
            "Missing database session cleanup "
            "(db.close()) causing connection leak."
        ),

        "expected_fix": (
            "Close database sessions properly after queries."
        )
    },

    {
        "id": 2,
        "title": "Frontend Dashboard Crash",
        "severity": "high",
        "service": "dashboard-frontend",

        "description": (
            "Dashboard crashes while loading user profile data."
        ),

        "metrics": {
            "frontend_errors": "146",
            "crash_rate": "37%",
            "page_load_time": "5400ms"
        },

        "logs": [
            "TypeError: Cannot read property 'name' of undefined",
            "React component crashed during render"
        ],

        "trace_summary": [
            "GET /profile executed successfully",
            "Frontend rendering failed",
            "Null object passed into component"
        ],

        # Hidden evaluation fields
        "expected_root_cause": (
            "Frontend component does not handle null user object."
        ),

        "expected_fix": (
            "Add null checks before accessing user properties."
        )
    },

    {
        "id": 3,
        "title": "Memory Leak In Analytics Service",
        "severity": "critical",
        "service": "analytics-service",

        "description": (
            "Analytics service memory usage continuously increases."
        ),

        "metrics": {
            "memory_usage": "97%",
            "container_restarts": "12",
            "response_time": "4100ms"
        },

        "logs": [
            "Large objects retained in memory",
            "Garbage collection frequency increased",
            "Container killed due to OOM"
        ],

        "trace_summary": [
            "Analytics aggregation loop never released memory",
            "Large datasets persisted between requests"
        ],

        # Hidden evaluation fields
        "expected_root_cause": (
            "Objects retained globally causing memory leak."
        ),

        "expected_fix": (
            "Release unused objects and clear caches properly."
        )
    }

]