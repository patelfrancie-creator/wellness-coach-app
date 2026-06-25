-- ════════════════════════════════════════════════════════════════════════════════
-- OneSattva — Safe schema update (skips anything already existing)
-- ════════════════════════════════════════════════════════════════════════════════

-- Add missing columns to onboarding table
alter table public.onboarding add column if not exists lab_upload_acknowledged boolean default false;
alter table public.onboarding add column if not exists lab_acknowledged_at timestamp with time zone;
alter table public.onboarding add column if not exists updated_at timestamp with time zone default now();

-- Add missing columns to profiles table
alter table public.profiles add column if not exists sex text;
alter table public.profiles add column if not exists date_of_birth date;
alter table public.profiles add column if not exists onboarding_complete boolean default false;
alter table public.profiles add column if not exists allergies text;
alter table public.profiles add column if not exists alcohol text;
alter table public.profiles add column if not exists smoking text;
alter table public.profiles add column if not exists wake_time text;
alter table public.profiles add column if not exists sleep_time text;
alter table public.profiles add column if not exists assigned_practitioner_id uuid references auth.users(id);

-- Add timeframe to goals
alter table public.goals add column if not exists timeframe text;

