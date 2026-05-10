export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  tone = "violet"
}) {
  const toneMap = {
    violet: "from-violet-500/20 text-violet-200 ring-violet-400/20",
    cyan: "from-cyan-500/20 text-cyan-200 ring-cyan-400/20",
    emerald: "from-emerald-500/20 text-emerald-200 ring-emerald-400/20",
    amber: "from-amber-500/20 text-amber-200 ring-amber-400/20",
    red: "from-red-500/20 text-red-200 ring-red-400/20"
  };

  return (
    <div className="glass-card group rounded-3xl p-5 transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/30 hover:shadow-cyanGlow">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-400">{title}</p>
          <h3 className="mt-3 truncate text-3xl font-black tracking-tight text-white">
            {value}
          </h3>
          <p className="mt-2 text-xs font-medium leading-5 text-slate-500">
            {subtitle}
          </p>
        </div>

        {Icon && (
          <div
            className={`rounded-2xl bg-gradient-to-br to-transparent p-3 ring-1 ${toneMap[tone] || toneMap.violet}`}
          >
            <Icon size={22} />
          </div>
        )}
      </div>
    </div>
  );
}
