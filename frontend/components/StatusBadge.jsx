import { CheckCircle2, CircleDashed, ShieldAlert, XCircle } from "lucide-react";

export default function StatusBadge({ value, size = "sm" }) {
  const normalized = String(value || "unknown").toUpperCase();

  let styles = "border-slate-600/70 bg-slate-700/30 text-slate-200";
  let Icon = CircleDashed;

  if (
    ["PASS", "PASSED", "APPROVED", "APPROVED_STAGING", "COMPLETED", "HEALTHY", "UP", "SUCCESS"].includes(normalized)
  ) {
    styles = "border-emerald-400/30 bg-emerald-400/10 text-emerald-200";
    Icon = CheckCircle2;
  }

  if (["PARTIAL", "WARNING", "PENDING", "NOT RUN", "UNKNOWN"].includes(normalized)) {
    styles = "border-amber-400/30 bg-amber-400/10 text-amber-200";
    Icon = ShieldAlert;
  }

  if (
    ["FAIL", "FAILED", "REJECTED", "CRITICAL", "DOWN", "BLOCKED", "ERROR"].includes(normalized)
  ) {
    styles = "border-red-400/30 bg-red-400/10 text-red-200";
    Icon = XCircle;
  }

  const sizeClass = size === "lg" ? "px-3.5 py-1.5 text-sm" : "px-3 py-1 text-xs";

  return (
    <span
      className={`inline-flex max-w-full items-center gap-1.5 rounded-full border font-bold uppercase tracking-wide ${sizeClass} ${styles}`}
    >
      <Icon size={size === "lg" ? 15 : 13} />
      <span className="truncate">{value || "unknown"}</span>
    </span>
  );
}
