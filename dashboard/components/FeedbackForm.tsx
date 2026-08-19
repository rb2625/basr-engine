"use client";

import { useState } from "react";

export default function FeedbackForm({ page }: { page?: string }) {
  const [open, setOpen] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSending(true);
    setError("");

    const form = e.currentTarget;
    const data = new FormData(form);

    try {
      const res = await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.get("name") || null,
          email: data.get("email") || null,
          message: data.get("message"),
          page: page || null,
        }),
      });

      if (!res.ok) throw new Error("Failed");
      setSent(true);
      form.reset();
    } catch {
      setError("Something went wrong.");
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-24 right-6 z-50 rounded-xl bg-accent/90 px-3.5 py-2 text-[12px] font-semibold text-black shadow-glow transition-all hover:bg-accent hover:shadow-glow-lg"
      >
        Feedback
      </button>
    );
  }

  return (
    <div className="fixed bottom-24 right-6 z-50 w-80 rounded-2xl border border-white/8 bg-[#141416]/95 p-4 shadow-2xl backdrop-blur-xl">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display-sm text-ink">Send feedback</h3>
        <button
          onClick={() => { setOpen(false); setSent(false); setError(""); }}
          className="text-ink-3 hover:text-ink"
        >
          &times;
        </button>
      </div>

      {sent ? (
        <div className="py-4 text-center">
          <p className="text-body-sm font-medium text-positive">Thanks! Sent.</p>
          <button
            onClick={() => { setOpen(false); setSent(false); }}
            className="mt-2 text-caption text-ink-3 hover:text-ink"
          >
            Close
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-2.5">
          <input
            name="name"
            placeholder="Name (optional)"
            className="w-full rounded-xl border border-white/6 bg-white/[0.03] px-3 py-2 text-body-sm text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/20 transition-colors"
          />
          <input
            name="email"
            type="email"
            placeholder="Email (optional)"
            className="w-full rounded-xl border border-white/6 bg-white/[0.03] px-3 py-2 text-body-sm text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/20 transition-colors"
          />
          <textarea
            name="message"
            required
            rows={3}
            placeholder="What would you like to see?"
            className="w-full resize-none rounded-xl border border-white/6 bg-white/[0.03] px-3 py-2 text-body-sm text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/20 transition-colors"
          />
          {error && <p className="text-[10px] text-negative">{error}</p>}
          <button
            type="submit"
            disabled={sending}
            className="w-full rounded-xl bg-accent py-2 text-body-sm font-semibold text-black transition-all hover:bg-accent-dim disabled:opacity-50"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </form>
      )}
    </div>
  );
}
