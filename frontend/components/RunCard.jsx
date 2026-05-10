import {
  ArrowUpRight,
  Code2,
  FileCheck2,
  Rocket,
  Server,
  ShieldCheck
} from "lucide-react";

import StatusBadge from "./StatusBadge";

function MiniMetric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
      <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-1 truncate text-lg font-black text-white">{value}</p>
    </div>
  );
}

export default function RunCard({ run, onClick }) {
  const evaluation = run?.evaluation || {};
  const deployGate = run?.deploy_gate || {};
  const testStatus = run?.test_result?.status || run?.playwright_test_result?.status || "not run";
  const patchStatus = run?.patch_apply_result?.applied
    ? "applied"
    : run?.patch_file_path
      ? "saved"
      : "missing";

  return (
    <button
      onClick={onClick}
      className="group w-full rounded-3xl border border-slate-800/90 bg-slate-950/70 p-5 text-left shadow-lg shadow-black/20 transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/40 hover:bg-slate-900/80 hover:shadow-cyanGlow"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <StatusBadge value={evaluation.verdict || run?.status || "unknown"} />
            <StatusBadge value={run?.severity || "unknown"} />
          </div>

          <h3 className="truncate text-xl font-black text-white">
            {run?.incident_title || "Unknown Incident"}
          </h3>

          <p className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-400">
            <Server size={15} />
            {run?.service || "unknown-service"}
          </p>
        </div>

        <div className="inline-flex items-center gap-2 text-sm font-bold text-cyan-200">
          Open trace
          <ArrowUpRight
            className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
            size={17}
          />
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MiniMetric label="RCA" value={evaluation.root_cause_score ?? "-"} />
        <MiniMetric label="Fix" value={evaluation.fix_score ?? "-"} />
        <MiniMetric label="Overall" value={evaluation.overall_score ?? "-"} />
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            <Rocket size={13} />
            Deploy gate
          </p>
          <p className="mt-1 text-sm font-bold text-white">
            {deployGate.staging_allowed ? "Staging allowed" : "Staging blocked"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            <ShieldCheck size={13} />
            Human gate
          </p>
          <p className="mt-1 text-sm font-bold text-white">
            {deployGate.production_requires_human ? "Required" : "Not required"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            <Code2 size={13} />
            Patch
          </p>
          <p className="mt-1 text-sm font-bold text-white">{patchStatus}</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-500">
            <FileCheck2 size={13} />
            Tests
          </p>
          <p className="mt-1 text-sm font-bold text-white">{testStatus}</p>
        </div>
      </div>

      <p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-400">
        {run?.rca_analysis || run?.error?.message || "No RCA output available yet."}
      </p>
    </button>
  );
}
