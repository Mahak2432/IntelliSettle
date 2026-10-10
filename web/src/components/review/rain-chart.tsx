/** Daily rainfall bars with the 100 mm / 24 h policy trigger drawn as a line. */
export function RainChart({ daily, lossDate, trigger = 100 }: { daily: Record<string, number>; lossDate: string; trigger?: number }) {
  // Firestore does not preserve map order, so sort the days explicitly.
  const days = Object.entries(daily).sort(([a], [b]) => a.localeCompare(b));
  if (!days.length) return null;
  const max = Math.max(trigger * 1.15, ...days.map(([, v]) => v));
  const h = 120;
  const barW = 100 / days.length;
  const y = (v: number) => h - (v / max) * h;
  return (
    <figure>
      <svg viewBox={`0 0 100 ${h + 16}`} preserveAspectRatio="none" className="h-40 w-full overflow-visible" role="img" aria-label="Daily rainfall">
        <line x1={0} x2={100} y1={y(trigger)} y2={y(trigger)} stroke="var(--color-chilli)" strokeDasharray="2 1.5" strokeWidth={0.4} vectorEffect="non-scaling-stroke" />
        {days.map(([day, mm], i) => (
          <rect
            key={day}
            x={i * barW + barW * 0.18}
            width={barW * 0.64}
            y={y(mm)}
            height={Math.max(h - y(mm), 0.6)}
            rx={0.8}
            fill={day === lossDate ? "var(--color-water)" : "var(--color-indigo)"}
            fillOpacity={day === lossDate ? 1 : 0.35}
          />
        ))}
      </svg>
      <div className="-mt-3 grid text-center text-xs text-slate" style={{ gridTemplateColumns: `repeat(${days.length}, 1fr)` }}>
        {days.map(([day, mm]) => (
          <span key={day} className={day === lossDate ? "font-semibold text-water" : undefined}>
            <span className="tabular block font-semibold">{Math.round(mm)} mm</span>
            {new Date(`${day}T12:00:00+05:30`).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
          </span>
        ))}
      </div>
      <figcaption className="mt-2 text-xs text-slate">Dashed line: {trigger} mm in 24 hours, the policy trigger.</figcaption>
    </figure>
  );
}
