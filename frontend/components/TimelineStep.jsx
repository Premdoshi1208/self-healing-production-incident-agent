import { CheckCircle2 } from "lucide-react";

export default function TimelineStep({ title, description, icon: Icon, index }) {
  const StepIcon = Icon || CheckCircle2;

  return (
    <div className="group rounded-2xl border border-slate-800 bg-slate-950/60 p-4 transition duration-200 hover:border-cyan-300/30 hover:bg-slate-900/70">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
          <StepIcon size={20} />
        </div>

        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.18em] text-cyan-300/80">
            Step {String(index).padStart(2, "0")}
          </p>
          <h4 className="mt-1 text-base font-bold text-white">{title}</h4>
          <p className="mt-2 text-sm leading-6 text-slate-400">{description}</p>
        </div>
      </div>
    </div>
  );
}
