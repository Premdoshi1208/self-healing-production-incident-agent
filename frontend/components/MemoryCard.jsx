import { BrainCircuit, Database, Server } from "lucide-react";

import StatusBadge from "./StatusBadge";

export default function MemoryCard({ memory }) {
  const title = memory?.incident_title || "Untitled incident memory";
  const service = memory?.service || "unknown-service";
  const severity = memory?.severity || "learned";
  const summary = memory?.learning_summary || "No learning summary was saved.";

  return (
    <article className="rounded-3xl border border-violet-300/10 bg-slate-950/70 p-5 transition duration-200 hover:border-violet-300/30 hover:bg-slate-900/70">
      <div className="flex items-start gap-4">
        <div className="rounded-2xl border border-violet-400/20 bg-violet-400/10 p-3 text-violet-200">
          <BrainCircuit size={20} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <h4 className="truncate text-base font-bold text-white">{title}</h4>
              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <Server size={13} />
                  {service}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Database size={13} />
                  Reflexion
                </span>
              </div>
            </div>

            <StatusBadge value={severity} />
          </div>

          <p className="mt-4 text-sm leading-6 text-slate-300">{summary}</p>
        </div>
      </div>
    </article>
  );
}
