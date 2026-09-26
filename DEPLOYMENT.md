# MailDigest — Deployment Guide

**Cost: ₹0/month — no credit card needed anywhere**

| Service  | Platform    | Cost |
|----------|-------------|------|
| Frontend | Vercel      | Free |
| Backend  | Render      | Free |
| Database | Supabase    | Free |
| AI       | Groq API    | Free |
| Gmail    | Google Cloud | Free |
| Outlook  | Microsoft 365 Dev Program | Free |

---

## Before you start

- GitHub account
- Google account
- Microsoft account (outlook.com / hotmail.com / live.com)

---

## STEP 1 — Push code to GitHub

Run this inside the `maildigest` folder:

```bash
git init
git add .
git commit -m "initial commit"
```

Go to [github.com/new](https://github.com/new) → create a private repo named `maildigest` → then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/maildigest.git
git branch -M main
git push -u origin main
```

---

## STEP 2 — Supabase (Database)

1. Go to [supabase.com](https://supabase.com) → Sign up → **New project**
2. Name: `maildigest` | Region: **Singapore** | Set a strong password
3. Wait ~2 minutes for provisioning
4. Left sidebar → **SQL Editor** → paste the full contents of `supabase/migrations/001_initial_schema.sql` → click **Run**
5. Go to **Project Settings → API** → copy these 4 values:

```
Project URL       →  SUPABASE_URL
anon public key   →  NEXT_PUBLIC_SUPABASE_ANON_KEY
service_role key  →  SUPABASE_SERVICE_KEY
JWT Secret        →  SUPABASE_JWT_SECRET
```

---

## STEP 3 — Groq API (Free AI)

1. Go to [console.groq.com](https://console.groq.com) → Sign up (free, **no credit card**)
2. **API Keys → Create API Key** → copy it

```
gsk_xxxxxxxx  →  GROQ_API_KEY
```

Free tier: 14,400 requests/day. More than enough for personal email use.

---

## STEP 4 — Gmail OAuth

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Top bar → **Select a project → New Project** → name it `maildigest` → Create
3. Search bar → type **Gmail API** → click Enable
4. Left menu → **OAuth consent screen**
   - User Type: **External** → Create
   - App name: `MailDigest`
   - User support email: your email
   - Developer contact email: your email
   - Save and Continue
   - **Scopes** → Add or remove scopes → search and tick:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/userinfo.email`
   - Save and Continue
   - **Test users** → Add Users → add all your Gmail addresses you want to connect
   - Save and Continue → Back to Dashboard
5. Left menu → **Credentials → + Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Name: `maildigest`
   - Authorized redirect URIs → **Add URI**:
     ```
     https://maildigest-backend.onrender.com/auth/gmail/callback
     ```
     *(if your Render URL is different, update this after Step 6)*
   - Create
6. Copy:

```
Client ID      →  GMAIL_CLIENT_ID
Client Secret  →  GMAIL_CLIENT_SECRET
```

---

## STEP 5 — Outlook OAuth (No Credit Card)

> Azure Portal requires a credit card. Use the **Microsoft 365 Developer Program** instead — it is completely free and gives you a full developer tenant with no payment needed.

### 5a — Get a free Microsoft 365 Dev tenant

1. Go to [developer.microsoft.com/microsoft-365/dev-program](https://developer.microsoft.com/en-us/microsoft-365/dev-program)
2. Click **Join now** → sign in with your Microsoft account
3. Fill in the form → choose **Personal projects** → Instant sandbox
4. This gives you a free `@onmicrosoft.com` developer account and full Azure access — **no credit card**

### 5b — Register your app (using dev tenant)

1. Go to [aad.portal.azure.com](https://aad.portal.azure.com) → sign in with your new dev tenant account
2. Search **App registrations** → **New registration**
   - Name: `MailDigest`
   - Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
   - Redirect URI: Web →
     ```
     https://maildigest-backend.onrender.com/auth/outlook/callback
     ```
   - Register

3. Left menu → **API permissions → Add a permission → Microsoft Graph → Delegated**
   - Add: `Mail.Read`
   - Add: `User.Read`
   - Add: `offline_access`
   - Click **Grant admin consent** → Yes

4. Left menu → **Certificates & secrets → New client secret**
   - Description: `maildigest`
   - Expires: **24 months**
   - Add → **copy the Value immediately** (disappears when you leave the page)

5. Left menu → **Overview** → copy:

```
Application (client) ID  →  OUTLOOK_CLIENT_ID
Secret Value             →  OUTLOOK_CLIENT_SECRET
```

### No Outlook? That's fine too.

If you only use Gmail accounts, you can skip Step 5 entirely. MailDigest works perfectly with Gmail-only. You can always add Outlook later.

---

## STEP 6 — Deploy Backend to Render

1. Go to [render.com](https://render.com) → Sign up with GitHub (free)

2. Dashboard → **New → Web Service** → connect your `maildigest` repo

3. Configure:

| Field | Value |
|-------|-------|
| Name | `maildigest-backend` |
| Root Directory | `backend` |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Plan | **Free** |

4. **Environment Variables** — add all of these:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | from Step 2 |
| `SUPABASE_SERVICE_KEY` | from Step 2 |
| `SUPABASE_JWT_SECRET` | from Step 2 |
| `GROQ_API_KEY` | from Step 3 |
| `GROQ_MODEL` | `llama-3.1-8b-instant` |
| `GMAIL_CLIENT_ID` | from Step 4 |
| `GMAIL_CLIENT_SECRET` | from Step 4 |
| `GMAIL_REDIRECT_URI` | `https://maildigest-backend.onrender.com/auth/gmail/callback` |
| `OUTLOOK_CLIENT_ID` | from Step 5 (or leave blank if skipping) |
| `OUTLOOK_CLIENT_SECRET` | from Step 5 (or leave blank if skipping) |
| `OUTLOOK_REDIRECT_URI` | `https://maildigest-backend.onrender.com/auth/outlook/callback` |
| `FRONTEND_URL` | `https://maildigest.vercel.app` *(update after Step 7)* |
| `JWT_SECRET` | any random string — generate one at [randomkeygen.com](https://randomkeygen.com) |
| `ENCRYPTION_KEY` | generate using command below |

5. **Generate ENCRYPTION_KEY** — run this once on your machine:

```bash
cd maildigest/backend
python -m venv venv
venv\Scripts\activate
pip install cryptography
python -c "from services.encryption import generate_key; print(generate_key())"
```

Copy the output → paste as `ENCRYPTION_KEY` in Render.

6. Click **Create Web Service** → wait ~3 minutes for first deploy

7. Test it — open this URL in your browser:
```
https://maildigest-backend.onrender.com/health
```
Expected response: `{"status":"ok","service":"maildigest"}`

---

## STEP 7 — Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → Sign up with GitHub (free)

2. Dashboard → **Add New → Project** → import your `maildigest` repo

3. Configure:

| Field | Value |
|-------|-------|
| Root Directory | `frontend` |
| Framework | Next.js (auto-detected) |
| Node.js Version | 20.x |

4. **Environment Variables**:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | from Step 2 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | from Step 2 |
| `NEXT_PUBLIC_API_URL` | `https://maildigest-backend.onrender.com` |

5. Click **Deploy** → wait ~2 minutes

6. Your URL: `https://maildigest-xxxx.vercel.app`

7. Go back to **Render → maildigest-backend → Environment** → update `FRONTEND_URL` to your actual Vercel URL → **Save Changes** (auto-redeploys)

---

## STEP 8 — First Login & Connect Accounts

1. Open your Vercel URL
2. Sign up with your email (Supabase handles auth)
3. Sidebar → **Accounts → Connect Gmail** → authorize with Google
4. If using Outlook → **Connect Outlook** → authorize with Microsoft
5. Add all your email accounts the same way
6. Sidebar → **Digest → Sync**
7. Emails load, categorized by Groq AI

---

## STEP 9 — Auto Sync Every Few Hours

So emails sync automatically without you clicking Sync manually.

1. Render Dashboard → **New → Cron Job** → connect same repo

2. Configure:

| Field | Value |
|-------|-------|
| Root Directory | `backend` |
| Build Command | `pip install httpx` |
| Command | `python -c "import httpx, os; httpx.get(os.environ['SYNC_URL'])"` |
| Schedule | `0 */3 * * *` (every 3 hours) |
| Plan | Free |

3. Add environment variable:

| Key | Value |
|-----|-------|
| `SYNC_URL` | `https://maildigest-backend.onrender.com/sync?user_id=YOUR_USER_ID` |

4. Get your user ID → Supabase → **Authentication → Users** → copy the UUID next to your email

---

## STEP 10 — Verify

- [ ] `https://your-backend.onrender.com/health` returns `{"status":"ok"}`
- [ ] Login works on your Vercel URL
- [ ] Accounts page shows connected accounts with green checkmarks
- [ ] Sync fetches emails
- [ ] Digest page shows emails grouped by category
- [ ] Clicking an email shows full content in the reading panel
- [ ] AI summaries appear (from Groq)
- [ ] "Open original" opens the email in Gmail/Outlook

---

## Troubleshooting

**Backend deploy fails on Render**
Check Render logs. 99% of the time it's a missing env variable or a typo.

**OAuth redirect_uri_mismatch error**
The redirect URI in Google Cloud / Azure must match exactly what's in your Render env vars. No trailing slash, exact same protocol (https).

**Emails not showing**
- Make sure you clicked Sync on the Accounts page
- Check Render logs for any Python errors
- Confirm the SQL migration ran — go to Supabase → Table Editor → you should see tables like `emails`, `email_accounts`, `ai_analysis`

**First load is slow (~30 seconds)**
Normal on Render free tier — it spins down after 15 minutes of inactivity. The first request of the day wakes it up. After that it's fast.

**Groq AI not classifying**
- Confirm `GROQ_API_KEY` starts with `gsk_` and is set in Render env vars
- Emails still show without AI — rule-based fallback kicks in automatically

---

## Full Architecture

```
Browser
  ↓
Vercel  (Next.js — serves the UI)
  ↓
Render  (FastAPI — business logic)
  ├── Supabase PostgreSQL   stores all emails permanently
  ├── Groq API              classifies and summarizes emails
  ├── Gmail API             fetches Gmail emails via OAuth
  └── Microsoft Graph API   fetches Outlook emails via OAuth
```

**Total cost: ₹0/month**
