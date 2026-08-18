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
      setError("Something went wrong. Please try again.");
    } finally {
      setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-white shadow-lg transition hover:bg-accent/90 hover:shadow-xl"
      >
        Feedback
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 rounded-xl border border-border bg-white p-4 shadow-2xl">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text1">Send feedback</h3>
        <button
          onClick={() => { setOpen(false); setSent(false); setError(""); }}
          className="text-mute hover:text-text1"
        >
          &times;
        </button>
      </div>

      {sent ? (
        <div className="py-4 text-center">
          <p className="text-sm font-medium text-green-600">Thanks! Your feedback was sent.</p>
          <button
            onClick={() => { setOpen(false); setSent(false); }}
            className="mt-3 text-xs text-mute hover:text-text1"
          >
            Close
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            name="name"
            placeholder="Name (optional)"
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text1 placeholder:text-mute focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <input
            name="email"
            type="email"
            placeholder="Email (optional)"
            className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text1 placeholder:text-mute focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
          <textarea
            name="message"
            required
            rows={3}
            placeholder="What would you like to see? What's working? What's not?"
            className="w-full resize-none rounded-lg border border-border bg-white px-3 py-2 text-sm text-text1 placeholder:text-mute focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
          {error && <p className="text-xs text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={sending}
            className="w-full rounded-lg bg-accent py-2 text-sm font-medium text-white transition hover:bg-accent/90 disabled:opacity-50"
          >
            {sending ? "Sending..." : "Send feedback"}
          </button>
        </form>
      )}
    </div>
  );
}
