"use client";

import { ChevronRight, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";
import { BigButton, BrandMark, ErrorNote, LangToggle, Spinner } from "@/components/common";
import { PerilIcon } from "@/components/peril-icon";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { longDate } from "@/lib/format";
import { useLang } from "@/lib/i18n";
import { startFarmerSession, startOfficerSession } from "@/lib/session";
import type { Persona } from "@/lib/types";

export default function Home() {
  const { lang, t } = useLang();
  const router = useRouter();
  const { data: personas, error } = useSWR<Persona[]>("/api/demo/personas");
  const [busy, setBusy] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  async function enter(key: string, start: () => Promise<void>, to: string) {
    setBusy(key);
    setFailure(null);
    try {
      await start();
      router.push(to);
    } catch (e) {
      setFailure(e instanceof Error ? e.message : String(e));
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-4 pb-16 pt-5 sm:px-8">
      <header className="flex items-center justify-between gap-3">
        <BrandMark />
        <div className="flex items-center gap-2">
          <LangToggle />
          <ThemeToggle />
        </div>
      </header>

      <section className="mt-10 sm:mt-16">
        <h1 className="max-w-3xl text-[2.35rem] font-bold leading-[1.15] text-indigo sm:text-6xl sm:leading-[1.08]">
          {t("tagline")}
        </h1>
        <p className="mt-4 max-w-2xl text-lg leading-relaxed text-slate sm:text-xl">{t("heroSub")}</p>
      </section>

      <section aria-labelledby="how" className="mt-10">
        <h2 id="how" className="sr-only">
          {t("howTitle")}
        </h2>
        <ol className="grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-3">
          {(["step1", "step2", "step3"] as const).map((key, i) => (
            <li key={key} className="flex gap-3 bg-surface p-4">
              <span className="w-condensed grid size-8 shrink-0 place-items-center rounded-full bg-indigo text-base font-bold text-white">
                {i + 1}
              </span>
              <p className="leading-snug">{t(key)}</p>
            </li>
          ))}
        </ol>
      </section>

      {failure && (
        <div className="mt-6">
          <ErrorNote message={failure} />
        </div>
      )}

      <div className="mt-12 grid gap-10 lg:grid-cols-[1.6fr_1fr] lg:gap-12">
        <section aria-labelledby="farmers">
          <h2 id="farmers" className="text-2xl font-bold">
            {t("farmer")}
          </h2>
          <p className="mt-1 text-slate">{t("pickFarmer")}</p>
          <ul className="mt-5 space-y-3">
            {error && <ErrorNote message={error.message} />}
            {!personas &&
              !error &&
              [0, 1, 2].map((i) => (
                <li key={i}>
                  <Skeleton className="h-32 w-full rounded-[var(--radius-touch)]" />
                </li>
              ))}
            {personas?.map((p) => (
              <li key={p.farmer_id}>
                <button
                  onClick={() => enter(p.farmer_id, () => startFarmerSession(p.farmer_id), "/farmer/")}
                  disabled={busy !== null}
                  className="group block w-full rounded-[var(--radius-touch)] text-left disabled:opacity-60"
                >
                <Card className="rounded-[var(--radius-touch)] text-base transition-shadow group-hover:ring-indigo/40">
                  <CardContent className="flex items-start gap-4">
                    <span className="mt-0.5 grid size-12 shrink-0 place-items-center rounded-2xl bg-indigo-soft text-indigo">
                      <PerilIcon peril={p.peril} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex flex-wrap items-center gap-2">
                        <span className="text-lg font-semibold leading-snug">{lang === "hi" ? p.name_hi : p.name}</span>
                        {p.fraud_test && (
                          <Badge className="h-auto border-0 bg-haldi-soft px-2 py-0.5 text-haldi-ink">{t("fraudTest")}</Badge>
                        )}
                      </span>
                      <span className="block text-slate">
                        {p.village}, {p.district}. {lang === "hi" ? p.crop_hi : p.crop_en}
                      </span>
                      <span className="mt-1 block leading-snug">{lang === "hi" ? p.story_hi : p.story_en}</span>
                      <span className="mt-1 block text-sm text-slate">
                        {t("demoDate", { date: longDate(p.demo_today, lang) })}
                      </span>
                    </span>
                    {busy === p.farmer_id ? (
                      <Spinner />
                    ) : (
                      <ChevronRight className="mt-3 size-5 shrink-0 text-slate" aria-hidden />
                    )}
                  </CardContent>
                </Card>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="officer">
          <h2 id="officer" className="text-2xl font-bold">
            {t("officer")}
          </h2>
          <Card className="mt-5 rounded-[var(--radius-touch)] text-base">
            <CardContent className="space-y-4">
              <span className="grid size-12 place-items-center rounded-2xl bg-indigo-soft text-indigo">
                <ShieldCheck className="size-6" aria-hidden />
              </span>
              <p className="leading-snug text-slate">{t("officerBlurb")}</p>
              <BigButton
                className="w-full"
                busy={busy === "officer"}
                disabled={busy !== null}
                onClick={() => enter("officer", startOfficerSession, "/review/")}
              >
                {t("openDesk")}
              </BigButton>
            </CardContent>
          </Card>
        </section>
      </div>

      <p className="mt-14 border-t border-line pt-5 text-sm text-slate">{t("demoNote")}</p>
    </main>
  );
}
