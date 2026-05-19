-- ============================================================
-- STUDY PLANNER — Supabase (Postgres) schema + RLS
-- ============================================================
-- Cole este arquivo inteiro no SQL Editor do Supabase
-- (projeto: rtskriowojyczcobvtgh) e clique em "Run".
--
-- Não criamos tabela `users`: usuários ficam em `auth.users`
-- (gerenciada pelo Supabase Auth). Nome / nível / curso são
-- salvos em user_metadata no momento do signUp.
-- ============================================================

-- ------------------------------------------------------------
-- SUBJECTS
-- ------------------------------------------------------------
create table if not exists public.subjects (
    id          bigserial primary key,
    user_id     uuid        not null references auth.users(id) on delete cascade,
    name        varchar(120) not null,
    difficulty  smallint    not null check (difficulty between 1 and 5),
    priority    smallint    not null check (priority   between 1 and 5),
    exam_date   date        not null,
    created_at  timestamptz not null default now()
);

create index if not exists idx_subjects_user_id on public.subjects(user_id);

-- ------------------------------------------------------------
-- STUDY_PLANS
-- ------------------------------------------------------------
create table if not exists public.study_plans (
    id                  bigserial primary key,
    user_id             uuid        not null references auth.users(id) on delete cascade,
    day_of_week         varchar(20) not null,
    subject_name        varchar(120) not null,
    study_time_minutes  integer     not null,
    generated_at        timestamptz not null default now()
);

create index if not exists idx_study_plans_user_id on public.study_plans(user_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table public.subjects    enable row level security;
alter table public.study_plans enable row level security;

-- ---- subjects ----
drop policy if exists "subjects_select_own" on public.subjects;
create policy "subjects_select_own"
    on public.subjects for select
    using (auth.uid() = user_id);

drop policy if exists "subjects_insert_own" on public.subjects;
create policy "subjects_insert_own"
    on public.subjects for insert
    with check (auth.uid() = user_id);

drop policy if exists "subjects_update_own" on public.subjects;
create policy "subjects_update_own"
    on public.subjects for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "subjects_delete_own" on public.subjects;
create policy "subjects_delete_own"
    on public.subjects for delete
    using (auth.uid() = user_id);

-- ---- study_plans ----
drop policy if exists "study_plans_select_own" on public.study_plans;
create policy "study_plans_select_own"
    on public.study_plans for select
    using (auth.uid() = user_id);

drop policy if exists "study_plans_insert_own" on public.study_plans;
create policy "study_plans_insert_own"
    on public.study_plans for insert
    with check (auth.uid() = user_id);

drop policy if exists "study_plans_update_own" on public.study_plans;
create policy "study_plans_update_own"
    on public.study_plans for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "study_plans_delete_own" on public.study_plans;
create policy "study_plans_delete_own"
    on public.study_plans for delete
    using (auth.uid() = user_id);
