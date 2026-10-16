"use client";

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore } from "react";
import type { ClaimStatus, Lang, Peril, Verdict } from "@/lib/types";

const en = {
  tagline: "Crop loss claims, checked in hours instead of months.",
  heroSub: "Rainfall, satellite radar, local news and land records check every claim. A claims officer approves in one click.",
  howTitle: "How a claim moves",
  step1: "The farmer reports the loss by voice, with photos from the field.",
  step2: "AI checks rainfall at the plot, radar flood images, news and the farmer's papers.",
  step3: "An officer reviews the evidence and approves; the money goes straight to the bank account.",
  fraudTest: "Fraud test",
  whoAreYou: "Who is using the app?",
  farmer: "Farmer",
  officer: "Claims officer",
  demoNote: "This is a demo with sample farmers. No real money moves.",
  pickFarmer: "Pick a farmer to continue",
  openDesk: "Open the review desk",
  officerBlurb: "Review AI-checked claims, see the evidence and approve in one click.",
  switchLang: "हिन्दी",

  hello: "Namaste, {name}",
  demoDate: "Demo date: {date}",
  yourCover: "Your crop cover",
  coverAmount: "Cover amount",
  coveredTill: "Covered till {date}",
  plot: "Plot {khasra}, {village}",
  reportLoss: "Report crop loss",
  yourClaims: "Your claims",
  noClaims: "No claims yet. If your crop is damaged, report it within 72 hours.",
  askHelp: "Ask for help",
  changeUser: "Change user",
  alertTitle: "Heavy rain near your field",
  alertBody: "{mm} mm of rain fell near your field on {date} ({category}). If your crop is damaged, report it.",

  whatHappened: "What happened to your crop?",
  speak: "Tell by speaking",
  listening: "Listening. Speak now",
  stopListening: "Stop",
  voiceUnsupported: "Voice input is not available in this browser. Please type instead.",
  comingSoon: "Coming soon",
  resetDemo: "Start the demo over",
  resetDone: "Your demo claims were cleared. You can start fresh.",
  voiceSoon: "Telling us by voice is coming soon. For now, tap the type of damage above.",
  helpSoon: "The voice help assistant is coming soon.",
  whenHappened: "When did it happen?",
  today: "Today",
  yesterday: "Yesterday",
  dayBefore: "2 days ago",
  otherDate: "Another date",
  windowNote: "Report within 72 hours of the damage. Older losses can't be claimed.",
  takePhotos: "Take photos of the damage",
  photosHint: "Stand in your field and take 2 or 3 photos of the damaged crop.",
  takePhoto: "Take photo",
  addPhoto: "Add another photo",
  useSamples: "Use sample photos (demo)",
  removePhoto: "Remove photo",
  locationHint: "Allow location access so we can confirm the photos were taken in your field.",
  papers: "Photos of your papers",
  papersHint: "A clear photo of your land record and bank passbook helps us pay faster. You can skip this.",
  landRecord: "Land record (Khatiyan)",
  passbook: "Bank passbook",
  addPaper: "Take photo",
  retake: "Retake",
  checkAndSend: "Check and send",
  describe: "Anything else about the damage? (optional)",
  describePlaceholder: "For example: the whole field is under knee-deep water",
  sendClaim: "Send claim",
  sending: "Sending…",
  next: "Next",
  back: "Back",
  skip: "Skip",
  lossType: "Damage",
  lossDate: "Date",
  photos: "Photos",
  documents: "Papers",
  none: "None",

  claimNo: "Claim {id}",
  whatWeChecked: "What we checked",
  checking: "We are checking your claim against weather data, satellite radar and local news. This usually takes a minute.",
  sentTo: "₹{amount} sent to account {account}",
  reference: "Reference {ref}",
  reason: "Reason",
  appealTitle: "Think we got it wrong?",
  appealPlaceholder: "Tell us what we missed",
  sendAppeal: "Send appeal",
  appealSent: "Appeal sent. A senior officer will look again.",
  backHome: "Back to home",

  helpTitle: "Ask anything about your claim",
  helpPlaceholder: "Type your question",
  send: "Send",
};

type Dict = typeof en;

const hi: Dict = {
  tagline: "फसल नुकसान के दावे की जाँच, महीनों नहीं घंटों में।",
  heroSub: "हर दावे की जाँच बारिश के आँकड़ों, सैटेलाइट रडार, स्थानीय ख़बरों और भूमि रिकॉर्ड से होती है। दावा अधिकारी एक क्लिक में मंज़ूरी देते हैं।",
  howTitle: "दावा कैसे आगे बढ़ता है",
  step1: "किसान बोलकर नुकसान बताते हैं और खेत की फ़ोटो भेजते हैं।",
  step2: "AI खेत पर हुई बारिश, रडार से बाढ़ की तस्वीरें, ख़बरें और किसान के कागज़ात जाँचता है।",
  step3: "अधिकारी सबूत देखकर मंज़ूरी देते हैं और पैसा सीधे बैंक खाते में जाता है।",
  fraudTest: "धोखाधड़ी जाँच",
  whoAreYou: "ऐप कौन इस्तेमाल कर रहा है?",
  farmer: "किसान",
  officer: "दावा अधिकारी",
  demoNote: "यह नमूना किसानों के साथ डेमो है। असली पैसा नहीं भेजा जाता।",
  pickFarmer: "आगे बढ़ने के लिए एक किसान चुनें",
  openDesk: "समीक्षा डेस्क खोलें",
  officerBlurb: "AI से जाँचे गए दावे देखें, सबूत परखें और एक क्लिक में मंज़ूरी दें।",
  switchLang: "English",

  hello: "नमस्ते, {name}",
  demoDate: "डेमो तारीख: {date}",
  yourCover: "आपका फसल बीमा",
  coverAmount: "बीमा राशि",
  coveredTill: "{date} तक सुरक्षा",
  plot: "खसरा {khasra}, {village}",
  reportLoss: "फसल नुकसान बताएं",
  yourClaims: "आपके दावे",
  noClaims: "अभी कोई दावा नहीं है। फसल खराब हो तो 72 घंटे के अंदर बताएं।",
  askHelp: "मदद लें",
  changeUser: "उपयोगकर्ता बदलें",
  alertTitle: "आपके खेत के पास भारी बारिश",
  alertBody: "{date} को आपके खेत के पास {mm} मिमी बारिश हुई ({category})। फसल को नुकसान हुआ हो तो बताएं।",

  whatHappened: "आपकी फसल को क्या हुआ?",
  speak: "बोलकर बताइए",
  listening: "सुन रहे हैं, अब बोलिए",
  stopListening: "रोकें",
  voiceUnsupported: "इस ब्राउज़र में बोलकर बताने की सुविधा नहीं है। कृपया लिखकर बताइए।",
  comingSoon: "जल्द आ रहा है",
  resetDemo: "डेमो फिर से शुरू करें",
  resetDone: "आपके डेमो दावे हटा दिए गए। अब नए सिरे से शुरू करें।",
  voiceSoon: "बोलकर बताने की सुविधा जल्द आ रही है। अभी ऊपर नुकसान का प्रकार चुनें।",
  helpSoon: "बोलकर मदद देने वाला सहायक जल्द आ रहा है।",
  whenHappened: "यह कब हुआ?",
  today: "आज",
  yesterday: "कल",
  dayBefore: "परसों",
  otherDate: "दूसरी तारीख",
  windowNote: "नुकसान के 72 घंटे के अंदर बताएं। इससे पुराने नुकसान का दावा नहीं हो सकता।",
  takePhotos: "नुकसान की फ़ोटो लें",
  photosHint: "अपने खेत में खड़े होकर खराब फसल की 2-3 फ़ोटो लें।",
  takePhoto: "फ़ोटो लें",
  addPhoto: "एक और फ़ोटो लें",
  useSamples: "नमूना फ़ोटो लगाएं (डेमो)",
  removePhoto: "फ़ोटो हटाएं",
  locationHint: "लोकेशन की अनुमति दें, ताकि पता चले कि फ़ोटो आपके खेत में ली गई हैं।",
  papers: "कागज़ात की फ़ोटो",
  papersHint: "खतियान और बैंक पासबुक की साफ़ फ़ोटो से भुगतान जल्दी होता है। चाहें तो छोड़ सकते हैं।",
  landRecord: "खतियान (भूमि रिकॉर्ड)",
  passbook: "बैंक पासबुक",
  addPaper: "फ़ोटो लें",
  retake: "दोबारा लें",
  checkAndSend: "जाँचें और भेजें",
  describe: "नुकसान के बारे में और कुछ? (ज़रूरी नहीं)",
  describePlaceholder: "जैसे: पूरे खेत में घुटनों तक पानी भरा है",
  sendClaim: "दावा भेजें",
  sending: "भेज रहे हैं…",
  next: "आगे",
  back: "पीछे",
  skip: "छोड़ें",
  lossType: "नुकसान",
  lossDate: "तारीख",
  photos: "फ़ोटो",
  documents: "कागज़ात",
  none: "कोई नहीं",

  claimNo: "दावा {id}",
  whatWeChecked: "हमने क्या जाँचा",
  checking: "हम आपके दावे को मौसम के आँकड़ों, सैटेलाइट रडार और स्थानीय ख़बरों से जाँच रहे हैं। इसमें आमतौर पर एक मिनट लगता है।",
  sentTo: "₹{amount} खाता {account} में भेजे गए",
  reference: "संदर्भ संख्या {ref}",
  reason: "कारण",
  appealTitle: "क्या हमसे गलती हुई?",
  appealPlaceholder: "बताइए हमसे क्या छूट गया",
  sendAppeal: "अपील भेजें",
  appealSent: "अपील भेज दी गई। एक वरिष्ठ अधिकारी दोबारा देखेंगे।",
  backHome: "होम पर जाएं",

  helpTitle: "अपने दावे के बारे में कुछ भी पूछें",
  helpPlaceholder: "अपना सवाल लिखें",
  send: "भेजें",
};

export const PERIL: Record<Peril, Record<Lang, string>> = {
  flood: { en: "Flood or waterlogging", hi: "बाढ़ या जलभराव" },
  excess_rain: { en: "Heavy rain", hi: "भारी बारिश" },
  hailstorm: { en: "Hailstorm", hi: "ओलावृष्टि" },
};

export const STATUS: Record<ClaimStatus, Record<Lang, string>> = {
  submitted: { en: "Received", hi: "मिल गया" },
  assessing: { en: "Being checked", hi: "जाँच हो रही है" },
  ready_for_review: { en: "With claims officer", hi: "दावा अधिकारी के पास" },
  approved: { en: "Approved", hi: "मंज़ूर" },
  paid: { en: "Money sent", hi: "पैसा भेज दिया गया" },
  rejected: { en: "Not approved", hi: "मंज़ूर नहीं हुआ" },
  appealed: { en: "Appeal under review", hi: "अपील की जाँच हो रही है" },
};

export const VERDICT: Record<Verdict, string> = {
  looks_genuine: "Looks genuine",
  needs_review: "Needs review",
  looks_suspicious: "Looks suspicious",
};

const dictionaries: Record<Lang, Dict> = { en, hi };
const LANG_KEY = "kk-lang";

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (key: keyof Dict, vars?: Record<string, string | number>) => string };
const LangContext = createContext<Ctx | null>(null);

// The saved language lives in localStorage; useSyncExternalStore reads it without a hydration mismatch.
const listeners = new Set<() => void>();
let memoryLang: Lang = "hi";

function readLang(): Lang {
  try {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === "en" || saved === "hi") return saved;
  } catch {}
  return memoryLang;
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function LangProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(subscribe, readLang, () => "hi" as Lang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    memoryLang = l;
    try {
      localStorage.setItem(LANG_KEY, l);
    } catch {}
    listeners.forEach((notify) => notify());
  }, []);

  const t = useCallback(
    (key: keyof Dict, vars?: Record<string, string | number>) =>
      Object.entries(vars ?? {}).reduce(
        (text, [k, v]) => text.replaceAll(`{${k}}`, String(v)),
        dictionaries[lang][key],
      ),
    [lang],
  );

  return <LangContext.Provider value={{ lang, setLang, t }}>{children}</LangContext.Provider>;
}

export function useLang(): Ctx {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used inside LangProvider");
  return ctx;
}
