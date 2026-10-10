"use client";

import { ChevronRight, CloudRain, LifeBuoy, Plus, Sprout } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { BigButton, ErrorNote } from "@/components/common";
import { FarmerShell } from "@/components/farmer-shell";
import { PerilIcon } from "@/components/peril-icon";
import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { longDate, rupees } from "@/lib/format";
import { PERIL, useLang } from "@/lib/i18n";
import type { FarmerClaim, Me } from "@/lib/types";

const CROP_HI: Record<string, string> = { paddy: "धान", wheat: "गेहूँ", maize: "मक्का" };

function HomeSkeleton() {
  return (
    <div className="mt-6 space-y-5" aria-busy>
      <Skeleton className="h-9 w-56" />
      <Skeleton className="h-52 w-full rounded-[var(--radius-touch)]" />
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-20 w-full rounded-[var(--radius-touch)]" />
    </div>
  );
}

export default function FarmerHome() {
  const { lang, t } = useLang();
  const { data: me, error } = useSWR<Me>("/api/me");
  const { data: claims } = useSWR<FarmerClaim[]>(me ? "/api/claims" : null);

  if (error) {
    return (
      <FarmerShell>
        <div className="mt-8 space-y-4">
          <ErrorNote message={error.message} />
          <Link href="/" className="font-semibold text-indigo underline">
            {t("changeUser")}
          </Link>
        </div>
      </FarmerShell>
    );
  }
  if (!me?.farmer) {
    return (
      <FarmerShell>
        <HomeSkeleton />
      </FarmerShell>
    );
  }

  const farmer = me.farmer;
  const policy = me.policies?.[0];
  const alert = me.alerts?.[0];
  const crop = policy ? (lang === "hi" ? (CROP_HI[policy.crop] ?? policy.crop) : policy.crop) : "";

  return (
    <FarmerShell demoToday={farmer.demo_today}>
      <h1 className="mt-6 text-3xl font-bold text-indigo">
        {t("hello", { name: lang === "hi" ? farmer.name_hi : farmer.name })}
      </h1>

      {alert && (
        <Alert role="status" className="mt-5 rounded-[var(--radius-touch)] border-2 border-haldi/50 bg-haldi-soft p-4 text-base">
          <CloudRain className="size-6! text-haldi-ink" aria-hidden />
          <AlertTitle className="text-lg font-bold text-haldi-ink">{t("alertTitle")}</AlertTitle>
          <AlertDescription className="text-base leading-snug text-ink">
            {t("alertBody", {
              mm: Math.round(alert.rain_mm),
              date: longDate(alert.date, lang),
              category: lang === "hi" ? alert.category_hi : alert.category_en,
            })}
            <BigButton
              className="mt-3 h-12 w-full text-base"
              render={<Link href={`/farmer/new/?peril=excess_rain&date=${alert.date}`} />}
              nativeButton={false}
            >
              {t("reportLoss")}
            </BigButton>
          </AlertDescription>
        </Alert>
      )}

      {policy && (
        <Card className="mt-5 rounded-[var(--radius-touch)] text-base">
          <CardContent>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-slate">{t("yourCover")}</p>
                <p className="mt-1 text-xl font-semibold capitalize">
                  {crop}, {policy.season}
                </p>
                <p className="text-slate">{t("plot", { khasra: policy.plot.khasra_no, village: policy.plot.village })}</p>
              </div>
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-paddy-soft text-paddy">
                <Sprout className="size-6" aria-hidden />
              </span>
            </div>
            <Separator className="my-4" />
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-sm text-slate">{t("coverAmount")}</p>
                <p className="w-condensed tabular text-4xl font-bold text-indigo">₹{rupees(policy.sum_insured_inr, lang)}</p>
              </div>
              <p className="text-right text-sm text-slate">{t("coveredTill", { date: longDate(policy.cover_end, lang) })}</p>
            </div>
            <ul className="mt-4 flex flex-wrap gap-2">
              {policy.perils.map((p) => (
                <li key={p} className="flex items-center gap-1.5 rounded-full bg-indigo-soft px-3 py-1 text-sm text-indigo">
                  <PerilIcon peril={p} className="size-4" />
                  {PERIL[p][lang]}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <section className="mt-8">
        <h2 className="text-xl font-bold">{t("yourClaims")}</h2>
        {!claims && <Skeleton className="mt-3 h-20 w-full rounded-[var(--radius-touch)]" />}
        {claims?.length === 0 && <p className="mt-2 text-slate">{t("noClaims")}</p>}
        {claims && claims.length > 0 && (
          <Card className="mt-3 gap-0 rounded-[var(--radius-touch)] py-0 text-base">
            <ul className="divide-y divide-line">
              {claims.map((c) => (
                <li key={c.claim_id}>
                  <Link href={`/farmer/claim/?id=${c.claim_id}`} className="flex items-center gap-3 p-4 hover:bg-indigo-soft/50">
                    <PerilIcon peril={c.peril} className="size-6 text-indigo" />
                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold">{PERIL[c.peril][lang]}</span>
                      <span className="block text-sm text-slate">{longDate(c.loss_date, lang)}</span>
                    </span>
                    <StatusBadge status={c.status} />
                    <ChevronRight className="size-5 text-slate" aria-hidden />
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </section>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-2">
        <Link href="/farmer/help/" className="flex min-h-12 items-center gap-2 rounded-xl px-1 font-semibold text-indigo">
          <LifeBuoy className="size-5" aria-hidden />
          {t("askHelp")}
        </Link>
        <Link href="/" className="flex min-h-11 items-center text-sm text-slate underline">
          {t("changeUser")}
        </Link>
      </div>

      <div className="fixed inset-x-0 bottom-0 border-t border-line bg-page/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto max-w-xl">
          <BigButton className="w-full" render={<Link href="/farmer/new/" />} nativeButton={false}>
            <Plus className="size-6" aria-hidden />
            {t("reportLoss")}
          </BigButton>
        </div>
      </div>
    </FarmerShell>
  );
}
