# Google Cloud and Firebase Setup

Do these steps once, in order. They take about 30–40 minutes. When you're done, you'll have everything in the **Part G** checklist.

**No secret API keys are needed.** The backend talks to Gemini, Firestore, Storage and Earth Engine through Google service accounts, so there are no keys to leak. If anything secret ever comes up, save it in a local `.env` file and never commit it.

---

## Part A: Billing and cost guard (Cloud Console)

Cloud Run and Firebase Storage only work when a billing account is linked, even if usage stays inside the free tier. Expected cost for this POC is about $0.

1. Open https://console.cloud.google.com and select the project.
2. Go to **Billing → Link a billing account** and link one.
3. **If you have Google AI Pro:** sign in at https://developers.google.com/program with the subscribed account, activate the developer benefits, and apply the monthly Google Cloud credit ($10/month) to the billing account from step 2.
4. Go to **Billing → Budgets & alerts → Create budget**:
   - Scope: this project only
   - Amount: ₹500 (or $5)
   - Alert thresholds: 50%, 90%, 100%

   Budget alerts send you an email. **They do not stop spending.** Services are also set to scale to zero when idle.

## Part B: Install and update tools on this PC

Run each line in a terminal:

```bash
gcloud components update
```

```bash
winget install --id=astral-sh.uv -e
```

```bash
winget install --id=GitHub.cli -e
```

`uv` installs Python 3.12 for the project automatically. Your current Python is 3.9, which is too old for some of the libraries we need. Docker is **not** needed: Cloud Build builds the containers in the cloud.

## Part C: Log gcloud in on this PC (so you can deploy from it)

```bash
gcloud auth login
```

```bash
gcloud auth application-default login
```

```bash
gcloud config set project YOUR_PROJECT_ID
```

After this, the needed APIs, IAM roles and deploys are all done from this PC with `gcloud` (see the deployment section in [DECISIONS.md](DECISIONS.md)).

## Part D: Firebase (Firebase Console)

1. Open https://console.firebase.google.com, choose **Create a project**, and pick **your existing Google Cloud project** (don't create a new one). Skip Google Analytics.
2. Click **Upgrade** (bottom-left) and select the **Blaze** plan, using the same billing account. Usage inside the free quotas costs nothing.
3. **Build → Authentication → Get started → Sign-in method**, then enable:
   - **Anonymous**: powers the "Try as demo farmer" button, so judges can use the app without a phone number.
   - **Phone**: under *Phone numbers for testing*, add 2 fictional numbers, each with a 6-digit code. Test numbers never send an SMS and cost nothing. Note them in your team notes.
   - **Email/Password**: used for reviewer (insurer staff) logins.
4. **Build → Firestore Database → Create database**: location **asia-south1 (Mumbai)**, production mode. Only the API reads and writes it; browsers never touch it directly.
5. **Build → Storage → Get started**: same location (**asia-south1**), production mode.
6. **Project settings (gear icon) → General → Your apps → Web (`</>`)**: register a web app (any name, e.g. `web`) and copy the `firebaseConfig` object it shows. These values are **not secret**, because they ship inside every Firebase web app.

## Part E: Earth Engine (for the satellite flood check)

1. Open https://code.earthengine.google.com/register.
2. Register **the same Cloud project**.
3. Choose the unpaid/noncommercial option **only if it honestly fits you**. If Earth Engine says you need a commercial plan, the radar check can switch to Copernicus Data Space, which is also free.

## Part F: GitHub

```bash
gh auth login
```

Then create an empty repo (**public**, since judges need to open it).

## Part G: Checklist

- [ ] Project ID
- [ ] Confirmation that Parts A–E are done (billing linked, budget set, Firebase on Blaze, Earth Engine registered)
- [ ] The `firebaseConfig` object (not secret; it goes in `web/.env.production.local`)
- [ ] GitHub repo URL
