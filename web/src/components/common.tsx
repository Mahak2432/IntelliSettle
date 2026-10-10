"use client";

import { Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

type Tone = "primary" | "secondary" | "approve" | "reject";

const TONES: Record<Tone, string> = {
  primary: "bg-indigo text-white hover:bg-indigo-hover",
  secondary: "border-2 border-indigo/20 bg-surface text-indigo hover:border-indigo/50 hover:bg-surface",
  approve: "bg-paddy text-white hover:bg-paddy/90",
  reject: "bg-chilli text-white hover:bg-chilli/90",
};

/** Large touch target for farmers and the officer's decision buttons. */
export function BigButton({
  tone = "primary",
  busy = false,
  className,
  children,
  disabled,
  ...props
}: React.ComponentProps<typeof Button> & { tone?: Tone; busy?: boolean }) {
  return (
    <Button
      {...props}
      disabled={disabled || busy}
      className={cn("h-14 rounded-[var(--radius-touch)] px-6 text-lg font-semibold gap-2", TONES[tone], className)}
    >
      {busy && <Loader2 className="size-5 animate-spin" aria-hidden />}
      {children}
    </Button>
  );
}

export function LangToggle({ className }: { className?: string }) {
  const { lang, setLang, t } = useLang();
  return (
    <Button
      variant="outline"
      onClick={() => setLang(lang === "hi" ? "en" : "hi")}
      className={cn("h-10 rounded-full bg-surface px-4 text-sm font-semibold text-indigo", className)}
      lang={lang === "hi" ? "en" : "hi"}
    >
      {t("switchLang")}
    </Button>
  );
}

export function BrandMark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="w-wide text-xl font-bold tracking-tight text-indigo">
      IntelliSettle
    </Link>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 text-slate">
      <Loader2 className="size-5 animate-spin" aria-hidden />
      {label && <span>{label}</span>}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <p role="alert" className="rounded-xl bg-chilli-soft px-4 py-3 text-chilli">
      {message}
    </p>
  );
}
