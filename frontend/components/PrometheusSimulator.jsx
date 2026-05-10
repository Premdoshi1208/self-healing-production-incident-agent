"use client";

import { useState } from "react";
import {
  RadioTower,
  Send,
  RefreshCw,
  AlertTriangle,
  ServerCrash,
  Activity
} from "lucide-react";

import { sendPrometheusAlert } from "../lib/api";
import StatusBadge from "./StatusBadge";

const ALERT_TEMPLATES = [
  {
    id: "db-leak",
    name: "Database Connection Pool Exhausted",
    severity: "critical",
    service: "auth-service",
    icon: ServerCrash,
    buildPayload: () => ({
      receiver: "ai-sre-agent",
      status: "firing",
      alerts: [
        {
          status: "firing",
          labels: {
            alertname: "DatabaseConnectionPoolExhausted",
            severity: "critical",
            service: "auth-service",
            job: "auth-service",
            instance: "auth-service-pod-7d9c"
          },
          annotations: {
            summary: "Database Connection Leak",
            description:
              "Login latency increased dramatically. Database connection pool is exhausted and users are experiencing login delays.",
            metric_snapshot: {
              cpu_usage: "92%",
              memory_usage: "88%",
              p95_latency: "3200ms",
              error_rate: "18%"
            },
            logs: [
              "Database connection pool exhausted",
              "Timeout while querying users table",
              "Too many active database sessions"
            ],
            trace_summary: [
              "POST /login → db.query()",
              "Database session remained active",
              "Repeated connection retries detected"
            ]
          },
          startsAt: new Date().toISOString()
        }
      ]
    })
  },
  {
    id: "frontend-crash",
    name: "Frontend Dashboard Crash",
    severity: "high",
    service: "dashboard-frontend",
    icon: AlertTriangle,
    buildPayload: () => ({
      receiver: "ai-sre-agent",
      status: "firing",
      alerts: [
        {
          status: "firing",
          labels: {
            alertname: "FrontendDashboardCrash",
            severity: "high",
            service: "dashboard-frontend",
            job: "frontend",
            instance: "frontend-edge-2"
          },
          annotations: {
            summary: "Frontend Dashboard Crash",
            description:
              "Dashboard crashes while loading user profile data. Frontend error rate increased sharply.",
            metric_snapshot: {
              frontend_errors: "146",
              crash_rate: "37%",
              page_load_time: "5400ms"
            },
            logs: [
              "TypeError: Cannot read property 'name' of undefined",
              "React component crashed during render"
            ],
            trace_summary: [
              "GET /profile executed successfully",
              "Frontend rendering failed",
              "Null object passed into component"
            ]
          },
          startsAt: new Date().toISOString()
        }
      ]
    })
  },
  {
    id: "memory-leak",
    name: "Analytics Memory Leak",
    severity: "critical",
    service: "analytics-service",
    icon: Activity,
    buildPayload: () => ({
      receiver: "ai-sre-agent",
      status: "firing",
      alerts: [
        {
          status: "firing",
          labels: {
            alertname: "AnalyticsMemoryLeak",
            severity: "critical",
            service: "analytics-service",
            job: "analytics-service",
            instance: "analytics-worker-4"
          },
          annotations: {
            summary: "Memory Leak In Analytics Service",
            description:
              "Analytics service memory usage continuously increases and containers are restarting due to OOM.",
            metric_snapshot: {
              memory_usage: "97%",
              container_restarts: "12",
              response_time: "4100ms"
            },
            logs: [
              "Large objects retained in memory",
              "Garbage collection frequency increased",
              "Container killed due to OOM"
            ],
            trace_summary: [
              "Analytics aggregation loop never released memory",
              "Large datasets persisted between requests"
            ]
          },
          startsAt: new Date().toISOString()
        }
      ]
    })
  }
];

export default function PrometheusSimulator({ onWorkflowComplete }) {
  const [selectedAlertId, setSelectedAlertId] = useState("db-leak");
  const [loading, setLoading] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");

  const selectedAlert = ALERT_TEMPLATES.find(
    (alert) => alert.id === selectedAlertId
  );

  async function handleSendAlert() {
    try {
      setLoading(true);
      setResponseMessage("");

      const payload = selectedAlert.buildPayload();
      const response = await sendPrometheusAlert(payload);

      const workflowResult = response.workflow_results?.[0];

      setResponseMessage(
        `${response.alerts_received} alert processed through Prometheus webhook`
      );

      if (workflowResult && onWorkflowComplete) {
        await onWorkflowComplete(workflowResult);
      }
    } catch (error) {
      setResponseMessage(error.message || "Failed to send alert");
    } finally {
      setLoading(false);
    }
  }

  const Icon = selectedAlert?.icon || RadioTower;

  return (
    <div className="glass-card rounded-3xl p-6 shadow-glow">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
            <RadioTower size={14} />
            Real-style monitoring ingestion
          </div>

          <h2 className="text-2xl font-bold text-white">
            Prometheus Alert Simulator
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Send a monitoring-style alert into the webhook and trigger the full AI incident workflow.
          </p>
        </div>

        <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-300">
          <Icon size={23} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-[1fr_auto]">
        <select
          value={selectedAlertId}
          onChange={(event) => setSelectedAlertId(event.target.value)}
          className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400"
        >
          {ALERT_TEMPLATES.map((alert) => (
            <option key={alert.id} value={alert.id}>
              {alert.name}
            </option>
          ))}
        </select>

        <button
          onClick={handleSendAlert}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-600 px-6 py-3 font-bold text-white shadow-glow transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="animate-spin" size={18} />
              Sending Alert...
            </>
          ) : (
            <>
              <Send size={18} />
              Send Alert
            </>
          )}
        </button>
      </div>

      {selectedAlert && (
        <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-bold text-white">{selectedAlert.name}</h3>
              <p className="mt-1 text-sm text-slate-400">
                Service: {selectedAlert.service}
              </p>
            </div>

            <StatusBadge value={selectedAlert.severity} />
          </div>

          <div className="mt-4 rounded-xl bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Webhook endpoint
            </p>
            <p className="mt-1 font-mono text-sm text-cyan-200">
              POST /api/prometheus/webhook
            </p>
          </div>
        </div>
      )}

      {responseMessage && (
        <div className="mt-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/10 p-4 text-sm text-cyan-100">
          {responseMessage}
        </div>
      )}
    </div>
  );
}