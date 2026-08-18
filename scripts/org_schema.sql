-- Organizations table
CREATE TABLE IF NOT EXISTS orgs (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- User-org membership
CREATE TABLE IF NOT EXISTS org_members (
  id BIGSERIAL PRIMARY KEY,
  org_id BIGINT REFERENCES orgs(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- User profiles (linked to auth)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS policies
ALTER TABLE orgs ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "orgs_visible_to_members" ON orgs
  FOR SELECT USING (
    id IN (SELECT org_id FROM org_members WHERE user_id = auth.uid())
  );

CREATE POLICY "org_members_read_own" ON org_members
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "profiles_read_own" ON profiles
  FOR SELECT USING (id = auth.uid());

CREATE POLICY "profiles_update_own" ON profiles
  FOR UPDATE USING (id = auth.uid());

CREATE POLICY "profiles_insert_own" ON profiles
  FOR INSERT WITH CHECK (id = auth.uid());
