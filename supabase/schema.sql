-- Bilancio — schema Postgres per Supabase
-- Eseguire per intero nel SQL Editor di Supabase (Project → SQL Editor → New query).
-- Single-user per ora: nessuna colonna user_id. RLS è abilitata su ogni tabella
-- ma SENZA policy: FastAPI si collega con la connection string da owner/service
-- role, che bypassa sempre RLS, quindi l'app continua a funzionare normalmente.
-- L'unico effetto è bloccare del tutto l'accesso alle tabelle tramite l'API
-- REST/anon key automatica di Supabase (PostgREST), che altrimenti esporrebbe
-- pubblicamente ogni riga a chiunque avesse l'anon key.
-- Quando si aggiungerà Supabase Auth multi-utente, andrà aggiunta una colonna
-- `user_id uuid references auth.users(id)` su ogni tabella + policy RLS reali
-- (es. `using (auth.uid() = user_id)`), ed eventualmente passare la connessione
-- di FastAPI a un ruolo Postgres non-superuser perché RLS abbia effetto anche lì.

create extension if not exists pgcrypto;

-- ====================================================
-- CATEGORIES
-- ====================================================
create table if not exists categories (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  type          text not null default 'expense' check (type in ('income','expense')),
  color         text not null default '#7CA8E3',
  monthly_limit numeric(12,2),
  created_at    timestamptz not null default now()
);
alter table categories enable row level security;

-- Migration idempotente per database creati prima dell'introduzione del campo "type"
-- (sicura da rieseguire: non fa nulla se la colonna/constraint esistono già)
alter table categories add column if not exists type text not null default 'expense';
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'categories_type_check') then
    alter table categories add constraint categories_type_check check (type in ('income','expense'));
  end if;
end $$;

-- ====================================================
-- ACCOUNTS (conti) — schema pronto, nessuna API ancora in questa fase
-- ====================================================
create table if not exists accounts (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,
  type            text not null check (type in ('corrente','risparmio','investimento','contanti','carta')),
  initial_balance numeric(12,2) not null default 0,
  color           text not null default '#6FE3A0',
  created_at      timestamptz not null default now()
);
alter table accounts enable row level security;

-- ====================================================
-- PERSONS — schema pronto, nessuna API ancora in questa fase
-- ====================================================
create table if not exists persons (
  id         uuid primary key default gen_random_uuid(),
  name       text not null unique,
  created_at timestamptz not null default now()
);
alter table persons enable row level security;

-- ====================================================
-- GOALS (obiettivi) — schema pronto, nessuna API ancora in questa fase
-- ====================================================
create table if not exists goals (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  target     numeric(12,2) not null check (target > 0),
  current    numeric(12,2) not null default 0,
  deadline   date,
  created_at timestamptz not null default now()
);
alter table goals enable row level security;

-- ====================================================
-- MOVEMENTS
-- category_id è una FK reale (categories ha già l'API in questa fase).
-- account_name / person_name / from_account_name / to_account_name / goal_name
-- sono testo denormalizzato per ora: conti/persone/obiettivi vivono ancora in
-- localStorage lato frontend e i loro id client-side non esistono nel DB.
-- Quando avranno una loro API, sostituire con account_id/person_id/goal_id (FK)
-- + migration di backfill che fa il match per nome.
-- ====================================================
create table if not exists movements (
  id                 uuid primary key default gen_random_uuid(),
  type               text not null check (type in ('income','expense','transfer')),
  description        text not null,
  amount             numeric(12,2) not null check (amount > 0),
  date               date not null,
  category_id        uuid references categories(id) on delete set null,
  account_name       text,
  person_name        text,
  from_account_name  text,
  to_account_name    text,
  goal_name          text,
  goal_amount        numeric(12,2),
  created_at         timestamptz not null default now()
);

create index if not exists idx_movements_date on movements (date);
create index if not exists idx_movements_category_id on movements (category_id);
create index if not exists idx_movements_type on movements (type);
alter table movements enable row level security;

-- ====================================================
-- INVESTMENTS — schema pronto, nessuna API ancora in questa fase
-- ====================================================
create table if not exists investments (
  id         uuid primary key default gen_random_uuid(),
  ticker     text not null,
  isin       text,
  name       text not null,
  type       text not null check (type in ('azione','etf','obbligazione','crypto','altro')),
  sector     text not null,
  qty        numeric(18,6) not null check (qty > 0),
  avg_price  numeric(18,6) not null check (avg_price > 0),
  cur_price  numeric(18,6) not null,
  added_at   date not null default current_date,
  updated_at date not null default current_date
);
alter table investments enable row level security;

-- ====================================================
-- RECURRING_EXPENSES — spese/entrate ricorrenti (mutuo, abbonamenti, ecc.)
-- account_name / person_name denormalizzati per lo stesso motivo di movements.
-- Le occorrenze dovute vengono generate come righe in `movements` da
-- POST /recurring/run-due, chiamato dal frontend a ogni apertura dell'app.
-- ====================================================
create table if not exists recurring_expenses (
  id                  uuid primary key default gen_random_uuid(),
  name                text not null,
  type                text not null check (type in ('income','expense')) default 'expense',
  amount              numeric(12,2) not null check (amount > 0),
  category_id         uuid references categories(id) on delete set null,
  account_name        text,
  person_name         text,
  day_of_month        smallint not null check (day_of_month between 1 and 31),
  start_date          date not null,
  end_date            date,
  active              boolean not null default true,
  last_generated_date date,
  created_at          timestamptz not null default now()
);
alter table recurring_expenses enable row level security;

-- Impostazioni app (configurazione Telegram, nome app, ecc.)
create table if not exists app_settings (
  key        text primary key,
  value      text,
  updated_at timestamptz not null default now()
);
alter table app_settings enable row level security;
