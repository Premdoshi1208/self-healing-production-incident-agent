const API_BASE_URL = "http://127.0.0.1:8000/api";
const DEMO_SERVICE_BASE_URL = "http://127.0.0.1:8100";

async function parseResponse(response, fallbackMessage) {
  if (response.ok) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      return response.json();
    }

    return { message: await response.text() };
  }

  let detail = fallbackMessage;

  try {
    const data = await response.json();
    detail = data?.message || data?.detail || data?.error?.message || detail;
  } catch (error) {
    detail = response.statusText || detail;
  }

  throw new Error(detail);
}

async function optionalJson(url, fallback) {
  try {
    const response = await fetch(url, { cache: "no-store" });
    return parseResponse(response, "Optional endpoint unavailable");
  } catch (error) {
    return fallback;
  }
}

export async function getIncidents() {
  const response = await fetch(`${API_BASE_URL}/incidents`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch incidents");
}

export async function runIncidentWorkflow(incidentId) {
  const response = await fetch(`${API_BASE_URL}/incidents/run/${incidentId}`, {
    method: "POST"
  });

  return parseResponse(response, "Failed to run incident workflow");
}

export async function sendPrometheusAlert(payload) {
  const response = await fetch(`${API_BASE_URL}/prometheus/webhook`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse(response, "Failed to send Prometheus alert");
}

export async function getRecentRuns() {
  const response = await fetch(`${API_BASE_URL}/runs/recent`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch recent runs");
}

export async function getRunsSummary() {
  const response = await fetch(`${API_BASE_URL}/runs/summary`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch run summary");
}

export async function getRecentMemories() {
  const response = await fetch(`${API_BASE_URL}/memory/recent`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch memories");
}

export async function getServiceStatus() {
  const response = await fetch(`${API_BASE_URL}/services/status`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch service status");
}

export async function getCodebaseStatus() {
  return optionalJson(`${API_BASE_URL}/codebase/status`, {
    enabled: false,
    message: "Codebase search endpoint is not available yet.",
    suspected_files: []
  });
}

export async function getPatches() {
  return optionalJson(`${API_BASE_URL}/patches`, {
    enabled: false,
    message: "Patch listing endpoint is not available yet.",
    patches: []
  });
}

export async function preparePullRequestFromRun(runId) {
  const response = await fetch(`${API_BASE_URL}/github/pr/from-run/${runId}`, {
    method: "POST"
  });

  return parseResponse(response, "Failed to prepare GitHub PR");
}

export async function runPlaywrightQA() {
  const response = await fetch(`${API_BASE_URL}/qa/run-playwright`, {
    method: "POST"
  });

  return parseResponse(response, "Failed to run Playwright QA");
}

export async function getLatestPlaywrightQA() {
  const response = await fetch(`${API_BASE_URL}/qa/test-runs/latest`, {
    cache: "no-store"
  });

  return parseResponse(response, "Failed to fetch Playwright QA result");
}

export async function approveRunForStaging(runId, comment = "") {
  const response = await fetch(`${API_BASE_URL}/approvals/${runId}/approve-staging`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ reviewer: "frontend-operator", comment })
  });

  return parseResponse(response, "Failed to approve staging");
}

export async function rejectRun(runId, comment = "") {
  const response = await fetch(`${API_BASE_URL}/approvals/${runId}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ reviewer: "frontend-operator", comment })
  });

  return parseResponse(response, "Failed to reject patch");
}

export async function approveRunForProduction(runId, comment = "") {
  const response = await fetch(`${API_BASE_URL}/approvals/${runId}/approve-production`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ reviewer: "frontend-operator", comment })
  });

  return parseResponse(response, "Failed to approve production");
}

export async function getDemoServiceHealth() {
  const response = await fetch(`${DEMO_SERVICE_BASE_URL}/health`, {
    cache: "no-store"
  });

  return parseResponse(response, "Demo service unavailable");
}

export async function setDemoBugMode(mode, enabled) {
  const endpointMap = {
    dbLeak: `/simulate/db-leak/${enabled ? "on" : "off"}`,
    slowLogin: `/simulate/slow-login/${enabled ? "on" : "off"}`,
    randomErrors: `/simulate/random-errors/${enabled ? "on" : "off"}`
  };

  const response = await fetch(`${DEMO_SERVICE_BASE_URL}${endpointMap[mode]}`, {
    method: "POST"
  });

  return parseResponse(response, "Failed to update demo service mode");
}

export async function resetDemoService() {
  const response = await fetch(`${DEMO_SERVICE_BASE_URL}/simulate/reset`, {
    method: "POST"
  });

  return parseResponse(response, "Failed to reset demo service");
}

export async function sendDemoLoginTraffic(count = 12) {
  const results = [];

  for (let index = 0; index < count; index += 1) {
    try {
      const response = await fetch(`${DEMO_SERVICE_BASE_URL}/login`, {
        method: "POST"
      });
      const data = await parseResponse(response, "Login request failed");
      results.push({ ok: true, data });
    } catch (error) {
      results.push({ ok: false, error: error.message });
    }
  }

  const successes = results.filter((result) => result.ok).length;
  const failures = results.length - successes;
  const health = await getDemoServiceHealth();

  return {
    message: `Sent ${count} login requests`,
    successes,
    failures,
    active_db_connections: health.active_db_connections,
    bug_state: health.bug_state,
    results
  };
}
