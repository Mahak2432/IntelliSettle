"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { Lang } from "@/lib/types";

/* Minimal typing for the browser Web Speech API (Chrome on Android supports hi-IN). */
interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start(): void;
  stop(): void;
  onresult: ((e: { resultIndex: number; results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null;
  onend: (() => void) | null;
  onerror: ((e: { error: string }) => void) | null;
}

function recognitionClass(): (new () => Recognition) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as Record<string, unknown>;
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as (new () => Recognition) | null;
}

const noSubscribe = () => () => {};

export function useSpeech(lang: Lang, onFinal: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const supported = useSyncExternalStore(noSubscribe, () => recognitionClass() !== null, () => true);
  const ref = useRef<Recognition | null>(null);
  const onFinalRef = useRef(onFinal);
  useEffect(() => {
    onFinalRef.current = onFinal;
  });

  const stop = useCallback(() => ref.current?.stop(), []);

  const start = useCallback(() => {
    const Ctor = recognitionClass();
    if (!Ctor) return;
    const rec = new Ctor();
    rec.lang = lang === "hi" ? "hi-IN" : "en-IN";
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (e) => {
      let finalText = "";
      let partial = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalText += r[0].transcript;
        else partial += r[0].transcript;
      }
      setInterim(partial);
      if (finalText) onFinalRef.current(finalText.trim());
    };
    rec.onend = () => {
      setListening(false);
      setInterim("");
    };
    rec.onerror = () => setListening(false);
    ref.current = rec;
    rec.start();
    setListening(true);
  }, [lang]);

  return { listening, interim, supported, start, stop };
}

/** Rough keyword match so a spoken description can pre-select the type of damage. */
export function guessPeril(text: string): "flood" | "excess_rain" | "hailstorm" | null {
  const t = text.toLowerCase();
  if (/(ओल|ओला|hail)/.test(t)) return "hailstorm";
  if (/(बाढ़|बाढ|डूब|जलभराव|पानी भर|flood|waterlog)/.test(t)) return "flood";
  if (/(बारिश|वर्षा|बरसात|rain)/.test(t)) return "excess_rain";
  return null;
}
