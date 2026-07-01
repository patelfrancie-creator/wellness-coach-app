-- OneSattva — schema additions for the new app.py
-- Run in Supabase Dashboard → SQL Editor. Safe to re-run (IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).

-- profiles: cycle gate + a few onboarding fields
alter table profiles add column if not exists has_cycle boolean default false;
alter table profiles add column if not exists dob date;
alter table profiles add column if not exists occupation text;
alter table profiles add column if not exists allergies text;
alter table profiles add column if not exists eating_pattern text;
alter table profiles add column if not exists onboarding_complete boolean default false;

-- roadmaps: plan mode + commit/provisional tracking
alter table roadmaps add column if not exists plan_mode text;
alter table roadmaps add column if not exists committed boolean default false;
alter table roadmaps add column if not exists provisional boolean default false;
alter table roadmaps add column if not exists phase_start_date date;
alter table roadmaps add column if not exists roadmap_text text;
alter table roadmaps add column if not exists generated_at date;

-- cycle_data: real period duration, never assumed
alter table cycle_data add column if not exists period_duration int;

-- checkins: the 6 metrics the brief specifies
alter table checkins add column if not exists energy int;
alter table checkins add column if not exists mental_clarity int;
alter table checkins add column if not exists sleep_quality int;
alter table checkins add column if not exists mood int;
alter table checkins add column if not exists gut text;
alter table checkins add column if not exists libido text;
alter table checkins add column if not exists sleep_hours numeric;
alter table checkins add column if not exists workout text;
alter table checkins add column if not exists notes text;

-- ── New tables ────────────────────────────────────────────────────────────

create table if not exists daily_priorities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  for_date date not null,
  priorities_json text not null,
  generated_at timestamptz default now(),
  unique (user_id, for_date)
);

create table if not exists checkin_insights (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  for_date date not null,
  insight_text text not null,
  generated_at timestamptz default now(),
  unique (user_id, for_date)
);

create table if not exists materiality_flags (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  level text not null,           -- 'roadmap' | 'monthly_focus' | 'supplements' | 'nutrition' | 'workouts'
  flag_text text not null,
  resolved boolean default false,
  created_at timestamptz default now()
);

create table if not exists monthly_focus (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) unique,
  content text not null,
  generated_at date
);

create table if not exists supplement_plan (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) unique,
  content text not null,
  generated_at date
);

create table if not exists nutrition_plan (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) unique,
  content text not null,
  generated_at date
);

create table if not exists workout_plan (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) unique,
  content text not null,
  generated_at date
);

-- ── RLS — mirror whatever policy pattern your other per-user tables use ────
-- (auth.uid() = user_id). Enable + add a policy for each new table, e.g.:
--
-- alter table daily_priorities enable row level security;
-- create policy "own rows" on daily_priorities for all using (auth.uid() = user_id);
--
-- Repeat for checkin_insights, materiality_flags, monthly_focus, supplement_plan,
-- nutrition_plan, workout_plan. Skipped here since I don't know your existing
-- policy names/conventions — copy whatever you used for e.g. `checkins`.

-- ═══════════════════════════════════════════════════════════════════════════
-- Round 2 fixes — safe to re-run.
--
-- `roadmaps` has never had a unique constraint on user_id. Every upsert
-- (onboarding step 6 writing committed=false, then step 7 writing
-- committed=true) was therefore a plain INSERT — two rows per user, and
-- db_get_single()'s `.limit(1)` with no ORDER BY could return either one.
-- That is the exact cause of "Protocol says not committed" even after
-- committing, and the confusing PROVISIONAL banner on Home/Protocol.
-- The app code now always passes on_conflict="user_id" for this table,
-- but that only works once the constraint actually exists — hence this
-- migration. Same root-cause class for cycle_data, checkins, and onboarding
-- (each should be one row per user; none had the constraint app code needs).
-- ═══════════════════════════════════════════════════════════════════════════

-- Step 1: dedupe existing rows so the unique constraint can be added.
-- roadmaps: keep the committed row if one exists, else the most recent.
with ranked as (
  select id, row_number() over (
    partition by user_id
    order by committed desc, generated_at desc nulls last, id desc
  ) as rn
  from roadmaps
)
delete from roadmaps where id in (select id from ranked where rn > 1);

with ranked as (
  select id, row_number() over (partition by user_id order by id desc) as rn
  from cycle_data
)
delete from cycle_data where id in (select id from ranked where rn > 1);

with ranked as (
  select id, row_number() over (partition by user_id, checkin_date order by id desc) as rn
  from checkins
)
delete from checkins where id in (select id from ranked where rn > 1);

-- onboarding has no surrogate id column, so dedupe via ctid (Postgres's
-- built-in physical row identifier) instead of assuming one.
delete from onboarding a
using onboarding b
where a.user_id = b.user_id
  and a.ctid < b.ctid;

-- Step 2: add the missing unique constraints (guarded — safe to re-run).
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'roadmaps_user_id_key') then
    alter table roadmaps add constraint roadmaps_user_id_key unique (user_id);
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'cycle_data_user_id_key') then
    alter table cycle_data add constraint cycle_data_user_id_key unique (user_id);
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'checkins_user_id_checkin_date_key') then
    alter table checkins add constraint checkins_user_id_checkin_date_key unique (user_id, checkin_date);
  end if;
end $$;

do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'onboarding_user_id_key') then
    alter table onboarding add constraint onboarding_user_id_key unique (user_id);
  end if;
end $$;

-- current_step powers the "resume onboarding where you left off" fix.
alter table onboarding add column if not exists current_step int;

-- ═══════════════════════════════════════════════════════════════════════════
-- Round 3: clean up duplicate conditions/medications/supplements.
--
-- These tables intentionally have no unique constraint (a person can have
-- several conditions/meds/supplements), so the app-level dedup guard added
-- this round only stops *future* re-inserts — it can't remove rows that
-- were already duplicated by an earlier onboarding run (e.g. before the
-- forced-logout/resume fix existed). This deletes exact-name duplicates
-- (case-insensitive), keeping the earliest row per person.
--
-- This will NOT catch near-duplicates typed differently, e.g. "Peruease"
-- vs "Peruease 1mg" as two separate medication entries — those aren't the
-- same string, so the database can't safely tell they're the same thing.
-- Delete those manually from Profile & Data (Delete buttons are now on
-- every condition/medication/supplement row) once this migration runs.
-- ═══════════════════════════════════════════════════════════════════════════
with ranked as (
  select id, row_number() over (partition by user_id, lower(condition) order by id) as rn
  from medical_history
)
delete from medical_history where id in (select id from ranked where rn > 1);

with ranked as (
  select id, row_number() over (partition by user_id, lower(name) order by id) as rn
  from medications
)
delete from medications where id in (select id from ranked where rn > 1);

with ranked as (
  select id, row_number() over (partition by user_id, lower(name) order by id) as rn
  from supplements
)
delete from supplements where id in (select id from ranked where rn > 1);

-- ═══════════════════════════════════════════════════════════════════════════
-- Round 4: give lifestyle fields real columns instead of flattened text.
--
-- Onboarding Step 3 collects these as dropdowns/sliders (activity level,
-- alcohol, smoking, sleep quality, meals per day, eating out, stress level)
-- and text fields (bedtime, exercise routine, food preferences, etc). They
-- were being concatenated into one free-text field, so Profile & Data could
-- only show/edit them as a text box — losing the dropdown/slider UI the
-- onboarding wizard used. These columns let Profile & Data render the same
-- widget type for each field as onboarding did.
-- ═══════════════════════════════════════════════════════════════════════════
alter table profiles add column if not exists activity_level text;
alter table profiles add column if not exists alcohol text;
alter table profiles add column if not exists smoking text;
alter table profiles add column if not exists exercise_routine text;
alter table profiles add column if not exists sleep_bedtime text;
alter table profiles add column if not exists sleep_wake_time text;
alter table profiles add column if not exists sleep_duration text;
alter table profiles add column if not exists sleep_quality int;
alter table profiles add column if not exists sleep_challenges text;
alter table profiles add column if not exists first_meal text;
alter table profiles add column if not exists last_meal text;
alter table profiles add column if not exists meals_per_day text;
alter table profiles add column if not exists eating_out text;
alter table profiles add column if not exists food_prefs text;
alter table profiles add column if not exists stress_level int;
alter table profiles add column if not exists stressors text;
alter table profiles add column if not exists symptoms text;
alter table profiles add column if not exists anything_else text;

-- ═══════════════════════════════════════════════════════════════════════════
-- Round 6: let account deletion cascade through the newer tables.
--
-- daily_priorities, checkin_insights, materiality_flags, monthly_focus,
-- supplement_plan, nutrition_plan, and workout_plan all reference
-- auth.users(id) with no ON DELETE action, which defaults to blocking the
-- delete. That's why "delete user" in Authentication > Users started
-- failing once these tables had rows — they didn't exist before this round
-- of fixes. This drops and re-adds each FK with ON DELETE CASCADE so
-- deleting the auth user cleans up everywhere, restoring the old
-- delete-and-restart workflow. Safe to re-run.
-- ═══════════════════════════════════════════════════════════════════════════
alter table daily_priorities drop constraint if exists daily_priorities_user_id_fkey;
alter table daily_priorities add constraint daily_priorities_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table checkin_insights drop constraint if exists checkin_insights_user_id_fkey;
alter table checkin_insights add constraint checkin_insights_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table materiality_flags drop constraint if exists materiality_flags_user_id_fkey;
alter table materiality_flags add constraint materiality_flags_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table monthly_focus drop constraint if exists monthly_focus_user_id_fkey;
alter table monthly_focus add constraint monthly_focus_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table supplement_plan drop constraint if exists supplement_plan_user_id_fkey;
alter table supplement_plan add constraint supplement_plan_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table nutrition_plan drop constraint if exists nutrition_plan_user_id_fkey;
alter table nutrition_plan add constraint nutrition_plan_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;

alter table workout_plan drop constraint if exists workout_plan_user_id_fkey;
alter table workout_plan add constraint workout_plan_user_id_fkey foreign key (user_id) references auth.users(id) on delete cascade;
