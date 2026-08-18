"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const { signIn, signUp } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSending(true);
    setError("");

    const result = isSignUp
      ? await signUp(email, password)
      : await signIn(email, password);

    if (result.error) {
      setError(result.error);
      setSending(false);
    } else {
      router.push("/");
      router.refresh();
    }
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-accent-dim text-xl font-bold text-white shadow-glow">
            B
          </div>
          <h1 className="text-display-sm text-ink">
            {isSignUp ? "Create account" : "Sign in"}
          </h1>
          <p className="mt-2 text-sm text-mute">
            {isSignUp
              ? "Create an account to access org features"
              : "Sign in to access your workspace"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-ink">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink placeholder:text-mute focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-[13px] font-medium text-ink">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-line bg-white px-4 py-2.5 text-sm text-ink placeholder:text-mute focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition-colors"
              placeholder="Your password"
            />
          </div>

          {error && (
            <div className="rounded-xl border border-neg/20 bg-neg-light px-4 py-3 text-sm text-neg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={sending}
            className="w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-white transition-all hover:bg-accent-dim hover:shadow-glow disabled:opacity-50"
          >
            {sending ? "Please wait..." : isSignUp ? "Create account" : "Sign in"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => { setIsSignUp(!isSignUp); setError(""); }}
            className="text-[13px] text-mute hover:text-accent transition-colors"
          >
            {isSignUp
              ? "Already have an account? Sign in"
              : "Don't have an account? Sign up"}
          </button>
        </div>

        <div className="mt-8 border-t border-line pt-6 text-center">
          <a href="/" className="text-[13px] text-mute hover:text-accent transition-colors">
            Continue without account
          </a>
        </div>
      </div>
    </div>
  );
}
