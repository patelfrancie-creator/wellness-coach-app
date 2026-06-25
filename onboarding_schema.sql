-- ════════════════════════════════════════════════════════════════════════════════
-- OneSattva — Onboarding & Extended Schema
-- Run this once in Supabase SQL Editor
-- ════════════════════════════════════════════════════════════════════════════════

-- Onboarding progress tracking
create table public.onboarding (
  user_id uuid references public.profiles(id) on delete cascade primary key,
  current_step integer default 1,
  step1_done boolean default false,
  step2_done boolean default false,
  step3_done boolean default false,
  step4_done boolean default false,
  completed boolean default false,
  lab_upload_acknowledged boolean default false,
  lab_acknowledged_at timestamp with time zone,
  started_at timestamp with time zone default now(),
  completed_at timestamp with time zone,
  updated_at timestamp with time zone default now()
);

alter table public.onboarding enable row level security;
create policy "Users can manage own onboarding" on public.onboarding
  for all using (auth.uid() = user_id);

-- ── Extend profiles table ─────────────────────────────────────────────────────

-- Basic info fields
alter table public.profiles add column if not exists sex text;
alter table public.profiles add column if not exists date_of_birth date;
alter table public.profiles add column if not exists onboarding_complete boolean default false;
alter table public.profiles add column if not exists allergies text;
alter table public.profiles add column if not exists alcohol text;
alter table public.profiles add column if not exists smoking text;
alter table public.profiles add column if not exists wake_time text;
alter table public.profiles add column if not exists sleep_time text;

-- Practitioner relationship (nullable — does nothing today, enables Phase 2)
-- When practitioners are added, this links a patient to their assigned doctor/nutritionist
alter table public.profiles add column if not exists assigned_practitioner_id uuid references auth.users(id);

-- ── Extend goals table ────────────────────────────────────────────────────────
alter table public.goals add column if not exists timeframe text;

-- ════════════════════════════════════════════════════════════════════════════════
-- FUTURE USE ONLY — Practitioner layer (do not activate yet)
-- When ready for Phase 2, run the section below in a separate query
-- ════════════════════════════════════════════════════════════════════════════════

-- create table public.practitioner_profiles (
--   id uuid references auth.users(id) on delete cascade primary key,
--   full_name text,
--   specialty text,
--   license_number text,
--   verified boolean default false,
--   created_at timestamp with time zone default now()
-- );
--
-- create table public.practitioner_notes (
--   id uuid default gen_random_uuid() primary key,
--   practitioner_id uuid references public.practitioner_profiles(id),
--   patient_id uuid references public.profiles(id),
--   note text,
--   created_at timestamp with time zone default now()
-- );
--
-- create policy "Practitioners can view assigned patients"
--   on public.profiles for select
--   using (assigned_practitioner_id = auth.uid());

