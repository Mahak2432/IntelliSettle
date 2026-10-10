"use client";

import { ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";
import { PerilIcon } from "@/components/peril-icon";
import { BigButton, BrandMark, ErrorNote, LangToggle, Spinner } from "@/components/common";
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
      <header className="flex items-center justify-between">
        <BrandMark />
        <LangToggle />
      </header>

      <h1 className="mt-10 max-w-3xl text-[2.35rem] font-bold leading-[1.15] text-indigo sm:mt-16 sm:text-6xl sm:leading-[1.08]">
        {t("tagline")}
      </h1>

      {failure && (
        <div className="mt-6">
          <ErrorNote message={failure} />
        </div>
      )}

      <div className="mt-10 grid gap-10 sm:mt-14 lg:grid-cols-[1.6fr_1fr] lg:gap-14">
        <section aria-labelledby="farmers">
          <h2 id="farmers" className="text-2xl font-bold">
            {t("farmer")}
          </h2>
          <p className="mt-1 text-slate">{t("pickFarmer")}</p>
          <ul className="mt-5 space-y-3">
            {error && <ErrorNote message={error.message} />}
            {!personas && !error && <Spinner />}
            {personas?.map((p) => (
              <li key={p.farmer_id}>
                <button
                  onClick={() => enter(p.farmer_id, () => startFarmerSession(p.farmer_id), "/farmer/")}
                  disabled={busy !== null}
                  className="group flex w-full items-start gap-4 rounded-[var(--radius-touch)] border border-line bg-surface p-4 text-left transition-colors hover:border-indigo/40 disabled:opacity-60"
                >
                  <span className="mt-0.5 grid size-12 shrink-0 place-items-center rounded-2xl bg-indigo-soft text-indigo">
                    <PerilIcon peril={p.peril} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-lg font-semibold leading-snug">
                      {lang === "hi" ? p.name_hi : p.name}
                    </span>
                    <span className="block text-slate">
                      {p.village}, {p.district}. {lang === "hi" ? p.crop_hi : p.crop_en}
                    </span>
                    <span className="mt-1 block text-[0.95rem] leading-snug">
                      {lang === "hi" ? p.story_hi : p.story_en}
                    </span>
                    <span className="mt-1 block text-sm text-slate">
                      {t("demoDate", { date: longDate(p.demo_today, lang) })}
                    </span>
                  </span>
                  {busy === p.farmer_id && <Spinner />}
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="officer" className="lg:pt-0">
          <h2 id="officer" className="text-2xl font-bold">
            {t("officer")}
          </h2>
          <p className="mt-1 text-slate">{t("officerBlurb")}</p>
          <BigButton
            className="mt-5 w-full"
            busy={busy === "officer"}
            disabled={busy !== null}
            onClick={() => enter("officer", startOfficerSession, "/review/")}
          >
            <ShieldCheck className="size-5" aria-hidden />
            {t("openDesk")}
          </BigButton>
        </section>
      </div>

      <p className="mt-14 border-t border-line pt-5 text-sm text-slate">{t("demoNote")}</p>
    </main>
  );
}
