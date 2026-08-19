create table if not exists feedback (
  id         bigserial primary key,
  name       text,
  email      text,
  message    text not null,
  page       text,
  created_at timestamptz default now()
);

alter table feedback enable row level security;

create policy "service_only" on feedback
  for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');
