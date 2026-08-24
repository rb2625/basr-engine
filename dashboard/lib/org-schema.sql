-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  owner_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- User-Org membership
CREATE TABLE IF NOT EXISTS user_orgs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, org_id)
);

-- RLS policies
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_orgs ENABLE ROW LEVEL SECURITY;

-- Users can see orgs they belong to
CREATE POLICY "Users can view own orgs" ON organizations
  FOR SELECT USING (
    id IN (SELECT org_id FROM user_orgs WHERE user_id = auth.uid())
  );

CREATE POLICY "Users can view own memberships" ON user_orgs
  FOR SELECT USING (user_id = auth.uid());

-- Owners can update their orgs
CREATE POLICY "Owners can update orgs" ON organizations
  FOR UPDATE USING (owner_id = auth.uid());

-- Any authenticated user can create an org
CREATE POLICY "Authenticated users can create orgs" ON organizations
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Authenticated users can join orgs" ON user_orgs
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
