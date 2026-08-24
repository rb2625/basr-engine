"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getBrowserClient } from "@/lib/supabase-browser";
import { useAuth } from "@/lib/auth-context";

interface Org {
  id: string;
  name: string;
  slug: string;
  role: string;
}

interface OrgContextType {
  orgs: Org[];
  currentOrg: Org | null;
  loading: boolean;
  createOrg: (name: string) => Promise<{ error?: string; org?: Org }>;
  switchOrg: (orgId: string) => void;
}

const OrgContext = createContext<OrgContextType>({
  orgs: [],
  currentOrg: null,
  loading: false,
  createOrg: async () => ({}),
  switchOrg: () => {},
});

export function useOrg() {
  return useContext(OrgContext);
}

export function OrgProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [currentOrg, setCurrentOrg] = useState<Org | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = getBrowserClient();

  useEffect(() => {
    if (!supabase || !user) {
      setOrgs([]);
      setCurrentOrg(null);
      setLoading(false);
      return;
    }

    async function loadOrgs() {
      setLoading(true);
      const { data } = await supabase!
        .from("user_orgs")
        .select("role, organizations(id, name, slug)")
        .eq("user_id", user!.id);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rows = (data || []) as any[];
      const parsed: Org[] = rows
        .filter((row) => row.organizations?.id)
        .map((row) => ({
          id: String(row.organizations.id),
          name: String(row.organizations.name),
          slug: String(row.organizations.slug),
          role: String(row.role),
        }));

      setOrgs(parsed);

      // Restore last selected org
      const saved = localStorage.getItem("basr_org_id");
      const match = parsed.find((o: Org) => o.id === saved);
      setCurrentOrg(match || parsed[0] || null);
      setLoading(false);
    }

    loadOrgs();
  }, [supabase, user]);

  function switchOrg(orgId: string) {
    const org = orgs.find((o) => o.id === orgId);
    if (org) {
      setCurrentOrg(org);
      localStorage.setItem("basr_org_id", orgId);
    }
  }

  async function createOrg(name: string) {
    if (!supabase || !user) return { error: "Not authenticated" };

    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

    const { data: org, error: orgErr } = await supabase
      .from("organizations")
      .insert({ name, slug, owner_id: user.id })
      .select()
      .single();

    if (orgErr) return { error: orgErr.message };

    const { error: memErr } = await supabase
      .from("user_orgs")
      .insert({ user_id: user.id, org_id: org.id, role: "owner" });

    if (memErr) return { error: memErr.message };

    const newOrg: Org = { id: org.id, name: org.name, slug: org.slug, role: "owner" };
    setOrgs((prev) => [...prev, newOrg]);
    setCurrentOrg(newOrg);
    localStorage.setItem("basr_org_id", newOrg.id);

    return { org: newOrg };
  }

  return (
    <OrgContext.Provider value={{ orgs, currentOrg, loading, createOrg, switchOrg }}>
      {children}
    </OrgContext.Provider>
  );
}
