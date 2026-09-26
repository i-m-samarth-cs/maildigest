# MailDigest

Personal daily email digest. Connect Gmail and Outlook, sync automatically, browse everything in one clean UI.

## Stack

| Layer    | Tech                          |
|----------|-------------------------------|
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Backend  | FastAPI + Python 3.12         |
| Database | Supabase PostgreSQL (free tier) |
| Email    | Gmail API + Microsoft Graph API |
| AI       | Ollama (local, free)          |
| Auth     | Supabase Auth + OAuth 2.0     |

**Cost: ₹0/month** — all free tiers and open source.

---

## Setup

### 1. Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to SQL Editor → paste and run `supabase/migrations/001_initial_schema.sql`
3. Copy your **Project URL**, **anon key**, **service role key**, and **JWT secret** from Project Settings → API

### 2. Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API**
3. OAuth consent screen → External → add your email as test user
4. Credentials → Create OAuth 2.0 Client ID (Web application)
5. Add redirect URI: `http://localhost:8000/auth/gmail/callback`
6. Copy Client ID and Client Secret

### 3. Outlook OAuth

1. Go to [Azure Portal](https://portal.azure.com) → App registrations → New registration
2. Redirect URI: `http://localhost:8000/auth/outlook/callback`
3. API permissions → Add `Mail.Read`, `User.Read`, `offline_access`
4. Certificates & secrets → New client secret
5. Copy Application (client) ID and secret value

### 4. Ollama (local AI)

```bash
# Install from https://ollama.com
ollama pull llama3.2
ollama serve
```

Ollama runs on `http://localhost:11434`. If it's not running, MailDigest falls back to rule-based classification automatically.

### 5. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Copy and fill env
copy .env.example .env

# Generate encryption key
python -c "from services.encryption import generate_key; print(generate_key())"
# Paste output as ENCRYPTION_KEY in .env

uvicorn main:app --reload --port 8000
```

### 6. Frontend

```bash
cd frontend
npm install
copy .env.local.example .env.local
# Fill NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL

npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Daily Usage

1. Open [http://localhost:3000/digest](http://localhost:3000/digest)
2. Click **Sync** to fetch latest emails from all accounts
3. Browse by category, search, or click any email to read it
4. Original email always shown — AI summary is extra context only

## How it works

```
Gmail API / Microsoft Graph
        ↓
  FastAPI sync_service
        ↓
  Supabase (emails table)       ← source of truth, never modified
        ↓
  ai_service (Ollama / rules)   ← stored separately in ai_analysis
        ↓
  Next.js digest page           ← shows ALL emails, AI enriches display
```

**No email is ever lost.** AI failure never hides an email. The original email content is always preserved.

## Adding a new email provider

1. Subclass `backend/providers/base.py` → `EmailProvider`
2. Implement all abstract methods
3. Register in `backend/providers/provider_factory.py`
4. Add OAuth flow in `backend/services/oauth_service.py`
5. Add route in `backend/api/auth.py`

## Automatic sync (optional cron)

The backend exposes `GET /sync?user_id=<id>` for external triggers.

On Linux/Mac add to crontab:
```
*/30 * * * * curl -s http://localhost:8000/sync?user_id=YOUR_USER_ID
```

On Windows use Task Scheduler to call the same URL every 30 minutes.
