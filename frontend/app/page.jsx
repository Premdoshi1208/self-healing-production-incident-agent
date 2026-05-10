"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  ClipboardCheck,
  Code2,
  DatabaseZap,
  ExternalLink,
  FileDiff,
  GitPullRequest,
  Lock,
  Play,
  RadioTower,
  RefreshCw,
  Search,
  SearchCode,
  Server,
  ShieldCheck,
  Sparkles,
  TestTube2,
  Zap
} from "lucide-react";

import {
  getCodebaseStatus,
  getIncidents,
  getLatestPlaywrightQA,
  getPatches,
  getRecentMemories,
  getRecentRuns,
  getRunsSummary,
  getServiceStatus,
  runIncidentWorkflow,
  runPlaywrightQA
} from "../lib/api";

import AgentTraceDrawer from "../components/AgentTraceDrawer";
import DemoAuthControls from "../components/DemoAuthControls";
import MemoryCard from "../components/MemoryCard";
import MetricCard from "../components/MetricCard";
import PrometheusSimulator from "../components/PrometheusSimulator";
import RunCard from "../components/RunCard";
import StatusBadge from "../components/StatusBadge";
import TimelineStep from "../components/TimelineStep";

const QUICK_LINKS = [
  ["Backend docs", "http://127.0.0.1:8000/docs"],
  ["Demo service docs", "http://127.0.0.1:8100/docs"],
  ["Prometheus", "http://127.0.0.1:9090"],
  ["Alertmanager", "http://127.0.0.1:9093"],
  ["Grafana", "http://127.0.0.1:3001"]
];

const REQUIRED_SERVICES = [
  { key: "backend", name: "AI Backend", url: "http://127.0.0.1:8000/health" },
  { key: "demo_service", name: "Demo Auth Service", url: "http://127.0.0.1:8100/health" },
  { key: "prometheus", name: "Prometheus", url: "http://127.0.0.1:9090" },
  { key: "alertmanager", name: "Alertmanager", url: "http://127.0.0.1:9093" },
  { key: "grafana", name: "Grafana", url: "http://127.0.0.1:3001" }
];

const PIPELINE_STEPS = [
  ["Memory Retrieval", "Pulls relevant Reflexion memories before reasoning starts.", BrainCircuit],
  ["RCA Agent", "Uses logs, metrics, and traces to explain the likely root cause.", Activity],
  ["Fix Planner", "Builds a remediation plan, rollback path, and required validation.", ClipboardCheck],
  ["Codebase Search", "Identifies suspected files and evidence when code search data is available.", SearchCode],
  ["Patch Diff", "Produces a reviewable patch artifact instead of applying changes directly.", FileDiff],
  ["Tests", "Captures Playwright or saved QA test output for deploy decisions.", TestTube2],
  ["QA Validation", "Reviews regression risk and deployment readiness.", ShieldCheck],
  ["Evaluation", "Scores agent output with deterministic evaluation metadata.", CheckCircle2],
  ["Deploy Gate", "Blocks unsafe releases with policy, not LLM confidence.", Lock],
  ["Reflexion Memory", "Stores learnings for the next similar incident.", BrainCircuit]
];

function safeValue(value, fallback = "-") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

function SectionHeader({ eyebrow, title, subtitle, icon: Icon }) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        {eyebrow && (
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-cyan-100">
            {Icon && <Icon size={14} />}
            {eyebrow}
          </div>
        )}
        <h2 className="text-2xl font-black tracking-tight text-white">{title}</h2>
        {subtitle && <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{subtitle}</p>}
      </div>
    </div>
  );
}

function ServiceStatusCard({ service }) {
  const status = service?.status || "unknown";
  const isUp = status === "up" || status === "healthy";

  return (
    <article className="glass-card rounded-3xl p-5 transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/30">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-base font-black text-white">{service.name}</p>
          <p className="mt-1 truncate text-xs font-semibold text-slate-500">
            {service.url || service.link || "local service"}
          </p>
        </div>

        <div className={`rounded-2xl border p-3 ${isUp ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-200" : "border-amber-300/20 bg-amber-300/10 text-amber-200"}`}>
          <Server size={20} />
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between gap-3">
        <StatusBadge value={isUp ? "healthy" : status} />
        <span className="text-xs font-bold text-slate-500">
          HTTP {service?.http_status || "-"}
        </span>
      </div>
    </article>
  );
}

function SignalCard({ label, value, icon: Icon, tone = "cyan" }) {
  const tones = {
    cyan: "border-cyan-300/20 bg-cyan-300/10 text-cyan-200",
    violet: "border-violet-300/20 bg-violet-300/10 text-violet-200",
    emerald: "border-emerald-300/20 bg-emerald-300/10 text-emerald-200",
    amber: "border-amber-300/20 bg-amber-300/10 text-amber-200"
  };

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950/60 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
          {label}
        </p>
        {Icon && <div className={`rounded-xl border p-2 ${tones[tone] || tones.cyan}`}><Icon size={15} /></div>}
      </div>
      <p className="mt-3 truncate text-lg font-black text-white">{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const [incidents, setIncidents] = useState([]);
  const [runs, setRuns] = useState([]);
  const [summary, setSummary] = useState(null);
  const [memories, setMemories] = useState([]);
  const [serviceStatus, setServiceStatus] = useState(null);
  const [latestTestResult, setLatestTestResult] = useState(null);
  const [codebaseStatus, setCodebaseStatus] = useState(null);
  const [patches, setPatches] = useState(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState(1);
  const [latestResult, setLatestResult] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [runFilter, setRunFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [qaLoading, setQaLoading] = useState(false);
  const [booting, setBooting] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  async function loadDashboardData() {
    setError("");

    const results = await Promise.allSettled([
      getIncidents(),
      getRecentRuns(),
      getRunsSummary(),
      getRecentMemories(),
      getServiceStatus(),
      getLatestPlaywrightQA(),
      getCodebaseStatus(),
      getPatches()
    ]);

    const [
      incidentResult,
      runResult,
      summaryResult,
      memoryResult,
      serviceResult,
      testResult,
      codebaseResult,
      patchResult
    ] = results;

    if (incidentResult.status === "fulfilled") {
      setIncidents(incidentResult.value.incidents || []);
    }

    if (runResult.status === "fulfilled") {
      setRuns((runResult.value.runs || []).slice().reverse());
    }

    if (summaryResult.status === "fulfilled") {
      setSummary(summaryResult.value);
    }

    if (memoryResult.status === "fulfilled") {
      setMemories((memoryResult.value.memories || []).slice().reverse());
    }

    if (serviceResult.status === "fulfilled") {
      setServiceStatus(serviceResult.value);
    }

    if (testResult.status === "fulfilled") {
      setLatestTestResult(testResult.value.test_result || null);
    }

    if (codebaseResult.status === "fulfilled") {
      setCodebaseStatus(codebaseResult.value);
    }

    if (patchResult.status === "fulfilled") {
      setPatches(patchResult.value);
    }

    const failedRequired = [incidentResult, runResult, summaryResult, memoryResult]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "Request failed");

    if (failedRequired.length > 0) {
      setError(failedRequired.join(" | "));
    }

    setLastUpdated(new Date().toLocaleString());
    setBooting(false);
  }

  async function handleRunIncident() {
    try {
      setLoading(true);
      setError("");
      setLatestResult(null);

      const result = await runIncidentWorkflow(selectedIncidentId);
      setLatestResult(result);
      setSelectedRun(result);
      await loadDashboardData();
    } catch (err) {
      setError(err.message || "Workflow failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleWebhookWorkflowComplete(result) {
    setLatestResult(result);
    setSelectedRun(result);
    await loadDashboardData();
  }

  async function handleRunPlaywrightQA() {
    try {
      setQaLoading(true);
      setError("");
      const result = await runPlaywrightQA();
      setLatestTestResult(result.test_result);
      await loadDashboardData();
    } catch (err) {
      setError(err.message || "Playwright QA failed");
    } finally {
      setQaLoading(false);
    }
  }

  useEffect(() => {
    loadDashboardData();
  }, []);

  const selectedIncident = incidents.find(
    (incident) => Number(incident.id) === Number(selectedIncidentId)
  ) || incidents[0];

  const services = useMemo(() => {
    const reported = serviceStatus?.services || [];
    return REQUIRED_SERVICES.map((required) => {
      const match = reported.find((item) => item.key === required.key);
      return match ? { ...required, ...match, name: required.name } : { ...required, status: "unknown" };
    });
  }, [serviceStatus]);

  const filteredRuns = useMemo(() => {
    const query = runFilter.trim().toLowerCase();

    if (!query) {
      return runs;
    }

    return runs.filter((run) =>
      [
        run?.incident_title,
        run?.service,
        run?.severity,
        run?.status,
        run?.evaluation?.verdict,
        run?.deploy_gate?.decision_summary,
        run?.patch_file_path
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    );
  }, [runs, runFilter]);

  const deployGateDecisions = runs.filter((run) => run?.deploy_gate).length;
  const patchCount = patches?.patches?.length ?? runs.filter((run) => run?.patch_file_path).length;

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.05)_1px,transparent_1px)] bg-[size:48px_48px]" />

      <div className="relative mx-auto max-w-[1500px]">
        <header className="mb-8 glass-card-strong rounded-3xl p-6 lg:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
            <div className="max-w-4xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-300/25 bg-violet-300/10 px-4 py-2 text-sm font-black uppercase tracking-wide text-violet-100">
                <Sparkles size={16} />
                Autonomous AI SRE Command Center
              </div>

              <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl">
                Self-Healing <span className="gradient-text">Incident Agent</span>
              </h1>

              <p className="mt-5 max-w-3xl text-base leading-8 text-slate-300 lg:text-lg">
                A production-style incident workflow that ingests alerts, retrieves memory,
                performs RCA, plans fixes, saves patches, validates safety, gates deployment,
                and exposes every decision through metrics and trace history.
              </p>
            </div>

            <div className="flex flex-col gap-3 xl:items-end">
              <button
                onClick={loadDashboardData}
                disabled={booting}
                className="command-button border-cyan-300/30 bg-cyan-300/10 text-cyan-100 shadow-cyanGlow hover:bg-cyan-300/20"
              >
                <RefreshCw className={booting ? "animate-spin" : ""} size={18} />
                Refresh Dashboard
              </button>
              <p className="text-xs font-semibold text-slate-500">
                Last updated: {lastUpdated || "not loaded"}
              </p>
              <div className="flex flex-wrap gap-2 xl:justify-end">
                {QUICK_LINKS.map(([label, href]) => (
                  <a
                    key={href}
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1.5 text-xs font-bold text-slate-300 transition hover:border-cyan-300/40 hover:text-white"
                  >
                    <ExternalLink size={13} />
                    {label}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </header>

        {error && (
          <section className="mb-8 rounded-3xl border border-red-300/25 bg-red-400/10 p-5 text-sm font-semibold text-red-100">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 shrink-0" size={18} />
              <span>{error}</span>
            </div>
          </section>
        )}

        <section className="mb-8">
          <SectionHeader
            eyebrow="live topology"
            title="Service Status"
            subtitle="One glance across the AI backend, demo service, and monitoring plane."
            icon={Server}
          />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {services.map((service) => (
              <ServiceStatusCard key={service.key} service={service} />
            ))}
          </div>
        </section>

        <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <MetricCard title="Total Runs" value={summary?.total_runs ?? runs.length} subtitle="Saved workflow executions" icon={Activity} tone="cyan" />
          <MetricCard title="Pass Count" value={summary?.pass_count ?? 0} subtitle="Evaluated successful runs" icon={CheckCircle2} tone="emerald" />
          <MetricCard title="Average Score" value={summary?.average_score ?? 0} subtitle="Across evaluated incidents" icon={ShieldCheck} tone="violet" />
          <MetricCard title="Memory Entries" value={memories.length} subtitle="Recent Reflexion learnings" icon={BrainCircuit} tone="amber" />
          <MetricCard title="Deploy Gates" value={deployGateDecisions} subtitle="Recent gate decisions loaded" icon={Lock} tone="red" />
        </section>

        <section className="mb-8 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="glass-card rounded-3xl p-6">
            <SectionHeader
              eyebrow="manual incident"
              title="Run Incident Workflow"
              subtitle="Trigger the full AI SRE workflow from a known incident profile."
              icon={Zap}
            />

            <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
              <select
                value={selectedIncident?.id || selectedIncidentId}
                onChange={(event) => setSelectedIncidentId(Number(event.target.value))}
                className="field-shell"
              >
                {incidents.map((incident) => (
                  <option key={incident.id} value={incident.id}>
                    #{incident.id} - {incident.title}
                  </option>
                ))}
              </select>

              <button
                onClick={handleRunIncident}
                disabled={loading || booting || !selectedIncident}
                className="command-button border-violet-300/30 bg-violet-500 text-white shadow-glow hover:bg-violet-400"
              >
                {loading ? (
                  <>
                    <RefreshCw className="animate-spin" size={18} />
                    Running Workflow
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    Run Workflow
                  </>
                )}
              </button>
            </div>

            {selectedIncident && (
              <div className="mt-5 rounded-3xl border border-slate-800 bg-slate-950/70 p-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h3 className="text-xl font-black text-white">{selectedIncident.title}</h3>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                      {selectedIncident.description}
                    </p>
                  </div>
                  <StatusBadge value={selectedIncident.severity} size="lg" />
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {Object.entries(selectedIncident.metrics || {}).map(([key, value]) => (
                    <SignalCard
                      key={key}
                      label={key.replaceAll("_", " ")}
                      value={value}
                      icon={Activity}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="glass-card rounded-3xl p-6">
            <SectionHeader
              eyebrow="agent path"
              title="Agent Pipeline"
              subtitle="The workflow is explicit, inspectable, and deployment-safe."
              icon={ShieldCheck}
            />
            <div className="grid gap-3 sm:grid-cols-2">
              {PIPELINE_STEPS.map(([title, description, Icon], index) => (
                <TimelineStep
                  key={title}
                  title={title}
                  description={description}
                  icon={Icon}
                  index={index + 1}
                />
              ))}
            </div>
          </div>
        </section>

        <DemoAuthControls />

        <section className="mb-8 grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <PrometheusSimulator onWorkflowComplete={handleWebhookWorkflowComplete} />

          <div className="glass-card rounded-3xl p-6">
            <SectionHeader
              eyebrow="quality and artifacts"
              title="Patch, Test, and Codebase Signals"
              subtitle="Optional engineering artifacts are surfaced without making the UI brittle."
              icon={Code2}
            />

            <div className="grid gap-4 md:grid-cols-2">
              <SignalCard
                label="Latest tests"
                value={latestTestResult?.status || "not run"}
                icon={TestTube2}
                tone={latestTestResult?.status === "passed" ? "emerald" : "amber"}
              />
              <SignalCard
                label="Patch artifacts"
                value={patchCount}
                icon={FileDiff}
                tone="violet"
              />
              <SignalCard
                label="Codebase search"
                value={codebaseStatus?.enabled === false ? "not configured" : safeValue(codebaseStatus?.status, "ready")}
                icon={SearchCode}
                tone="cyan"
              />
              <SignalCard
                label="Pull request"
                value="human gated"
                icon={GitPullRequest}
                tone="emerald"
              />
            </div>

            <button
              onClick={handleRunPlaywrightQA}
              disabled={qaLoading}
              className="command-button mt-5 border-emerald-300/30 bg-emerald-400/10 text-emerald-100 hover:bg-emerald-400/20"
            >
              {qaLoading ? <RefreshCw className="animate-spin" size={17} /> : <TestTube2 size={17} />}
              {qaLoading ? "Running Playwright" : "Run Playwright QA"}
            </button>
          </div>
        </section>

        {latestResult && (
          <section className="mb-8 glass-card-strong rounded-3xl p-6">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-emerald-100">
                  <CheckCircle2 size={14} />
                  Latest result
                </div>
                <h2 className="text-2xl font-black text-white">
                  {latestResult.incident_title || "Workflow completed"}
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {latestResult.deploy_gate?.decision_summary || latestResult.error?.message || "Run saved to workflow history."}
                </p>
              </div>

              <button
                onClick={() => setSelectedRun(latestResult)}
                className="command-button border-cyan-300/30 bg-cyan-300/10 text-cyan-100 hover:bg-cyan-300/20"
              >
                Open Full Agent Trace
              </button>
            </div>
          </section>
        )}

        <section className="grid gap-6 xl:grid-cols-[1.18fr_0.82fr]">
          <div className="glass-card rounded-3xl p-6">
            <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-black uppercase tracking-wide text-amber-100">
                  <RadioTower size={14} />
                  auditable runs
                </div>
                <h2 className="text-2xl font-black text-white">Recent Workflow Runs</h2>
                <p className="mt-2 text-sm text-slate-400">
                  Click any run to inspect the agent trace, patch, tests, and deploy gate.
                </p>
              </div>

              <label className="relative block w-full lg:max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
                <input
                  value={runFilter}
                  onChange={(event) => setRunFilter(event.target.value)}
                  placeholder="Search runs, services, verdicts"
                  className="field-shell w-full pl-10"
                />
              </label>
            </div>

            <div className="grid gap-4">
              {filteredRuns.length === 0 ? (
                <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-6 text-sm text-slate-400">
                  {runs.length === 0
                    ? "No workflow runs yet. Trigger an incident workflow, send a simulator alert, or use the real demo service loop."
                    : "No workflow runs match the current filter."}
                </div>
              ) : (
                filteredRuns.map((run) => (
                  <RunCard
                    key={run.run_id || `${run.incident_id}-${run.created_at}`}
                    run={run}
                    onClick={() => setSelectedRun(run)}
                  />
                ))
              )}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6">
            <SectionHeader
              eyebrow="memory"
              title="Reflexion Memory"
              subtitle="Reusable learnings from prior incidents."
              icon={BrainCircuit}
            />

            <div className="grid gap-4">
              {memories.length === 0 ? (
                <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-6 text-sm text-slate-400">
                  No memories saved yet.
                </div>
              ) : (
                memories.map((memory, index) => (
                  <MemoryCard
                    key={`${memory?.timestamp || "memory"}-${index}`}
                    memory={memory}
                  />
                ))
              )}
            </div>
          </div>
        </section>
      </div>

      <AgentTraceDrawer
        run={selectedRun}
        onClose={() => setSelectedRun(null)}
        onRunUpdated={(updatedRun) => {
          setSelectedRun(updatedRun);
          loadDashboardData();
        }}
      />
    </main>
  );
}
