"use client";

import { ChevronRight, CloudRain, LifeBuoy, Plus } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { BigButton, ErrorNote, Spinner } from "@/components/common";
import { FarmerShell } from "@/components/farmer-shell";
import { PerilIcon } from "@/components/peril-icon";
import { StatusBadge } from "@/components/status-badge";
import { longDate, rupees } from "@/lib/format";
import { PERIL, useLang } from "@/lib/i18n";
import type { FarmerClaim, Me } from "@/lib/types";

const CROP_HI: Record<string, string> = { paddy: "धान", wheat: "गेहूँ", maize: "मक्का" };

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
        <div className="mt-10">
          <Spinner />
        </div>
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
        <section className="mt-5 rounded-[var(--radius-touch)] border-2 border-haldi/50 bg-haldi-soft p-4" role="status">
          <div className="flex items-start gap-3">
            <CloudRain className="mt-0.5 size-7 shrink-0 text-haldi-ink" aria-hidden />
            <div>
              <h2 className="text-lg font-bold text-haldi-ink">{t("alertTitle")}</h2>
              <p className="mt-1 leading-snug">
                {t("alertBody", {
                  mm: Math.round(alert.rain_mm),
                  date: longDate(alert.date, lang),
                  category: lang === "hi" ? alert.category_hi : alert.category_en,
                })}
              </p>
            </div>
          </div>
          <Link
            href={`/farmer/new/?peril=excess_rain&date=${alert.date}`}
            className="mt-3 flex min-h-12 items-center justify-center rounded-2xl bg-indigo px-4 font-semibold text-white"
          >
            {t("reportLoss")}
          </Link>
        </section>
      )}

      {policy && (
        <section className="mt-5 rounded-[var(--radius-touch)] bg-surface p-5 shadow-[0_1px_0_var(--color-line)]">
          <p className="text-slate">{t("yourCover")}</p>
          <p className="mt-1 text-xl font-semibold capitalize">
            {crop}, {policy.season}
          </p>
          <p className="text-slate">{t("plot", { khasra: policy.plot.khasra_no, village: policy.plot.village })}</p>
          <div className="mt-4 flex items-end justify-between gap-4">
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
        </section>
      )}

      <section className="mt-8">
        <h2 className="text-xl font-bold">{t("yourClaims")}</h2>
        {!claims && <div className="mt-4"><Spinner /></div>}
        {claims?.length === 0 && <p className="mt-2 text-slate">{t("noClaims")}</p>}
        <ul className="mt-3 divide-y divide-line overflow-hidden rounded-[var(--radius-touch)] bg-surface">
          {claims?.map((c) => (
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
      </section>

      <Link href="/farmer/help/" className="mt-6 flex min-h-12 items-center gap-2 font-semibold text-indigo">
        <LifeBuoy className="size-5" aria-hidden />
        {t("askHelp")}
      </Link>
      <Link href="/" className="mt-1 flex min-h-11 items-center text-sm text-slate underline">
        {t("changeUser")}
      </Link>

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
