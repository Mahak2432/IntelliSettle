"use client";

import {
  ArrowLeft,
  Check,
  CircleAlert,
  CircleHelp,
  CloudRain,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  Newspaper,
  Satellite,
  X,
} from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";
import { BigButton, ErrorNote, Spinner } from "@/components/common";
import { PerilIcon } from "@/components/peril-icon";
import { RadarCompare } from "@/components/review/radar-compare";
import { RainChart } from "@/components/review/rain-chart";
import { ReviewShell } from "@/components/review/review-shell";
import { ScoreGauge, VERDICT_TONE, VerdictBadge } from "@/components/review/verdict";
import { StatusBadge } from "@/components/status-badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { api, authedImageUrl } from "@/lib/api";
import { longDate, rupees, shortDateTime } from "@/lib/format";
import { PERIL } from "@/lib/i18n";
import type { CheckResult, EvidenceItem, ReviewClaim, Signal } from "@/lib/types";
import { cn } from "@/lib/utils";

const SIGNAL: Record<Signal, { label: string; className: string }> = {
  supports: { label: "Supports the claim", className: "bg-paddy-soft text-paddy" },
  contradicts: { label: "Contradicts the claim", className: "bg-chilli-soft text-chilli" },
  inconclusive: { label: "Inconclusive", className: "bg-muted text-slate" },
  unavailable: { label: "Not available", className: "bg-muted text-slate" },
};
const SOURCE_ICON: Record<string, typeof CloudRain> = {
  weather: CloudRain,
  satellite: Satellite,
  news: Newspaper,
  photo: ImageIcon,
};
const DOC_LABEL = { land_record: "Land record (Khatiyan)", bank_passbook: "Bank passbook", policy: "Policy" };

function useAuthedImage(path: string | null) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!path) return;
    let revoke: string | null = null;
    authedImageUrl(path).then((u) => setUrl((revoke = u))).catch(() => setUrl(null));
    return () => {
      if (revoke) URL.revokeObjectURL(revoke);
    };
  }, [path]);
  return url;
}

function ClaimPhoto({ path, alt }: { path: string; alt: string }) {
  const url = useAuthedImage(path);
  return url ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={url} alt={alt} className="aspect-[4/3] w-full rounded-lg object-cover" />
  ) : (
    <div className="aspect-[4/3] w-full animate-pulse rounded-lg bg-muted" />
  );
}

function EvidenceCard({ item, claimId, lossDate, photoCount }: { item: EvidenceItem; claimId: string; lossDate: string; photoCount: number }) {
  const Icon = SOURCE_ICON[item.source] ?? FileText;
  const signal = SIGNAL[item.signal];
  const m = item.metrics as Record<string, unknown>;
  return (
    <section className="rounded-xl border border-line bg-surface p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 font-semibold">
          <Icon className="size-5 text-indigo" aria-hidden />
          {item.label}
        </h3>
        <span className={cn("rounded-full px-2.5 py-0.5 text-sm font-medium", signal.className)}>{signal.label}</span>
      </header>
      <p className="mt-2 leading-snug">{item.summary}</p>

      {item.source === "satellite" && item.visuals.after && (
        <div className="mt-3 max-w-sm">
          <RadarCompare
            before={item.visuals.before}
            after={item.visuals.after}
            beforeLabel="Before"
            afterLabel={m.post_date ? `After, ${longDate(String(m.post_date))}` : "After"}
          />
        </div>
      )}
      {item.source === "weather" && m.daily_mm != null && (
        <div className="mt-3">
          <RainChart daily={m.daily_mm as Record<string, number>} lossDate={lossDate} />
        </div>
      )}
      {item.source === "photo" && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {Array.from({ length: Math.min(photoCount, 6) }, (_, i) => (
            <ClaimPhoto key={i} path={`/api/claims/${claimId}/files/photos/${i}`} alt={`Damage photo ${i + 1}`} />
          ))}
        </div>
      )}
      {item.source === "news" && Array.isArray(m.reports) && m.reports.length > 0 && (
        <ul className="mt-3 space-y-2 text-sm">
          {(m.reports as { title: string; publisher: string; published_date?: string; relevant_fact: string }[]).map((r) => (
            <li key={r.title} className="border-l-2 border-indigo/30 pl-3">
              <span className="font-medium">{r.publisher}</span>
              {r.published_date && <span className="text-slate">, {r.published_date}</span>}
              <span className="block">{r.relevant_fact}</span>
            </li>
          ))}
        </ul>
      )}
      {item.citations.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
          {item.citations.slice(0, 5).map((c) => (
            <li key={c.url}>
              <a href={c.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-indigo underline">
                {c.title}
                <ExternalLink className="size-3" aria-hidden />
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function CheckRow({ check }: { check: CheckResult }) {
  const Icon = check.status === "pass" ? Check : check.status === "fail" ? X : CircleHelp;
  return (
    <li className="flex gap-3 py-2.5">
      <span
        className={cn(
          "mt-0.5 grid size-6 shrink-0 place-items-center rounded-full",
          check.status === "pass" && "bg-paddy-soft text-paddy",
          check.status === "fail" && "bg-chilli-soft text-chilli",
          check.status === "unknown" && "bg-haldi-soft text-haldi-ink",
        )}
        aria-label={check.status}
      >
        <Icon className="size-4" />
      </span>
      <span>
        <span className="block font-medium leading-snug">{check.label}</span>
        <span className="block text-sm text-slate">{check.detail}</span>
      </span>
    </li>
  );
}

type Decision = { action: "approve" | "reject"; fast: boolean };

function ReviewClaimView() {
  const id = useSearchParams().get("id");
  const { data, error, mutate } = useSWR<ReviewClaim>(id ? `/api/claims/${id}` : null, {
    refreshInterval: (d) => (d && ["submitted", "assessing"].includes(d.claim.status) ? 2000 : 0),
  });
  const [pending, setPending] = useState<Decision | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  async function decide({ action, fast }: Decision) {
    setBusy(true);
    try {
      const updated = await api<ReviewClaim>(`/api/claims/${id}/decision`, {
        method: "POST",
        json: { action, fast_lane: fast, reason: reason.trim() || null },
      });
      await mutate(updated, false);
      toast.success(action === "approve" ? `Approved. ₹${rupees(updated.claim.payout?.amount_inr ?? 0)} sent.` : "Claim rejected. The farmer has been told why.");
      setPending(null);
      setReason("");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (error) return <ReviewShell><ErrorNote message={error.message} /></ReviewShell>;
  if (!data) return <ReviewShell><Spinner /></ReviewShell>;

  const { claim, farmer, policy } = data;
  const a = claim.assessment;
  const open = claim.status === "ready_for_review" || claim.status === "appealed";
  const appealed = claim.status === "appealed";
  const lastDecision = claim.decisions.at(-1);

  return (
    <ReviewShell>
      <Link href="/review/" className="-ml-2 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-indigo hover:bg-indigo-soft">
        <ArrowLeft className="size-4" aria-hidden />
        All claims
      </Link>

      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-indigo">{farmer.name}</h1>
          <p className="text-slate">
            {policy.plot.village}, {policy.plot.block}, {policy.plot.district}. Khasra {policy.plot.khasra_no},{" "}
            {policy.insured_area_ha} ha of <span className="capitalize">{policy.crop}</span> ({policy.season})
          </p>
          <p className="mt-1 flex items-center gap-2">
            <PerilIcon peril={claim.peril} className="size-4 text-indigo" />
            {PERIL[claim.peril].en} on {longDate(claim.loss_date)}. Filed {shortDateTime(claim.submitted_at)}.
            <span className="text-slate">{claim.claim_id}</span>
          </p>
          {claim.description && <p className="mt-2 max-w-2xl rounded-lg bg-surface px-3 py-2 italic">“{claim.description}”</p>}
        </div>
        <StatusBadge status={claim.status} lang="en" />
      </div>

      {!a ? (
        <div className="mt-8 rounded-xl border border-line bg-surface p-6">
          <Spinner label="AI is checking rainfall, radar, news and the documents. This takes about a minute." />
        </div>
      ) : (
        <>
          {/* Decision strip: the score, why, and the action, always together. */}
          <section className={cn("mt-6 grid gap-6 rounded-2xl border-2 bg-surface p-5 lg:grid-cols-[auto_1fr_auto]", "border-current/20", VERDICT_TONE[a.verdict].text)}>
            <ScoreGauge score={a.truth.score} verdict={a.verdict} thresholds={a.thresholds} />
            <div className="text-ink">
              <VerdictBadge verdict={a.verdict} />
              {a.truth.fallback && (
                <p className="mt-2 text-sm text-haldi-ink">AI scoring was unavailable; this is the rule-based fallback score, so the fast lane is off.</p>
              )}
              <ul className="mt-3 space-y-1.5">
                {a.truth.reasons.map((r) => (
                  <li key={r} className="flex gap-2"><Check className="mt-1 size-4 shrink-0 text-paddy" aria-hidden />{r}</li>
                ))}
                {a.truth.red_flags.map((r) => (
                  <li key={r} className="flex gap-2"><CircleAlert className="mt-1 size-4 shrink-0 text-chilli" aria-hidden />{r}</li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-slate">Scored by {a.truth.model}. The score never approves or pays anything on its own.</p>
            </div>
            <div className="flex min-w-64 flex-col gap-3 text-ink">
              <div>
                <p className="text-sm text-slate">Payout if approved</p>
                <p className="w-condensed tabular text-4xl font-bold">₹{rupees(a.payout_quote.amount_inr)}</p>
                <p className="text-sm text-slate">
                  {a.payout_quote.payout_percent}% of ₹{rupees(a.payout_quote.sum_insured_inr)}. {a.payout_quote.basis}
                </p>
              </div>
              {open ? (
                <>
                  {a.verdict === "looks_genuine" && !appealed && (
                    <BigButton tone="approve" busy={busy} onClick={() => decide({ action: "approve", fast: true })}>
                      Fast approve ₹{rupees(a.payout_quote.amount_inr)}
                    </BigButton>
                  )}
                  {a.verdict === "looks_suspicious" && !appealed && (
                    <BigButton tone="reject" busy={busy} onClick={() => setPending({ action: "reject", fast: true })}>
                      Fast reject
                    </BigButton>
                  )}
                  <div className="flex gap-2">
                    <BigButton tone="secondary" className="h-11 flex-1 text-base" disabled={busy || a.payout_quote.amount_inr <= 0} onClick={() => setPending({ action: "approve", fast: false })}>
                      Approve
                    </BigButton>
                    <BigButton tone="secondary" className="h-11 flex-1 text-base" disabled={busy} onClick={() => setPending({ action: "reject", fast: false })}>
                      Reject
                    </BigButton>
                  </div>
                  {appealed && <p className="text-sm text-haldi-ink">Appeal: “{claim.appeal?.message}”. Appeals always get a full review.</p>}
                </>
              ) : (
                lastDecision && (
                  <p className="rounded-lg bg-muted px-3 py-2 text-sm">
                    {lastDecision.action === "approve" ? "Approved" : "Rejected"}
                    {lastDecision.fast_lane ? " in the fast lane" : " after full review"} on {shortDateTime(lastDecision.decided_at)}.
                    {lastDecision.reason && <span className="block">Reason: {lastDecision.reason}</span>}
                    {claim.payout && <span className="block">Paid, reference {claim.payout.reference}.</span>}
                  </p>
                )
              )}
            </div>
          </section>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
            <div className="space-y-4">
              <h2 className="text-xl font-bold">Evidence</h2>
              {a.evidence.map((e) => (
                <EvidenceCard key={e.source} item={e} claimId={claim.claim_id} lossDate={claim.loss_date} photoCount={claim.photos.length} />
              ))}
            </div>
            <aside className="space-y-6">
              <section>
                <h2 className="text-xl font-bold">Rule checks</h2>
                <ul className="mt-2 divide-y divide-line rounded-xl border border-line bg-surface px-4">
                  {a.checks.map((c) => <CheckRow key={c.code} check={c} />)}
                </ul>
              </section>
              {claim.documents.length > 0 && (
                <section>
                  <h2 className="text-xl font-bold">Documents read by AI</h2>
                  <div className="mt-2 space-y-3">
                    {claim.documents.map((d, i) => (
                      <div key={d.document_id} className="rounded-xl border border-line bg-surface p-3">
                        <p className="font-semibold">{DOC_LABEL[d.kind]}</p>
                        <div className="mt-2 grid grid-cols-[96px_1fr] gap-3">
                          <ClaimPhoto path={`/api/claims/${claim.claim_id}/files/documents/${i}`} alt={DOC_LABEL[d.kind]} />
                          <dl className="space-y-1 text-sm">
                            {d.extraction ? (
                              Object.entries(d.extraction.fields).map(([k, f]) => (
                                <div key={k} className="flex justify-between gap-2">
                                  <dt className="text-slate">{k.replaceAll("_", " ")}</dt>
                                  <dd className={cn("text-right font-medium", f.confidence < 0.85 && "text-haldi-ink")}>
                                    {f.value ?? "unreadable"}
                                    <span className="tabular ml-1 text-xs text-slate">{Math.round(f.confidence * 100)}%</span>
                                  </dd>
                                </div>
                              ))
                            ) : (
                              <p className="text-slate">Not read yet.</p>
                            )}
                          </dl>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
              <section>
                <h2 className="text-xl font-bold">History</h2>
                <ol className="mt-2 space-y-2 text-sm">
                  {claim.timeline.map((e) => (
                    <li key={`${e.at}-${e.status}`} className="flex gap-3">
                      <span className="tabular w-28 shrink-0 text-slate">{shortDateTime(e.at)}</span>
                      <span>{e.note}</span>
                    </li>
                  ))}
                </ol>
              </section>
            </aside>
          </div>
        </>
      )}

      <Dialog open={pending !== null} onOpenChange={(o) => !o && setPending(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {pending?.action === "approve" ? `Approve ₹${rupees(a?.payout_quote.amount_inr ?? 0)}` : pending?.fast ? "Fast reject" : "Reject claim"}
            </DialogTitle>
            <DialogDescription>
              {pending?.fast
                ? "Optional: add a note. The farmer sees the reason and can appeal once."
                : "Write the reason for your decision (at least 10 characters). The farmer sees it."}
            </DialogDescription>
          </DialogHeader>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} className="min-h-24" placeholder="Reason" />
          <DialogFooter>
            <BigButton
              tone={pending?.action === "approve" ? "approve" : "reject"}
              className="h-11 text-base"
              busy={busy}
              disabled={!pending?.fast && reason.trim().length < 10}
              onClick={() => pending && decide(pending)}
            >
              {pending?.action === "approve" ? "Approve and pay" : "Reject claim"}
            </BigButton>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </ReviewShell>
  );
}

export default function ReviewClaimPage() {
  return (
    <Suspense>
      <ReviewClaimView />
    </Suspense>
  );
}
