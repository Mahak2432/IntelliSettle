"use client";

import { Camera, Check, ImagePlus, Mic, Square, X } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import useSWR from "swr";
import { BigButton, Spinner } from "@/components/common";
import { FarmerShell } from "@/components/farmer-shell";
import { PerilIcon } from "@/components/peril-icon";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { isoDay, longDate } from "@/lib/format";
import { PERIL, useLang } from "@/lib/i18n";
import type { FarmerClaim, Me, Peril } from "@/lib/types";
import { guessPeril, useSpeech } from "@/lib/use-speech";
import { cn } from "@/lib/utils";

type Shot = { file: File; url: string; capturedAt?: string; lat?: number; lon?: number };
type PaperKind = "land_record" | "bank_passbook";
type Manifest = { photos: string[]; land_record?: string; bank_passbook?: string };

const PERILS: Peril[] = ["flood", "excess_rain", "hailstorm"];
const STEPS = 5;

function currentPosition(): Promise<GeolocationPosition | null> {
  if (!("geolocation" in navigator)) return Promise.resolve(null);
  return new Promise((resolve) =>
    navigator.geolocation.getCurrentPosition(resolve, () => resolve(null), { enableHighAccuracy: true, timeout: 8000 }),
  );
}

async function fileFrom(url: string): Promise<File> {
  const blob = await (await fetch(url)).blob();
  return new File([blob], url.split("/").pop() ?? "photo.jpg", { type: blob.type || "image/jpeg" });
}

function NewClaim() {
  const { lang, t } = useLang();
  const router = useRouter();
  const params = useSearchParams();
  const { data: me } = useSWR<Me>("/api/me");
  const farmer = me?.farmer;
  const policy = me?.policies?.[0];
  const { data: manifest } = useSWR<Manifest | null>(
    farmer ? `/demo/${farmer.farmer_id}/manifest.json` : null,
    (url: string) => fetch(url).then((r) => (r.ok ? r.json() : null)),
  );

  const [step, setStep] = useState(0);
  const [peril, setPeril] = useState<Peril | null>((params.get("peril") as Peril) || null);
  const [lossDate, setLossDate] = useState<string | null>(params.get("date"));
  const [shots, setShots] = useState<Shot[]>([]);
  const [papers, setPapers] = useState<Partial<Record<PaperKind, Shot>>>({});
  const [description, setDescription] = useState("");
  const [sending, setSending] = useState(false);
  const photoInput = useRef<HTMLInputElement>(null);
  const paperInput = useRef<HTMLInputElement>(null);
  const paperKind = useRef<PaperKind>("land_record");

  const speech = useSpeech(lang, (text) => {
    setDescription((d) => (d ? `${d} ${text}` : text));
    const guess = guessPeril(text);
    if (guess) setPeril(guess);
  });

  const today = farmer?.demo_today ?? isoDay(new Date());
  useEffect(() => () => shots.forEach((s) => URL.revokeObjectURL(s.url)), []); // eslint-disable-line react-hooks/exhaustive-deps

  async function addPhotos(files: FileList | null) {
    if (!files?.length) return;
    const where = await currentPosition();
    const added = Array.from(files).map((file) => ({
      file,
      url: URL.createObjectURL(file),
      capturedAt: new Date().toISOString(),
      lat: where?.coords.latitude,
      lon: where?.coords.longitude,
    }));
    setShots((s) => [...s, ...added].slice(0, 6));
  }

  async function useSamplePhotos() {
    if (!manifest || !farmer) return;
    const base = `/demo/${farmer.farmer_id}/`;
    const files = await Promise.all(manifest.photos.map((p) => fileFrom(base + p)));
    // Sample photos carry their own EXIF time and GPS, so no device metadata is attached.
    setShots(files.map((file) => ({ file, url: URL.createObjectURL(file) })));
    const docs: Partial<Record<PaperKind, Shot>> = {};
    for (const kind of ["land_record", "bank_passbook"] as const) {
      const name = manifest[kind];
      if (name) {
        const file = await fileFrom(base + name);
        docs[kind] = { file, url: URL.createObjectURL(file) };
      }
    }
    setPapers(docs);
  }

  function addPaper(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setPapers((p) => ({ ...p, [paperKind.current]: { file, url: URL.createObjectURL(file) } }));
  }

  async function send() {
    if (!policy || !peril || !lossDate) return;
    setSending(true);
    const form = new FormData();
    form.set("policy_no", policy.policy_no);
    form.set("peril", peril);
    form.set("loss_date", lossDate);
    form.set("description", description);
    form.set("language", lang);
    const located = shots.find((s) => s.lat !== undefined);
    if (located?.lat !== undefined && located.lon !== undefined) {
      form.set("filed_lat", String(located.lat));
      form.set("filed_lon", String(located.lon));
    }
    form.set("photo_meta", JSON.stringify(shots.map((s) => ({ captured_at: s.capturedAt, lat: s.lat, lon: s.lon }))));
    shots.forEach((s) => form.append("photos", s.file));
    for (const kind of ["land_record", "bank_passbook"] as const) {
      const paper = papers[kind];
      if (paper) form.set(kind, paper.file);
    }
    try {
      const claim = await api<FarmerClaim>("/api/claims", { method: "POST", form });
      router.replace(`/farmer/claim/?id=${claim.claim_id}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : String(e));
      setSending(false);
    }
  }

  if (!me) {
    return (
      <FarmerShell>
        <div className="mt-10"><Spinner /></div>
      </FarmerShell>
    );
  }

  const canNext = [peril !== null, lossDate !== null, shots.length > 0, true, true][step];
  const dateChoices = [
    { label: t("today"), value: today },
    { label: t("yesterday"), value: isoDay(today, -1) },
    { label: t("dayBefore"), value: isoDay(today, -2) },
  ];

  return (
    <FarmerShell back={{ href: "/farmer/", label: t("back") }} demoToday={farmer?.demo_today}>
      <Progress value={((step + 1) / STEPS) * 100} className="mt-4 h-2" aria-label={`${step + 1} / ${STEPS}`} />

      {step === 0 && (
        <section className="mt-6">
          <h1 className="text-3xl font-bold text-indigo">{t("whatHappened")}</h1>
          <div className="mt-5 grid gap-3">
            {PERILS.map((p) => (
              <button
                key={p}
                onClick={() => setPeril(p)}
                aria-pressed={peril === p}
                className={cn(
                  "flex min-h-20 items-center gap-4 rounded-[var(--radius-touch)] border-2 bg-surface px-5 text-left text-xl font-semibold transition-colors",
                  peril === p ? "border-indigo bg-indigo-soft text-indigo" : "border-transparent",
                )}
              >
                <PerilIcon peril={p} className="size-9" />
                <span className="flex-1">{PERIL[p][lang]}</span>
                {peril === p && <Check className="size-6" aria-hidden />}
              </button>
            ))}
          </div>

          <div className="mt-8 flex flex-col items-center gap-3 text-center">
            <button
              onClick={speech.listening ? speech.stop : speech.start}
              className={cn(
                "grid size-20 place-items-center rounded-full bg-indigo text-white",
                speech.listening && "listening",
              )}
              aria-label={speech.listening ? t("stopListening") : t("speak")}
            >
              {speech.listening ? <Square className="size-7" /> : <Mic className="size-9" />}
            </button>
            <p className="font-semibold text-indigo">{speech.listening ? t("listening") : t("speak")}</p>
            {!speech.supported && <p className="text-sm text-slate">{t("voiceUnsupported")}</p>}
            {(speech.interim || description) && (
              <p className="max-w-md rounded-2xl bg-surface px-4 py-3 text-left italic">{speech.interim || description}</p>
            )}
          </div>
        </section>
      )}

      {step === 1 && (
        <section className="mt-6">
          <h1 className="text-3xl font-bold text-indigo">{t("whenHappened")}</h1>
          <div className="mt-5 grid gap-3">
            {dateChoices.map((d) => (
              <button
                key={d.value}
                onClick={() => setLossDate(d.value)}
                aria-pressed={lossDate === d.value}
                className={cn(
                  "flex min-h-16 items-center justify-between rounded-[var(--radius-touch)] border-2 bg-surface px-5 text-left text-xl font-semibold",
                  lossDate === d.value ? "border-indigo bg-indigo-soft text-indigo" : "border-transparent",
                )}
              >
                <span>{d.label}</span>
                <span className="text-base font-normal text-slate">{longDate(d.value, lang)}</span>
              </button>
            ))}
            <label className="flex min-h-16 items-center justify-between gap-3 rounded-[var(--radius-touch)] bg-surface px-5 text-lg">
              <span>{t("otherDate")}</span>
              <input
                type="date"
                max={today}
                value={lossDate && !dateChoices.some((d) => d.value === lossDate) ? lossDate : ""}
                onChange={(e) => setLossDate(e.target.value || null)}
                className="rounded-lg border border-line px-2 py-1"
              />
            </label>
          </div>
          <p className="mt-4 text-slate">{t("windowNote")}</p>
        </section>
      )}

      {step === 2 && (
        <section className="mt-6">
          <h1 className="text-3xl font-bold text-indigo">{t("takePhotos")}</h1>
          <p className="mt-2 text-lg">{t("photosHint")}</p>
          <input
            ref={photoInput}
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            hidden
            onChange={(e) => {
              addPhotos(e.target.files);
              e.target.value = "";
            }}
          />
          {shots.length > 0 && (
            <ul className="mt-5 grid grid-cols-3 gap-2">
              {shots.map((s, i) => (
                <li key={s.url} className="relative aspect-square overflow-hidden rounded-2xl bg-muted">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={s.url} alt="" className="size-full object-cover" />
                  <button
                    onClick={() => setShots((all) => all.filter((_, j) => j !== i))}
                    className="absolute right-1 top-1 grid size-9 place-items-center rounded-full bg-ink/70 text-white"
                    aria-label={t("removePhoto")}
                  >
                    <X className="size-5" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <BigButton tone="secondary" className="mt-5 w-full" onClick={() => photoInput.current?.click()}>
            <Camera className="size-6" aria-hidden />
            {shots.length ? t("addPhoto") : t("takePhoto")}
          </BigButton>
          {manifest && manifest.photos.length > 0 && (
            <button onClick={useSamplePhotos} className="mt-3 min-h-11 w-full font-semibold text-indigo underline">
              {t("useSamples")}
            </button>
          )}
          <p className="mt-4 text-sm text-slate">{t("locationHint")}</p>
        </section>
      )}

      {step === 3 && (
        <section className="mt-6">
          <h1 className="text-3xl font-bold text-indigo">{t("papers")}</h1>
          <p className="mt-2 text-lg">{t("papersHint")}</p>
          <input
            ref={paperInput}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              addPaper(e.target.files);
              e.target.value = "";
            }}
          />
          <div className="mt-5 grid gap-3">
            {(["land_record", "bank_passbook"] as const).map((kind) => (
              <div key={kind} className="flex items-center gap-4 rounded-[var(--radius-touch)] bg-surface p-3">
                <div className="grid size-20 shrink-0 place-items-center overflow-hidden rounded-xl bg-muted">
                  {papers[kind] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={papers[kind]!.url} alt="" className="size-full object-cover" />
                  ) : (
                    <ImagePlus className="size-7 text-slate" aria-hidden />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-lg font-semibold">{kind === "land_record" ? t("landRecord") : t("passbook")}</p>
                  <button
                    onClick={() => {
                      paperKind.current = kind;
                      paperInput.current?.click();
                    }}
                    className="mt-1 min-h-11 font-semibold text-indigo underline"
                  >
                    {papers[kind] ? t("retake") : t("addPaper")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {step === 4 && peril && lossDate && (
        <section className="mt-6">
          <h1 className="text-3xl font-bold text-indigo">{t("checkAndSend")}</h1>
          <dl className="mt-5 divide-y divide-line rounded-[var(--radius-touch)] bg-surface px-5">
            {[
              [t("lossType"), PERIL[peril][lang]],
              [t("lossDate"), longDate(lossDate, lang)],
              [t("photos"), String(shots.length)],
              [t("documents"), String(Object.keys(papers).length || t("none"))],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4 py-3 text-lg">
                <dt className="text-slate">{k}</dt>
                <dd className="font-semibold">{v}</dd>
              </div>
            ))}
          </dl>
          <label className="mt-5 block text-lg font-semibold" htmlFor="describe">
            {t("describe")}
          </label>
          <Textarea
            id="describe"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t("describePlaceholder")}
            className="mt-2 min-h-28 bg-surface text-lg"
          />
        </section>
      )}

      <div className="fixed inset-x-0 bottom-0 border-t border-line bg-page/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-xl gap-3">
          {step > 0 && (
            <BigButton tone="secondary" onClick={() => setStep(step - 1)} disabled={sending}>
              {t("back")}
            </BigButton>
          )}
          {step < STEPS - 1 ? (
            <BigButton className="flex-1" disabled={!canNext} onClick={() => setStep(step + 1)}>
              {step === 3 && Object.keys(papers).length === 0 ? t("skip") : t("next")}
            </BigButton>
          ) : (
            <BigButton className="flex-1" busy={sending} onClick={send}>
              {sending ? t("sending") : t("sendClaim")}
            </BigButton>
          )}
        </div>
      </div>
    </FarmerShell>
  );
}

export default function NewClaimPage() {
  return (
    <Suspense>
      <NewClaim />
    </Suspense>
  );
}
