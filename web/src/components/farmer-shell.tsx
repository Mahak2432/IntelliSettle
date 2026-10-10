"use client";

import { ArrowLeft, CalendarDays } from "lucide-react";
import Link from "next/link";
import { BrandMark, LangToggle } from "@/components/common";
import { ThemeToggle } from "@/components/theme-toggle";
import { longDate } from "@/lib/format";
import { useLang } from "@/lib/i18n";

export function FarmerShell({
  children,
  back,
  demoToday,
}: {
  children: React.ReactNode;
  back?: { href: string; label: string };
  demoToday?: string | null;
}) {
  const { lang, t } = useLang();
  return (
    <div className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-28 pt-4">
      <header className="flex items-center justify-between gap-3">
        {back ? (
          <Link
            href={back.href}
            className="-ml-2 flex min-h-11 items-center gap-1 rounded-xl px-2 font-semibold text-indigo hover:bg-indigo-soft"
          >
            <ArrowLeft className="size-5" aria-hidden />
            {back.label}
          </Link>
        ) : (
          <BrandMark href="/farmer/" />
        )}
        <div className="flex items-center gap-2">
          <LangToggle />
          <ThemeToggle />
        </div>
      </header>
      {demoToday && (
        <p className="mt-3 flex items-center gap-2 rounded-lg bg-indigo-soft px-3 py-1.5 text-sm text-indigo">
          <CalendarDays className="size-4" aria-hidden />
          {t("demoDate", { date: longDate(demoToday, lang) })}
        </p>
      )}
      {children}
    </div>
  );
}
