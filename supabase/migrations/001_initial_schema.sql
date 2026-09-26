-- MailDigest initial schema
-- Run this in Supabase SQL editor or via supabase db push

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ── Users ─────────────────────────────────────────────────────────────────────
-- Supabase Auth handles users. This table extends auth.users.
create table if not exists public.users (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  name        text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
alter table public.users enable row level security;
create policy "Users can read own row" on public.users for select using (auth.uid() = id);
create policy "Users can update own row" on public.users for update using (auth.uid() = id);

-- ── Email Accounts ─────────────────────────────────────────────────────────────
create table if not exists public.email_accounts (
  id                      uuid primary key default uuid_generate_v4(),
  user_id                 uuid not null references public.users(id) on delete cascade,
  provider                text not null check (provider in ('gmail', 'outlook')),
  email_address           text not null,
  display_name            text,
  provider_account_id     text,
  encrypted_access_token  text,
  encrypted_refresh_token text,
  token_expiry            timestamptz,
  sync_cursor             text,
  last_sync_at            timestamptz,
  sync_status             text not null default 'idle' check (sync_status in ('idle','syncing','error')),
  enabled                 boolean not null default true,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now(),
  unique (user_id, provider, email_address)
);
alter table public.email_accounts enable row level security;
create policy "Users manage own accounts" on public.email_accounts
  using (auth.uid() = user_id);

-- ── Emails ────────────────────────────────────────────────────────────────────
create table if not exists public.emails (
  id                   uuid primary key default uuid_generate_v4(),
  account_id           uuid not null references public.email_accounts(id) on delete cascade,
  provider_message_id  text not null,
  provider_thread_id   text,
  internet_message_id  text,
  sender_name          text,
  sender_email         text not null,
  recipients           jsonb default '[]',
  cc                   jsonb default '[]',
  bcc                  jsonb default '[]',
  subject              text,
  received_at          timestamptz not null,
  body_text            text,
  body_html            text,
  snippet              text,
  provider_url         text,
  has_attachments      boolean not null default false,
  is_read              boolean not null default false,
  is_starred           boolean not null default false,
  raw_metadata         jsonb,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  -- Deduplication: one row per message per account
  unique (account_id, provider_message_id)
);
create index if not exists emails_account_received on public.emails(account_id, received_at desc);
create index if not exists emails_received_at on public.emails(received_at desc);
alter table public.emails enable row level security;
create policy "Users read own emails" on public.emails for select
  using (
    exists (
      select 1 from public.email_accounts ea
      where ea.id = emails.account_id and ea.user_id = auth.uid()
    )
  );

-- ── Email Attachments ─────────────────────────────────────────────────────────
create table if not exists public.email_attachments (
  id                      uuid primary key default uuid_generate_v4(),
  email_id                uuid not null references public.emails(id) on delete cascade,
  provider_attachment_id  text not null,
  filename                text,
  mime_type               text,
  size_bytes              bigint,
  created_at              timestamptz not null default now(),
  unique (email_id, provider_attachment_id)
);
alter table public.email_attachments enable row level security;
create policy "Users read own attachments" on public.email_attachments for select
  using (
    exists (
      select 1 from public.emails e
      join public.email_accounts ea on ea.id = e.account_id
      where e.id = email_attachments.email_id and ea.user_id = auth.uid()
    )
  );

-- ── AI Analysis ───────────────────────────────────────────────────────────────
-- Separate table — NEVER overwrites email source data
create table if not exists public.ai_analysis (
  id               uuid primary key default uuid_generate_v4(),
  email_id         uuid not null references public.emails(id) on delete cascade,
  category         text check (category in ('jobs','competitions','tech','reddit','newsletters','college','personal','other')),
  subcategory      text,
  summary          text,
  priority         text check (priority in ('high','medium','low')),
  action_required  boolean default false,
  action_reason    text,
  deadline         timestamptz,
  event_date       timestamptz,
  organization     text,
  job_title        text,
  competition_name text,
  keywords         jsonb default '[]',
  confidence       float,
  model            text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  unique (email_id)
);
alter table public.ai_analysis enable row level security;
create policy "Users read own AI analysis" on public.ai_analysis for select
  using (
    exists (
      select 1 from public.emails e
      join public.email_accounts ea on ea.id = e.account_id
      where e.id = ai_analysis.email_id and ea.user_id = auth.uid()
    )
  );

-- ── Daily Digests ─────────────────────────────────────────────────────────────
create table if not exists public.daily_digests (
  id           uuid primary key default uuid_generate_v4(),
  user_id      uuid not null references public.users(id) on delete cascade,
  digest_date  date not null,
  timezone     text not null default 'Asia/Kolkata',
  total_emails integer not null default 0,
  complete     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  unique (user_id, digest_date)
);
alter table public.daily_digests enable row level security;
create policy "Users read own digests" on public.daily_digests
  using (auth.uid() = user_id);

-- ── User Settings ─────────────────────────────────────────────────────────────
create table if not exists public.user_settings (
  id            uuid primary key default uuid_generate_v4(),
  user_id       uuid not null references public.users(id) on delete cascade,
  digest_time   text not null default '20:00',
  timezone      text not null default 'Asia/Kolkata',
  ai_enabled    boolean not null default true,
  ollama_model  text not null default 'llama3.2',
  theme         text not null default 'light',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  unique (user_id)
);
alter table public.user_settings enable row level security;
create policy "Users manage own settings" on public.user_settings
  using (auth.uid() = user_id);

-- ── Updated-at trigger ────────────────────────────────────────────────────────
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger set_updated_at_email_accounts before update on public.email_accounts
  for each row execute function public.set_updated_at();
create trigger set_updated_at_emails before update on public.emails
  for each row execute function public.set_updated_at();
create trigger set_updated_at_ai_analysis before update on public.ai_analysis
  for each row execute function public.set_updated_at();
create trigger set_updated_at_user_settings before update on public.user_settings
  for each row execute function public.set_updated_at();
