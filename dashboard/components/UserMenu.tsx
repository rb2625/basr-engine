"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function UserMenu() {
  const { user, loading, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const router = useRouter();

  if (loading) return null;

  if (!user) {
    return (
      <button
        onClick={() => router.push("/login")}
        className="rounded-xl border border-line bg-white px-3.5 py-1.5 text-[13px] font-medium text-ink transition-all hover:border-accent hover:text-accent hover:shadow-sm"
      >
        Sign in
      </button>
    );
  }

  const initials = user.email
    ? user.email.slice(0, 2).toUpperCase()
    : "U";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/10 text-[12px] font-semibold text-accent transition-all hover:bg-accent/20"
      >
        {initials}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-line bg-white p-1.5 shadow-lift">
            <div className="px-3 py-2">
              <div className="text-[13px] font-medium text-ink truncate">
                {user.email}
              </div>
              <div className="text-[11px] text-mute">Signed in</div>
            </div>
            <div className="my-1 border-t border-line" />
            <button
              onClick={async () => {
                await signOut();
                setOpen(false);
                router.push("/");
                router.refresh();
              }}
              className="w-full rounded-lg px-3 py-2 text-left text-[13px] text-ink transition-colors hover:bg-panel2"
            >
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}
