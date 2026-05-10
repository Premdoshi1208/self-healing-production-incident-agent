"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  ClipboardCheck,
  Code2,
  Copy,
  FileCode2,
  FileDiff,
  GitPullRequest,
  Lock,
  PackageCheck,
  SearchCode,
  ShieldCheck,
  TerminalSquare,
  TestTube2,
  X
} from "lucide-react";

import {
  approveRunForProduction,
  approveRunForStaging,
  preparePullRequestFromRun,
  rejectRun
} from "../lib/api";
import StatusBadge from "./StatusBadge";

function formatContent(content) {
  if (content === null || content === undefined || content === "") {
    return "No output available.";
  }

  if (typeof content === "string") {
    return content;
  }

  return JSON.stringify(content, null, 2);
}

function getRunId(run) {
  return run?.run_id || run?.stored_run?.run_id || "";
}

function getPatchText(run) {
  return (
    run?.real_patch?.unified_diff ||
    run?.patch_diff ||
    run?.unified_diff ||
    run?.diff ||
    run?.code_patch ||
    run?.real_patch?.patch_summary ||
    "No patch diff was saved for this run."
  );
}

function getCodeSearchResults(run) {
  const raw =
    run?.code_search?.suspected_files ||
    run?.codebase_search?.suspected_files ||
    run?.suspected_files ||
    [];

  return Array.isArray(raw) ? raw : [];
}

function getTests(run) {
  return (
    run?.test_result ||
    run?.playwright_test_result ||
    run?.tests ||
    null
  );
}

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(formatContent(value));
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs font-bold text-slate-200 transition hover:border-cyan-300/50 hover:text-white"
    >
      {copied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function TextPanel({ title, content, icon: Icon = FileCode2 }) {
  const displayContent = formatContent(content);

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-2.5 text-cyan-200">
            <Icon size={18} />
          </div>
          <h3 className="text-lg font-black text-white">{title}</h3>
        </div>

        <CopyButton value={displayContent} />
      </div>

      <pre className="code-block whitespace-pre-wrap">{displayContent}</pre>
    </section>
  );
}

function SummaryCard({ label, value, icon: Icon, tone = "cyan" }) {
  const tones = {
    cyan: "border-cyan-300/20 bg-cyan-300/10 text-cyan-200",
    violet: "border-violet-300/20 bg-violet-300/10 text-violet-200",
    emerald: "border-emerald-300/20 bg-emerald-300/10 text-emerald-200",
    amber: "border-amber-300/20 bg-amber-300/10 text-amber-200",
    red: "border-red-300/20 bg-red-300/10 text-red-200"
  };

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-950/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-black uppercase tracking-wide text-slate-500">
          {label}
        </p>
        {Icon && (
          <div className={`rounded-xl border p-2 ${tones[tone] || tones.cyan}`}>
            <Icon size={16} />
          </div>
        )}
      </div>
      <p className="mt-3 truncate text-2xl font-black text-white">{value}</p>
    </div>
  );
}

function OverviewPanel({ run }) {
  const evaluation = run?.evaluation || {};
  const deployGate = run?.deploy_gate || {};
  const tests = getTests(run);

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="RCA score"
          value={evaluation.root_cause_score ?? "-"}
          icon={BrainCircuit}
          tone="violet"
        />
        <SummaryCard
          label="Fix score"
          value={evaluation.fix_score ?? "-"}
          icon={ClipboardCheck}
          tone="cyan"
        />
        <SummaryCard
          label="Overall"
          value={evaluation.overall_score ?? "-"}
          icon={Activity}
          tone="emerald"
        />
        <SummaryCard
          label="Verdict"
          value={evaluation.verdict || run?.status || "-"}
          icon={ShieldCheck}
          tone={evaluation.verdict === "PASS" ? "emerald" : "amber"}
        />
        <SummaryCard
          label="Patch applied"
          value={run?.patch_apply_result?.applied || run?.patch_applied ? "Yes" : "No"}
          icon={PackageCheck}
          tone={run?.patch_apply_result?.applied || run?.patch_applied ? "emerald" : "amber"}
        />
        <SummaryCard
          label="Tests passed"
          value={tests?.passed || tests?.status === "passed" ? "Yes" : "No"}
          icon={TestTube2}
          tone={tests?.passed || tests?.status === "passed" ? "emerald" : "amber"}
        />
        <SummaryCard
          label="Staging"
          value={deployGate.staging_allowed ? "Allowed" : "Blocked"}
          icon={ShieldCheck}
          tone={deployGate.staging_allowed ? "emerald" : "red"}
        />
        <SummaryCard
          label="Human approval"
          value={deployGate.production_requires_human ? "Required" : "Not required"}
          icon={Lock}
          tone="violet"
        />
      </div>

      <TextPanel title="Run Error / Status" content={run?.error || run?.observability || "No workflow error recorded."} />
      <TextPanel title="Patch Artifact" content={run?.patch_file_path || "No patch artifact path available."} />
    </div>
  );
}

function MemoryPanel({ run }) {
  const memories = run?.retrieved_memories || [];

  return (
    <div className="space-y-5">
      {memories.length === 0 ? (
        <TextPanel title="Retrieved Memories" content="No similar memories were retrieved for this run." icon={BrainCircuit} />
      ) : (
        <div className="grid gap-4">
          {memories.map((memory, index) => (
            <article
              key={`${memory?.incident_title || "memory"}-${index}`}
              className="rounded-3xl border border-violet-300/15 bg-violet-300/10 p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-black text-white">
                    {memory?.incident_title || "Untitled memory"}
                  </h3>
                  <p className="mt-1 text-sm font-semibold text-violet-200">
                    {memory?.service || "unknown-service"}
                  </p>
                </div>
                <StatusBadge value={memory?.severity || "memory"} />
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                {memory?.learning_summary || "No learning summary available."}
              </p>
            </article>
          ))}
        </div>
      )}

      <TextPanel
        title="Saved Memory Entry"
        content={run?.memory_entry || (run?.memory_saved ? "Memory was saved." : "No memory entry was saved.")}
        icon={BrainCircuit}
      />
    </div>
  );
}

function CodeSearchPanel({ run }) {
  const results = getCodeSearchResults(run);

  if (results.length === 0) {
    return (
      <TextPanel
        title="Code Search"
        icon={SearchCode}
        content="No code search results were captured for this run. Older runs may only contain the generated patch text."
      />
    );
  }

  return (
    <div className="grid gap-4">
      {results.map((file, index) => (
        <article
          key={`${file?.file_path || file?.path || file?.file || "file"}-${index}`}
          className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5"
        >
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h3 className="font-mono text-base font-black text-cyan-100">
                {file?.file_path || file?.path || file?.file || "Unknown file"}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                {file?.short_reason || file?.reason || file?.rationale || "No reason captured."}
              </p>
            </div>
            <StatusBadge value={`score ${file?.relevance_score ?? file?.score ?? "-"}`} />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {(file?.matched_terms || file?.terms || []).map((term) => (
              <span
                key={term}
                className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-bold text-cyan-100"
              >
                {term}
              </span>
            ))}
          </div>

          {(file?.code_preview || file?.preview) && (
            <pre className="code-block mt-4 whitespace-pre-wrap">{file.code_preview || file.preview}</pre>
          )}
        </article>
      ))}
    </div>
  );
}

function TestsPanel({ run }) {
  const tests = getTests(run);

  if (!tests) {
    return (
      <TextPanel
        title="Tests"
        icon={TestTube2}
        content="No test result was attached to this run."
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Status" value={tests.status || "-"} icon={TestTube2} tone={tests.passed || tests.status === "passed" ? "emerald" : "red"} />
        <SummaryCard label="Exit code" value={tests.exit_code ?? "-"} icon={TerminalSquare} tone="cyan" />
        <SummaryCard label="Duration" value={tests.duration_seconds ?? tests.duration ?? tests.parsed_report?.stats?.duration ?? "-"} icon={Activity} tone="violet" />
        <SummaryCard label="Finished" value={tests.finished_at || "-"} icon={CheckCircle2} tone="emerald" />
      </div>

      <TextPanel title="Test Command" icon={TerminalSquare} content={tests.command || "No command captured."} />
      <TextPanel title="Stdout" icon={TerminalSquare} content={tests.stdout || tests.summary || "No stdout captured."} />
      <TextPanel title="Stderr" icon={TerminalSquare} content={tests.stderr || "No stderr captured."} />
    </div>
  );
}

function EvaluationPanel({ evaluation }) {
  if (!evaluation) {
    return <TextPanel title="Evaluation" content="No evaluation available." icon={ShieldCheck} />;
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="RCA score" value={evaluation.root_cause_score ?? "-"} icon={BrainCircuit} tone="violet" />
        <SummaryCard label="Fix score" value={evaluation.fix_score ?? "-"} icon={ClipboardCheck} tone="cyan" />
        <SummaryCard label="Overall" value={evaluation.overall_score ?? "-"} icon={Activity} tone="emerald" />
        <SummaryCard label="Verdict" value={evaluation.verdict || "-"} icon={ShieldCheck} tone={evaluation.verdict === "PASS" ? "emerald" : "red"} />
      </div>
      <TextPanel title="Evaluation Note" icon={ShieldCheck} content={evaluation.note || evaluation.reason || evaluation} />
    </div>
  );
}

function DeployGatePanel({ run, approval, onApprovalUpdated }) {
  const deployGate = run?.deploy_gate;
  const runId = getRunId(run);
  const [actionLoading, setActionLoading] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  if (!deployGate) {
    return <TextPanel title="Deploy Gate" content="No deploy gate decision available." icon={ShieldCheck} />;
  }

  async function handleApproval(action, approvalFn, comment) {
    try {
      setActionLoading(action);
      setMessage("");
      setError("");

      const result = await approvalFn(runId, comment);
      setMessage(result.message || "Approval updated.");
      onApprovalUpdated?.(result.approval);
    } catch (err) {
      setError(err.message || "Approval action failed");
    } finally {
      setActionLoading("");
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Staging allowed" value={deployGate.staging_allowed ? "Yes" : "No"} icon={ShieldCheck} tone={deployGate.staging_allowed ? "emerald" : "red"} />
        <SummaryCard label="Production allowed" value={deployGate.production_allowed ? "Yes" : "No"} icon={Lock} tone={deployGate.production_allowed ? "emerald" : "red"} />
        <SummaryCard label="Human required" value={deployGate.production_requires_human ? "Yes" : "No"} icon={Lock} tone="violet" />
        <SummaryCard label="Policy engine" value={deployGate.policy_engine || "-"} icon={ShieldCheck} tone="cyan" />
      </div>

      <section className="rounded-3xl border border-amber-300/20 bg-amber-300/10 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-black text-white">Human Approval Workflow</h3>
            <p className="mt-2 text-sm text-slate-300">
              Current approval status:{" "}
              <span className="font-black text-amber-100">
                {approval?.status || "pending"}
              </span>
            </p>
            {approval?.comment && (
              <p className="mt-2 text-sm text-slate-400">{approval.comment}</p>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleApproval("staging", approveRunForStaging, "Approved from dashboard deploy gate tab.")}
              disabled={!runId || Boolean(actionLoading)}
              className="command-button border-emerald-300/30 bg-emerald-400/10 text-emerald-100 hover:bg-emerald-400/20"
            >
              Approve Staging
            </button>
            <button
              onClick={() => handleApproval("reject", rejectRun, "Rejected from dashboard deploy gate tab.")}
              disabled={!runId || Boolean(actionLoading)}
              className="command-button border-red-300/30 bg-red-400/10 text-red-100 hover:bg-red-400/20"
            >
              Reject Patch
            </button>
            <button
              onClick={() => handleApproval("production", approveRunForProduction, "Explicit human production approval from dashboard.")}
              disabled={!runId || Boolean(actionLoading)}
              className="command-button border-amber-300/40 bg-amber-400/10 text-amber-100 hover:bg-amber-400/20"
            >
              Approve Production
            </button>
          </div>
        </div>

        <p className="mt-4 text-xs font-black uppercase tracking-wide text-amber-200">
          Production is never automatically allowed by the LLM.
        </p>

        {message && <p className="mt-4 rounded-2xl bg-emerald-400/10 p-3 text-sm font-semibold text-emerald-100">{message}</p>}
        {error && <p className="mt-4 rounded-2xl bg-red-400/10 p-3 text-sm font-semibold text-red-100">{error}</p>}
      </section>

      <TextPanel title="Decision Summary" icon={ShieldCheck} content={deployGate.decision_summary || "No deploy gate summary available."} />
      <TextPanel title="Blocking Reasons" icon={Lock} content={deployGate.blocking_reasons || []} />
      <TextPanel title="Raw Deploy Gate JSON" icon={FileCode2} content={deployGate} />
    </div>
  );
}

function PullRequestPanel({ run }) {
  const runId = getRunId(run);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(run?.github_pr || run?.pull_request || null);
  const [error, setError] = useState("");

  async function handlePreparePr() {
    try {
      setLoading(true);
      setError("");
      const response = await preparePullRequestFromRun(runId);
      setResult(response);
    } catch (err) {
      setError(err.message || "Failed to prepare pull request.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-slate-800 bg-slate-950/70 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h3 className="text-lg font-black text-white">GitHub Pull Request</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Prepare a PR handoff from this run. Without GitHub credentials, the backend returns a safe disabled message.
            </p>
          </div>

          <button
            onClick={handlePreparePr}
            disabled={!runId || loading}
            className="command-button border-violet-300/30 bg-violet-400/10 text-violet-100 hover:bg-violet-400/20"
          >
            <GitPullRequest size={17} />
            {loading ? "Preparing..." : "Prepare PR From Run"}
          </button>
        </div>

        {error && <p className="mt-4 rounded-2xl bg-red-400/10 p-3 text-sm font-semibold text-red-100">{error}</p>}
      </section>

      <TextPanel title="Pull Request Status" icon={GitPullRequest} content={result || "No PR action has been requested for this run."} />
    </div>
  );
}

export default function AgentTraceDrawer({ run, onClose, onRunUpdated }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [approval, setApproval] = useState(run?.approval);

  useEffect(() => {
    setApproval(run?.approval);
    setActiveTab("overview");
  }, [run]);

  const tabs = useMemo(
    () => [
      { id: "overview", label: "Overview", icon: Activity },
      { id: "memory", label: "Memory", icon: BrainCircuit },
      { id: "rca", label: "RCA", icon: BrainCircuit },
      { id: "fix", label: "Fix Plan", icon: ClipboardCheck },
      { id: "code", label: "Code Search", icon: SearchCode },
      { id: "patch", label: "Patch Diff", icon: FileDiff },
      { id: "tests", label: "Tests", icon: TestTube2 },
      { id: "qa", label: "QA", icon: ShieldCheck },
      { id: "evaluation", label: "Evaluation", icon: CheckCircle2 },
      { id: "deploy", label: "Deploy Gate", icon: Lock },
      { id: "pr", label: "Pull Request", icon: GitPullRequest }
    ],
    []
  );

  if (!run) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-xl">
      <div className="h-full w-full max-w-6xl overflow-y-auto border-l border-cyan-300/20 bg-[#030712] shadow-2xl">
        <div className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 px-5 py-5 backdrop-blur-xl lg:px-8">
          <div className="flex items-start justify-between gap-5">
            <div className="min-w-0">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <StatusBadge value={run?.evaluation?.verdict || run?.status || "unknown"} size="lg" />
                <StatusBadge value={run?.severity || "unknown"} />
                <span className="rounded-full border border-slate-700 bg-slate-900/80 px-3 py-1 text-xs font-bold text-slate-400">
                  {run?.created_at || run?.stored_run?.created_at || "Latest run"}
                </span>
              </div>

              <h2 className="truncate text-3xl font-black tracking-tight text-white lg:text-4xl">
                {run?.incident_title || "Untitled incident run"}
              </h2>
              <p className="mt-2 text-sm font-semibold text-slate-400">
                {run?.service || "unknown-service"} / run {getRunId(run) || "not stored"}
              </p>
            </div>

            <button
              onClick={onClose}
              className="rounded-2xl border border-slate-700 bg-slate-900/80 p-3 text-slate-300 transition hover:border-red-300/50 hover:bg-red-400/10 hover:text-white"
              aria-label="Close agent trace drawer"
            >
              <X size={20} />
            </button>
          </div>

          <div className="mt-5 flex gap-2 overflow-x-auto pb-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex shrink-0 items-center gap-2 rounded-2xl border px-4 py-2 text-sm font-bold transition ${
                    activeTab === tab.id
                      ? "border-cyan-300/40 bg-cyan-300/15 text-white shadow-cyanGlow"
                      : "border-slate-800 bg-slate-900/70 text-slate-400 hover:border-violet-300/40 hover:text-white"
                  }`}
                >
                  <Icon size={15} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-5 lg:p-8">
          {activeTab === "overview" && <OverviewPanel run={run} />}
          {activeTab === "memory" && <MemoryPanel run={run} />}
          {activeTab === "rca" && <TextPanel title="Root Cause Analysis" icon={BrainCircuit} content={run?.rca_analysis} />}
          {activeTab === "fix" && <TextPanel title="Fix Plan" icon={ClipboardCheck} content={run?.fix_plan} />}
          {activeTab === "code" && <CodeSearchPanel run={run} />}
          {activeTab === "patch" && (
            <div className="space-y-5">
              <TextPanel title="Patch File Path" icon={FileCode2} content={run?.patch_file_path || "No patch file path available."} />
              <TextPanel title="Unified Diff / Patch Output" icon={FileDiff} content={getPatchText(run)} />
            </div>
          )}
          {activeTab === "tests" && <TestsPanel run={run} />}
          {activeTab === "qa" && <TextPanel title="QA Validation" icon={ShieldCheck} content={run?.qa_validation} />}
          {activeTab === "evaluation" && <EvaluationPanel evaluation={run?.evaluation} />}
          {activeTab === "deploy" && (
            <DeployGatePanel
              run={run}
              approval={approval}
              onApprovalUpdated={(updatedApproval) => {
                setApproval(updatedApproval);
                onRunUpdated?.({ ...run, approval: updatedApproval });
              }}
            />
          )}
          {activeTab === "pr" && <PullRequestPanel run={run} />}
        </div>
      </div>
    </div>
  );
}
