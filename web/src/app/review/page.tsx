"use client";

import { SlidersHorizontal } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";
import { ErrorNote, Spinner } from "@/components/common";
import { PerilIcon } from "@/components/peril-icon";
import { ReviewShell } from "@/components/review/review-shell";
import { VERDICT_TONE, VerdictBadge } from "@/components/review/verdict";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Slider } from "@/components/ui/slider";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { longDate, rupees, shortDateTime } from "@/lib/format";
import { PERIL } from "@/lib/i18n";
import type { QueueItem, Thresholds, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

type Filter = Verdict | "decided" | "all";
const OPEN = new Set(["ready_for_review", "appealed"]);
const FILTERS: { key: Filter; label: string }[] = [
  { key: "looks_genuine", label: "Looks genuine" },
  { key: "needs_review", label: "Needs review" },
  { key: "looks_suspicious", label: "Looks suspicious" },
  { key: "decided", label: "Decided" },
  { key: "all", label: "All" },
];

function matches(item: QueueItem, filter: Filter) {
  if (filter === "all") return true;
  if (filter === "decided") return ["approved", "paid", "rejected"].includes(item.status);
  return OPEN.has(item.status) && item.verdict === filter;
}

export default function ReviewQueue() {
  const { data: queue, error } = useSWR<QueueItem[]>("/api/claims", { refreshInterval: 4000 });
  const [chosen, setFilter] = useState<Filter | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const counts = Object.fromEntries(FILTERS.map((f) => [f.key, queue?.filter((q) => matches(q, f.key)).length ?? 0]));
  // Until the officer picks a tab, open the first one that has claims in it.
  const filter: Filter = chosen ?? FILTERS.find((f) => counts[f.key] > 0)?.key ?? "looks_genuine";
  const rows = queue?.filter((q) => matches(q, filter)) ?? [];
  const checking = queue?.filter((q) => q.status === "submitted" || q.status === "assessing").length ?? 0;
  const waiting = queue?.filter((q) => OPEN.has(q.status)).length ?? 0;
  const genuinePayable =
    queue?.filter((q) => matches(q, "looks_genuine")).reduce((sum, q) => sum + (q.amount_inr ?? 0), 0) ?? 0;

  return (
    <ReviewShell
      actions={
        <Button variant="outline" onClick={() => setSettingsOpen(true)} className="h-9 gap-2">
          <SlidersHorizontal className="size-4" aria-hidden />
          Fast-lane rules
        </Button>
      }
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-indigo">Claims to review</h1>
          <p className="text-slate">
            Every claim is checked against rainfall, radar and news before it reaches you. You make every decision.
          </p>
        </div>
        {checking > 0 && <Spinner label={`AI is checking ${checking} new claim${checking > 1 ? "s" : ""}`} />}
      </div>

      {queue && (
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <Card size="sm" className="text-base">
            <CardContent>
              <p className="text-sm text-slate">Waiting for you</p>
              <p className="w-condensed tabular text-4xl font-bold">{waiting}</p>
            </CardContent>
          </Card>
          <Card size="sm" className="text-base">
            <CardContent>
              <p className="text-sm text-slate">Ready for fast approve</p>
              <p className="flex items-baseline gap-2">
                <span className="w-condensed tabular text-4xl font-bold text-paddy">{counts.looks_genuine}</span>
                {genuinePayable > 0 && <span className="tabular text-slate">₹{rupees(genuinePayable)} payable</span>}
              </p>
            </CardContent>
          </Card>
          <Card size="sm" className="text-base">
            <CardContent>
              <p className="text-sm text-slate">Flagged as suspicious</p>
              <p className="w-condensed tabular text-4xl font-bold text-chilli">{counts.looks_suspicious}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={filter} onValueChange={(v) => setFilter(v as Filter)} className="mt-6">
        <TabsList className="h-auto flex-wrap">
          {FILTERS.map((f) => (
            <TabsTrigger key={f.key} value={f.key} className="gap-2 px-3 py-1.5">
              {f.label}
              <span className="tabular rounded-full bg-muted px-1.5 text-xs">{counts[f.key]}</span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {error && <div className="mt-6"><ErrorNote message={error.message} /></div>}
      {!queue && !error && (
        <div className="mt-4 space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}
      {queue && rows.length === 0 && (
        <p className="mt-10 text-center text-slate">Nothing here right now. New claims appear within a minute of being filed.</p>
      )}

      {rows.length > 0 && (
        <Card className="mt-4 gap-0 py-0">
          <Table className="min-w-[760px] text-base">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="px-4 text-slate">Farmer</TableHead>
                <TableHead className="text-slate">Loss</TableHead>
                <TableHead className="text-slate">Filed</TableHead>
                <TableHead className="text-right text-slate">Score</TableHead>
                <TableHead className="text-slate">AI verdict</TableHead>
                <TableHead className="px-4 text-right text-slate">Payout</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((q) => (
                <TableRow key={q.claim_id} className="relative hover:bg-indigo-soft/40">
                  <TableCell className="px-4 py-3">
                    <Link href={`/review/claim/?id=${q.claim_id}`} className="font-semibold text-indigo after:absolute after:inset-0">
                      {q.farmer_name}
                    </Link>
                    <span className="block text-sm text-slate">
                      {q.village}, {q.district}
                    </span>
                  </TableCell>
                  <TableCell className="py-3">
                    <span className="flex items-center gap-2">
                      <PerilIcon peril={q.peril} className="size-4 text-slate" />
                      {PERIL[q.peril].en}
                    </span>
                    <span className="block text-sm capitalize text-slate">
                      {q.crop}, {longDate(q.loss_date)}
                    </span>
                  </TableCell>
                  <TableCell className="py-3 text-sm text-slate">{shortDateTime(q.submitted_at)}</TableCell>
                  <TableCell className="py-3 text-right">
                    <span className={cn("w-condensed tabular text-3xl font-bold", q.verdict ? VERDICT_TONE[q.verdict].text : "text-slate")}>
                      {q.score ?? "…"}
                    </span>
                  </TableCell>
                  <TableCell className="py-3">
                    {OPEN.has(q.status) && q.verdict ? <VerdictBadge verdict={q.verdict} /> : <StatusBadge status={q.status} lang="en" />}
                    {q.appealed && <span className="ml-2 text-sm text-haldi-ink">Appeal</span>}
                  </TableCell>
                  <TableCell className="tabular px-4 py-3 text-right font-semibold">
                    {q.amount_inr != null ? `₹${rupees(q.amount_inr)}` : "…"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <ThresholdsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </ReviewShell>
  );
}

function ThresholdsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const { data, mutate } = useSWR<Thresholds>(open ? "/api/review/thresholds" : null);
  const [draft, setDraft] = useState<[number, number] | null>(null);
  const value = draft ?? (data ? [data.suspicious_at_or_below, data.genuine_at_or_above] : [30, 80]);

  async function save() {
    try {
      const saved = await api<Thresholds>("/api/review/thresholds", {
        method: "PUT",
        json: { suspicious_at_or_below: value[0], genuine_at_or_above: value[1] },
      });
      await mutate(saved, false);
      toast.success("Fast-lane rules saved. They apply to claims checked from now on.");
      onOpenChange(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); setDraft(null); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Fast-lane rules</DialogTitle>
          <DialogDescription>
            A one-click Fast approve appears only when every rule check passes, an independent source confirms the
            event, and the truth score is at or above the green mark. Fast reject appears at or below the red mark,
            or when any rule fails.
          </DialogDescription>
        </DialogHeader>
        <Slider
          value={value}
          min={0}
          max={100}
          step={5}
          onValueChange={(v) => setDraft(v as [number, number])}
          className="my-6"
        />
        <div className="flex justify-between text-sm">
          <span className="text-chilli">Fast reject at or below <b className="tabular">{value[0]}</b></span>
          <span className="text-paddy">Fast approve at or above <b className="tabular">{value[1]}</b></span>
        </div>
        <DialogFooter>
          <Button onClick={save} disabled={value[0] >= value[1]}>
            Save rules
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
