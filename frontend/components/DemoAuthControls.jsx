"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Bug,
  DatabaseZap,
  Gauge,
  Power,
  RefreshCw,
  RotateCcw,
  Send,
  TimerReset
} from "lucide-react";

import {
  getDemoServiceHealth,
  resetDemoService,
  sendDemoLoginTraffic,
  setDemoBugMode
} from "../lib/api";
import StatusBadge from "./StatusBadge";

function ControlButton({ children, icon: Icon, onClick, disabled, tone = "slate" }) {
  const toneClass = {
    red: "border-red-500/30 bg-red-500/10 text-red-100 hover:bg-red-500/20",
    emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100 hover:bg-emerald-500/20",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-100 hover:bg-amber-500/20",
    cyan: "border-cyan-500/30 bg-cyan-500/10 text-cyan-100 hover:bg-cyan-500/20",
    slate: "border-slate-700 bg-slate-900/80 text-slate-100 hover:border-violet-400"
  }[tone];

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${toneClass}`}
    >
      {Icon && <Icon size={16} />}
      {children}
    </button>
  );
}

export default function DemoAuthControls() {
  const [health, setHealth] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loadingAction, setLoadingAction] = useState("");

  async function refreshHealth() {
    try {
      setError("");
      const result = await getDemoServiceHealth();
      setHealth(result);
    } catch (err) {
      setError(err.message || "Demo service unavailable");
      setHealth(null);
    }
  }

  async function runAction(key, action) {
    try {
      setLoadingAction(key);
      setError("");
      setMessage("");

      const result = await action();
      setMessage(result.message || "Demo service updated");
      await refreshHealth();
    } catch (err) {
      setError(err.message || "Demo service action failed");
    } finally {
      setLoadingAction("");
    }
  }

  useEffect(() => {
    refreshHealth();
  }, []);

  const bugState = health?.bug_state || {};
  const busy = Boolean(loadingAction);

  return (
    <section className="mb-8 glass-card rounded-3xl p-6">
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
            <DatabaseZap size={14} />
            Real demo service
          </div>

          <h2 className="text-2xl font-bold text-white">
            Demo Auth Service Controls
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Toggle failure modes and generate traffic against the FastAPI auth service on port 8100.
          </p>
        </div>

        <ControlButton
          icon={RefreshCw}
          onClick={refreshHealth}
          disabled={busy}
        >
          Refresh Demo Health
        </ControlButton>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
          <p className="text-xs text-slate-500">Service Status</p>
          <div className="mt-3">
            <StatusBadge value={health?.status || "DOWN"} />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
          <p className="text-xs text-slate-500">Active DB Connections</p>
          <p className="mt-2 text-3xl font-black text-white">
            {health?.active_db_connections ?? "-"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
          <p className="text-xs text-slate-500">Bug State</p>
          <p className="mt-2 text-sm font-semibold text-slate-200">
            DB Leak: {bugState.db_leak ? "On" : "Off"} | Slow Login:{" "}
            {bugState.slow_login ? "On" : "Off"} | Random Errors:{" "}
            {bugState.random_errors ? "On" : "Off"}
          </p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <ControlButton
          icon={DatabaseZap}
          tone="red"
          disabled={busy}
          onClick={() => runAction("db-on", () => setDemoBugMode("dbLeak", true))}
        >
          Enable DB Leak
        </ControlButton>

        <ControlButton
          icon={RotateCcw}
          tone="emerald"
          disabled={busy}
          onClick={() => runAction("db-off", () => setDemoBugMode("dbLeak", false))}
        >
          Disable DB Leak / Reset
        </ControlButton>

        <ControlButton
          icon={Gauge}
          tone="amber"
          disabled={busy}
          onClick={() => runAction("slow-on", () => setDemoBugMode("slowLogin", true))}
        >
          Enable Slow Login
        </ControlButton>

        <ControlButton
          icon={TimerReset}
          tone="emerald"
          disabled={busy}
          onClick={() => runAction("slow-off", () => setDemoBugMode("slowLogin", false))}
        >
          Disable Slow Login
        </ControlButton>

        <ControlButton
          icon={Bug}
          tone="red"
          disabled={busy}
          onClick={() => runAction("errors-on", () => setDemoBugMode("randomErrors", true))}
        >
          Enable Random Errors
        </ControlButton>

        <ControlButton
          icon={Power}
          tone="emerald"
          disabled={busy}
          onClick={() => runAction("errors-off", () => setDemoBugMode("randomErrors", false))}
        >
          Disable Random Errors
        </ControlButton>

        <ControlButton
          icon={Send}
          tone="cyan"
          disabled={busy}
          onClick={() => runAction("traffic", () => sendDemoLoginTraffic(12))}
        >
          Send Login Traffic
        </ControlButton>

        <ControlButton
          icon={RotateCcw}
          disabled={busy}
          onClick={() => runAction("reset", resetDemoService)}
        >
          Reset All
        </ControlButton>
      </div>

      {loadingAction && (
        <div className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm text-slate-200">
          <RefreshCw className="animate-spin" size={16} />
          Running demo action...
        </div>
      )}

      {message && (
        <div className="mt-4 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
          {message}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} />
            {error}
          </div>
        </div>
      )}
    </section>
  );
}
