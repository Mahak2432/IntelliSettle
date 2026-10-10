// Mirrors api/src/claims_api/domain/models.py and api/views.py.

export type Lang = "hi" | "en";
export type Peril = "flood" | "excess_rain" | "hailstorm";
export type ClaimStatus =
  | "submitted"
  | "assessing"
  | "ready_for_review"
  | "approved"
  | "paid"
  | "rejected"
  | "appealed";
export type Verdict = "looks_genuine" | "needs_review" | "looks_suspicious";
export type CheckStatus = "pass" | "fail" | "unknown";
export type Signal = "supports" | "contradicts" | "inconclusive" | "unavailable";

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface Farmer {
  farmer_id: string;
  name: string;
  name_hi: string;
  father_name: string;
  phone: string;
  preferred_language: Lang;
  bank: { account_holder: string; account_masked: string; ifsc: string; bank_name: string };
  demo_today?: string | null;
}

export interface Plot {
  khasra_no: string;
  village: string;
  block: string;
  district: string;
  state: string;
  area_ha: number;
  location: GeoPoint;
}

export interface Policy {
  policy_no: string;
  product_code: string;
  farmer_id: string;
  insurer: string;
  scheme: string;
  season: string;
  crop: string;
  plot: Plot;
  insured_area_ha: number;
  sum_insured_inr: number;
  cover_start: string;
  cover_end: string;
  perils: Peril[];
}

export interface Persona {
  farmer_id: string;
  name: string;
  name_hi: string;
  village: string;
  district: string;
  crop_en: string;
  crop_hi: string;
  story_en: string;
  story_hi: string;
  demo_today: string;
  peril: Peril;
}

export interface RainAlert {
  policy_no: string;
  date: string;
  rain_mm: number;
  category_en: string;
  category_hi: string;
}

export interface Me {
  role: "farmer" | "reviewer";
  farmer?: Farmer;
  policies?: Policy[];
  alerts?: RainAlert[];
}

export interface TimelineEvent {
  at: string;
  status: ClaimStatus;
  note: string;
}

export interface PayoutRecord {
  amount_inr: number;
  reference: string;
  rail: string;
  account_masked: string;
  paid_at: string;
}

export interface FarmerClaim {
  claim_id: string;
  policy_no: string;
  peril: Peril;
  loss_date: string;
  submitted_at: string;
  status: ClaimStatus;
  description: string;
  message_en: string | null;
  message_hi: string | null;
  decision_reason: string | null;
  payout: PayoutRecord | null;
  appeal: { message: string; filed_at: string } | null;
  can_appeal: boolean;
  timeline: TimelineEvent[];
  photo_count: number;
}

export interface CheckResult {
  code: string;
  label: string;
  status: CheckStatus;
  detail: string;
  data: Record<string, unknown>;
}

export interface EvidenceItem {
  source: string;
  label: string;
  signal: Signal;
  summary: string;
  metrics: Record<string, unknown>;
  citations: { title: string; url: string; published?: string | null }[];
  independent: boolean;
  visuals: Record<string, string>;
}

export interface Assessment {
  product_code: string;
  checks: CheckResult[];
  evidence: EvidenceItem[];
  truth: {
    score: number;
    reasons: string[];
    red_flags: string[];
    summary_en: string;
    summary_hi: string;
    model: string;
    fallback: boolean;
  };
  verdict: Verdict;
  payout_quote: { sum_insured_inr: number; payout_percent: number; amount_inr: number; basis: string };
  thresholds: Thresholds;
  assessed_at: string;
}

export interface Thresholds {
  genuine_at_or_above: number;
  suspicious_at_or_below: number;
}

export interface ExtractedField {
  value: string | null;
  confidence: number;
}

export interface Claim {
  claim_id: string;
  policy_no: string;
  farmer_id: string;
  peril: Peril;
  loss_date: string;
  submitted_at: string;
  description: string;
  language: Lang;
  photos: {
    photo_id: string;
    exif_captured_at: string | null;
    exif_location: GeoPoint | null;
    device_captured_at: string | null;
    device_location: GeoPoint | null;
  }[];
  documents: {
    document_id: string;
    kind: "land_record" | "bank_passbook" | "policy";
    extraction: { kind: string; language: string | null; fields: Record<string, ExtractedField>; model: string } | null;
  }[];
  status: ClaimStatus;
  assessment: Assessment | null;
  decisions: {
    action: "approve" | "reject";
    fast_lane: boolean;
    reason: string | null;
    reviewer_id: string;
    decided_at: string;
    verdict_at_decision: Verdict;
    score_at_decision: number;
  }[];
  payout: PayoutRecord | null;
  appeal: { message: string; filed_at: string } | null;
  timeline: TimelineEvent[];
}

export interface ReviewClaim {
  claim: Claim;
  farmer: Farmer;
  policy: Policy;
}

export interface QueueItem {
  claim_id: string;
  farmer_name: string;
  village: string;
  district: string;
  crop: string;
  peril: Peril;
  loss_date: string;
  submitted_at: string;
  status: ClaimStatus;
  score: number | null;
  verdict: Verdict | null;
  amount_inr: number | null;
  appealed: boolean;
}
