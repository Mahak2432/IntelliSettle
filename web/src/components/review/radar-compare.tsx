"use client";

import { useState } from "react";

/** Drag to compare radar before and after the loss. Water shows in blue on the "after" image. */
export function RadarCompare({ before, after, beforeLabel, afterLabel }: { before?: string; after: string; beforeLabel: string; afterLabel: string }) {
  const [split, setSplit] = useState(50);
  if (!before) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={after} alt={afterLabel} className="aspect-square w-full rounded-xl object-cover" />
    );
  }
  return (
    <div className="select-none">
      <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-ink">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={after} alt={afterLabel} className="absolute inset-0 size-full object-cover" />
        <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={before} alt={beforeLabel} className="absolute inset-0 size-full object-cover" />
        </div>
        <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-white shadow" style={{ left: `${split}%` }} />
        <span className="absolute left-2 top-2 rounded bg-ink/70 px-2 py-0.5 text-xs text-white">{beforeLabel}</span>
        <span className="absolute right-2 top-2 rounded bg-water px-2 py-0.5 text-xs text-white">{afterLabel}</span>
        <span className="pointer-events-none absolute left-1/2 top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white" aria-hidden />
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={split}
        onChange={(e) => setSplit(Number(e.target.value))}
        className="mt-2 w-full accent-indigo"
        aria-label="Compare before and after"
      />
    </div>
  );
}
