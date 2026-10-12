# Decisions Log

Decisions confirmed by the team. Background is in [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md); where they differ, this file wins.

## Competition (verified on aibuildercup.com, 2026-10-10)
- Google Cloud AI Builder Cup 2026, **BFSI** theme ("Intelligent Risk, Fraud & Financial Experiences").
- Registration and team formation close **11 Oct 2026**. Prototype submission closes **18 Oct 2026**.
- Eligibility: teams of 2–4, every member 21 or older, no students.
- Must use Gemini or Gemma, and be deployed on Google Cloud (Cloud Run or Firebase).
- Deliverables: deployed working prototype, public 3-minute demo video, proposal deck as PDF, GitHub repo, short description. All code, docs and presentations in English.
- Judging: Technical merit and GenAI use 40%, problem alignment and impact 25%, innovation 25%, UX 10%.

## Product scope (POC)
| Topic | Decision |
|---|---|
| Lifecycle | Claim process only. Enrollment and policy purchase come later. |
| Farmer AI help | (a) AI-guided claim filing, (b) policy and scheme Q&A, (c) claim status explained, (e) voice. No crop advice. |
| Languages | Hindi and English. |
| Rain alerts | The system detects heavy rain near a plot and **only notifies** the farmer. AI never files a claim on its own. |
| Reviewer dashboard | Yes. UI must be modern, clean and easy to use. |
| AI truth score | AI scores how genuine a claim looks. Above a benchmark, the reviewer sees "looks genuine" plus a one-click Fast Approve. *(Details pending; see open questions.)* |
| Channel | Phone-friendly web app built with Next.js. WhatsApp bot later. |
| Government systems | Mocked with synthetic data behind swappable interfaces. |
| Documents | Fake (synthetic) samples only. |
| Payouts | Simulated. |
| Satellite | Sentinel-1 radar flood check included. |
| Demo region | Team's choice: whichever is easiest to build. |
| Tests | 2–3 real past events plus 1 fake claim run as automated scenario tests on every run. |
| Code hosting | GitHub. The team provides the GCP project. |
| Extensibility | Must be easy to add other insurance claim types later. |
| Cost | Aim for a $0 bill. |

## Confirmed 2026-10-10
- Team is registered.
- Truth score: **every payout needs a human click**. Fast approve needs a score ≥ 80, all checks passed and at least one independent source confirming; the benchmark is adjustable in the dashboard. Fast reject is offered when the score is ≤ 30 or any check failed.
- Costs: Google AI Pro credits are already linked; the team will confirm the ₹500 budget alert.
- GitHub repo: private for now, public before submission.
- UI library: shadcn/ui, on top of Tailwind (team suggestion).

## Implementation choices (within the freedom given)
- **Region:** Bihar (Darbhanga and Araria), so documents and the app share Hindi. Bihar left PMFBY in 2018, so the demo product is labelled "parametric crop micro-insurance (demo)", not PMFBY.
- **Demo scenarios** ([research](research/demo-events.md)):
  - A: Kosi embankment breach flood, 30 Sep 2024
  - B: 211 mm rain, 19 Oct 2021
  - C: hailstorm, 20 Mar 2026
  - D: fake flood, 25 Oct 2023
- **Demo farmers live on their event date** (`demo_today`), so a 2024 claim can be filed within 72 hours.
- **Synthetic documents** use fictional bank names and are visibly marked as samples. They never imitate a real bank or a government seal.
- **Known simplification:** the radar check may use a satellite pass from after the filing date (e.g. 6 Oct for event A). In production the claim would wait for, and re-check on, the next pass.

## Deployment (2026-10-12)
- **Web:** Firebase Hosting, https://insurance-crisis.web.app. Static export, deployed with `scripts/deploy_hosting.py`.
- **API:** Cloud Run **us-central1**, https://intellisettle-api-929855157031.us-central1.run.app. It scales to zero, with at most 2 instances.
  - It moved from asia-south1 because, after the billing hold was lifted, Cloud Run in that region would not start instances for traffic (429 "no available instance"), while the same image served immediately in us-central1.
- **Photos:** private bucket `gs://insurance-crisis-claims` (us-central1, always-free tier).
- **Gemini:** runs on Vertex AI through the Cloud Run service account; no API key is stored in the cloud.
- **Checks before a demo:** run `scripts/smoke_prod.py F-101` (real flood) and `scripts/smoke_prod.py F-104` (fake), then clear the test claims.

## Open questions
- [x] App name: **IntelliSettle** (confirmed 2026-10-11). Shown in Latin script in both languages.
- [x] Git: local commits only for now; push to GitHub later.
- [x] Billing: stays off until it is required. Gemini runs on a free AI Studio key until then; deployment (Cloud Run) is the first step that needs billing.
- [ ] Damage photos for the four demo farmers: download CC-licensed photos (each approved) or team-supplied.
- [ ] GCP project details (see SETUP_GCP.md Part G).
