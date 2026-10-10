"use client";

import { BadgeIndianRupee, Check, CircleX, Loader2 } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";
import { BigButton, ErrorNote, Spinner } from "@/components/common";
import { FarmerShell } from "@/components/farmer-shell";
import { PerilIcon } from "@/components/peril-icon";
import { StatusBadge } from "@/components/status-badge";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { longDate, rupees, shortDateTime } from "@/lib/format";
import { PERIL, STATUS, useLang } from "@/lib/i18n";
import type { ClaimStatus, FarmerClaim, Me } from "@/lib/types";
import { cn } from "@/lib/utils";

const IN_PROGRESS: ClaimStatus[] = ["submitted", "assessing"];

// The farmer-facing journey is a real sequence, so it is shown as ordered steps.
const JOURNEY: { status: ClaimStatus[]; key: ClaimStatus }[] = [
  { status: ["submitted"], key: "submitted" },
  { status: ["ready_for_review"], key: "ready_for_review" },
  { status: ["approved", "rejected"], key: "approved" },
  { status: ["paid"], key: "paid" },
];

function ClaimView() {
  const { lang, t } = useLang();
  const id = useSearchParams().get("id");
  const { data: me } = useSWR<Me>("/api/me");
  const { data: claim, error, mutate } = useSWR<FarmerClaim>(id ? `/api/claims/${id}` : null, {
    refreshInterval: (c) => (c && IN_PROGRESS.includes(c.status) ? 2000 : 0),
  });
  const [appeal, setAppeal] = useState("");
  const [sending, setSending] = useState(false);

  async function sendAppeal() {
    setSending(true);
    try {
      await mutate(await api<FarmerClaim>(`/api/claims/${id}/appeal`, { method: "POST", json: { message: appeal } }), false);
      toast.success(t("appealSent"));
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
    } finally {
      setSending(false);
    }
  }

  const shell = (body: React.ReactNode) => (
    <FarmerShell back={{ href: "/farmer/", label: t("backHome") }} demoToday={me?.farmer?.demo_today}>
      {body}
    </FarmerShell>
  );
  if (error) return shell(<div className="mt-8"><ErrorNote message={error.message} /></div>);
  if (!claim) return shell(<div className="mt-10"><Spinner /></div>);

  const message = lang === "hi" ? claim.message_hi : claim.message_en;
  const reached = new Map(claim.timeline.map((e) => [e.status, e.at]));
  const rejected = claim.status === "rejected" || (claim.status === "appealed" && reached.has("rejected"));

  return shell(
    <>
      <div className="mt-6 flex items-center gap-3">
        <PerilIcon peril={claim.peril} className="size-8 text-indigo" />
        <div>
          <h1 className="text-2xl font-bold text-indigo">{PERIL[claim.peril][lang]}</h1>
          <p className="text-slate">
            {longDate(claim.loss_date, lang)}. {t("claimNo", { id: claim.claim_id })}
          </p>
        </div>
      </div>

      <section className="mt-6 rounded-[var(--radius-touch)] bg-surface p-5">
        <StatusBadge status={claim.status} />
        {IN_PROGRESS.includes(claim.status) && (
          <div className="mt-4 flex gap-3">
            <Loader2 className="mt-1 size-6 shrink-0 animate-spin text-indigo" aria-hidden />
            <p className="text-lg leading-snug">{t("checking")}</p>
          </div>
        )}
        {claim.payout && (
          <div className="mt-4">
            <p className="w-condensed tabular text-5xl font-bold text-paddy">₹{rupees(claim.payout.amount_inr, lang)}</p>
            <p className="mt-1 text-lg">
              {t("sentTo", { amount: rupees(claim.payout.amount_inr, lang), account: claim.payout.account_masked })}
            </p>
            <p className="text-sm text-slate">{t("reference", { ref: claim.payout.reference })}</p>
          </div>
        )}
        {claim.decision_reason && (
          <p className="mt-4 text-lg">
            <span className="font-semibold">{t("reason")}: </span>
            {claim.decision_reason}
          </p>
        )}
        {message && !claim.payout && (
          <div className="mt-4 border-t border-line pt-4">
            <h2 className="font-semibold text-slate">{t("whatWeChecked")}</h2>
            <p className="mt-1 text-lg leading-snug">{message}</p>
          </div>
        )}
      </section>

      <ol className="mt-6 space-y-0">
        {JOURNEY.map((step, i) => {
          const at = step.status.map((s) => reached.get(s)).find(Boolean);
          const isRejectStep = step.key === "approved" && rejected;
          const label = isRejectStep ? STATUS.rejected[lang] : STATUS[step.key][lang];
          return (
            <li key={step.key} className="flex gap-4">
              <div className="flex flex-col items-center">
                <span
                  className={cn(
                    "grid size-9 place-items-center rounded-full border-2 text-sm font-bold",
                    at && !isRejectStep && "border-paddy bg-paddy text-white",
                    at && isRejectStep && "border-chilli bg-chilli text-white",
                    !at && "border-line bg-surface text-slate",
                  )}
                >
                  {at ? isRejectStep ? <CircleX className="size-5" /> : <Check className="size-5" /> : i + 1}
                </span>
                {i < JOURNEY.length - 1 && <span className="w-0.5 flex-1 bg-line" />}
              </div>
              <div className="pb-6 pt-1.5">
                <p className={cn("font-semibold", !at && "text-slate")}>{label}</p>
                {at && <p className="text-sm text-slate">{shortDateTime(at, lang)}</p>}
              </div>
            </li>
          );
        })}
      </ol>

      {claim.can_appeal && (
        <section className="mt-2 rounded-[var(--radius-touch)] bg-surface p-5">
          <h2 className="text-lg font-bold">{t("appealTitle")}</h2>
          <Textarea
            value={appeal}
            onChange={(e) => setAppeal(e.target.value)}
            placeholder={t("appealPlaceholder")}
            className="mt-3 min-h-24 text-lg"
          />
          <BigButton className="mt-3 w-full" busy={sending} disabled={appeal.trim().length < 10} onClick={sendAppeal}>
            <BadgeIndianRupee className="size-5" aria-hidden />
            {t("sendAppeal")}
          </BigButton>
        </section>
      )}
    </>,
  );
}

export default function ClaimPage() {
  return (
    <Suspense>
      <ClaimView />
    </Suspense>
  );
}
