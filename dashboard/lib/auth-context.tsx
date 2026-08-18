"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "@supabase/supabase-js";
import { getBrowserClient } from "@/lib/supabase-browser";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => ({}),
  signUp: async () => ({}),
  signOut: async () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = getBrowserClient();

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  async function signIn(email: string, password: string) {
    const supabase = getBrowserClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    return { error: error?.message };
  }

  async function signUp(email: string, password: string) {
    const supabase = getBrowserClient();
    const { error } = await supabase.auth.signUp({ email, password });
    return { error: error?.message };
  }

  async function signOut() {
    const supabase = getBrowserClient();
    await supabase.auth.signOut();
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
