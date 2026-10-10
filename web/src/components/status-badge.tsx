"use client";

import { STATUS, useLang } from "@/lib/i18n";
import type { ClaimStatus, Lang } from "@/lib/types";
import { cn } from "@/lib/utils";

const TONE: Record<ClaimStatus, string> = {
  submitted: "bg-indigo-soft text-indigo",
  assessing: "bg-indigo-soft text-indigo",
  ready_for_review: "bg-indigo-soft text-indigo",
  approved: "bg-paddy-soft text-paddy",
  paid: "bg-paddy-soft text-paddy",
  rejected: "bg-chilli-soft text-chilli",
  appealed: "bg-haldi-soft text-haldi-ink",
};

export function StatusBadge({ status, className, lang }: { status: ClaimStatus; className?: string; lang?: Lang }) {
  const { lang: current } = useLang();
  return (
    <span className={cn("inline-flex rounded-full px-3 py-1 text-sm font-semibold", TONE[status], className)}>
      {STATUS[status][lang ?? current]}
    </span>
  );
}
