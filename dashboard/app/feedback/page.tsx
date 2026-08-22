"use client";

import Section from "@/components/Section";
import { useApi } from "@/components/useApi";

interface FeedbackItem {
  id: number;
  name: string | null;
  email: string | null;
  message: string;
  page: string | null;
  created_at: string | null;
}

interface FeedbackData {
  items: FeedbackItem[];
  total: number;
}

export default function FeedbackPage() {
  const { data, error, loading } = useApi<FeedbackData>("feedback");

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-display-lg text-ink">User Feedback</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-relaxed text-mute">
          Submissions from the feedback button on the dashboard.
        </p>
      </div>

      <Section kicker="Submissions" title={`All feedback ${data ? `(${data.total})` : ""}`}>
        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card p-5">
                <div className="skeleton h-4 w-32" />
                <div className="skeleton mt-3 h-3 w-full" />
                <div className="skeleton mt-2 h-3 w-2/3" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="card border-neg/30 bg-neg/10 p-6 text-sm text-neg">
            <div className="font-semibold">Could not load feedback</div>
            <div className="mt-1 font-mono text-xs opacity-70">{error}</div>
            <div className="mt-3 text-xs text-mute">
              Run the feedback schema SQL in Supabase first:
              <code className="ml-1 rounded bg-ink-faint px-1.5 py-0.5 font-mono text-[11px]">
                scripts/feedback_schema.sql
              </code>
            </div>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="font-mono text-xs text-mute">
            No feedback submissions yet. Users can submit via the Feedback button on the dashboard.
          </div>
        ) : (
          <div className="divide-y divide-line">
            {data.items.map((item) => (
              <div key={item.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] font-medium text-ink">
                      {item.name || "Anonymous"}
                      {item.email && (
                        <span className="ml-2 font-mono text-[11px] text-mute">
                          {item.email}
                        </span>
                      )}
                    </div>
                    <div className="mt-1.5 text-[13px] leading-relaxed text-ink">
                      {item.message}
                    </div>
                    <div className="mt-2 font-mono text-[10px] text-mute">
                      {item.page && <span className="mr-2 rounded bg-panel-2 px-1.5 py-0.5">{item.page}</span>}
                      {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
