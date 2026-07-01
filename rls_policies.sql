-- OneSattva — RLS policies for the new tables, matching the existing
-- "Users can manage own X" / ALL / public pattern used on checkins, cycle_data, etc.
-- Safe to re-run: drops the policy first if it already exists.
-- Run in Supabase Dashboard → SQL Editor.

alter table daily_priorities enable row level security;
drop policy if exists "Users can manage own daily priorities" on daily_priorities;
create policy "Users can manage own daily priorities" on daily_priorities
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table checkin_insights enable row level security;
drop policy if exists "Users can manage own checkin insights" on checkin_insights;
create policy "Users can manage own checkin insights" on checkin_insights
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table materiality_flags enable row level security;
drop policy if exists "Users can manage own materiality flags" on materiality_flags;
create policy "Users can manage own materiality flags" on materiality_flags
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table monthly_focus enable row level security;
drop policy if exists "Users can manage own monthly focus" on monthly_focus;
create policy "Users can manage own monthly focus" on monthly_focus
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table supplement_plan enable row level security;
drop policy if exists "Users can manage own supplement plan" on supplement_plan;
create policy "Users can manage own supplement plan" on supplement_plan
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table nutrition_plan enable row level security;
drop policy if exists "Users can manage own nutrition plan" on nutrition_plan;
create policy "Users can manage own nutrition plan" on nutrition_plan
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

alter table workout_plan enable row level security;
drop policy if exists "Users can manage own workout plan" on workout_plan;
create policy "Users can manage own workout plan" on workout_plan
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
