import type { Lang } from "@/lib/types";

const locale = (lang: Lang) => (lang === "hi" ? "hi-IN" : "en-IN");

export function rupees(amount: number, lang: Lang = "en"): string {
  return amount.toLocaleString(locale(lang), { maximumFractionDigits: 0 });
}

export function longDate(iso: string, lang: Lang = "en"): string {
  return new Date(iso.length === 10 ? `${iso}T00:00:00+05:30` : iso).toLocaleDateString(locale(lang), {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

export function shortDateTime(iso: string, lang: Lang = "en"): string {
  return new Date(iso).toLocaleString(locale(lang), {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  });
}

/** Local calendar date (IST) as YYYY-MM-DD, offset by whole days. */
export function isoDay(base: string | Date, offsetDays = 0): string {
  const d = typeof base === "string" ? new Date(`${base}T12:00:00+05:30`) : new Date(base);
  d.setUTCDate(d.getUTCDate() + offsetDays);
  return d.toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
}
