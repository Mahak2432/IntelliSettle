import { CircleAlert, CircleCheck, CircleHelp } from "lucide-react";
import { VERDICT } from "@/lib/i18n";
import type { Thresholds, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

export const VERDICT_TONE: Record<Verdict, { text: string; soft: string; solid: string; stroke: string }> = {
  looks_genuine: { text: "text-paddy", soft: "bg-paddy-soft", solid: "bg-paddy", stroke: "var(--color-paddy)" },
  needs_review: { text: "text-haldi-ink", soft: "bg-haldi-soft", solid: "bg-haldi", stroke: "var(--color-haldi)" },
  looks_suspicious: { text: "text-chilli", soft: "bg-chilli-soft", solid: "bg-chilli", stroke: "var(--color-chilli)" },
};

const ICON = { looks_genuine: CircleCheck, needs_review: CircleHelp, looks_suspicious: CircleAlert };

export function VerdictBadge({ verdict, className }: { verdict: Verdict; className?: string }) {
  const Icon = ICON[verdict];
  const tone = VERDICT_TONE[verdict];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold", tone.soft, tone.text, className)}>
      <Icon className="size-4" aria-hidden />
      {VERDICT[verdict]}
    </span>
  );
}

/** Half-circle dial. The coloured bands are the officer's own thresholds, so the dial explains the verdict. */
export function ScoreGauge({ score, verdict, thresholds }: { score: number; verdict: Verdict; thresholds: Thresholds }) {
  const r = 80;
  const arc = (from: number, to: number) => {
    const a = (v: number) => Math.PI * (1 - v / 100);
    const [x1, y1] = [100 + r * Math.cos(a(from)), 100 - r * Math.sin(a(from))];
    const [x2, y2] = [100 + r * Math.cos(a(to)), 100 - r * Math.sin(a(to))];
    return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
  };
  const low = thresholds.suspicious_at_or_below;
  const high = thresholds.genuine_at_or_above;
  const needle = Math.PI * (1 - score / 100);
  return (
    <figure className="relative w-44" aria-label={`Truth score ${score} out of 100`}>
      <svg viewBox="0 0 200 112" className="w-full">
        <path d={arc(0, low)} stroke="var(--color-chilli)" strokeOpacity={0.25} strokeWidth={14} fill="none" />
        <path d={arc(low, high)} stroke="var(--color-haldi)" strokeOpacity={0.25} strokeWidth={14} fill="none" />
        <path d={arc(high, 100)} stroke="var(--color-paddy)" strokeOpacity={0.25} strokeWidth={14} fill="none" />
        <path d={arc(0, Math.max(score, 0.5))} stroke={VERDICT_TONE[verdict].stroke} strokeWidth={14} strokeLinecap="round" fill="none" />
        <circle cx={100 + 66 * Math.cos(needle)} cy={100 - 66 * Math.sin(needle)} r={4} fill="var(--color-ink)" />
      </svg>
      <figcaption className="absolute inset-x-0 bottom-0 text-center">
        <span className={cn("w-condensed tabular block text-5xl font-bold leading-none", VERDICT_TONE[verdict].text)}>{score}</span>
        <span className="text-xs text-slate">truth score</span>
      </figcaption>
    </figure>
  );
}
