export default function ApiDocsPage() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-2xl font-bold text-ink mb-2">BASR API v1</h1>
      <p className="text-sm text-ink-3 mb-8">
        Programmatic access to UAE sentiment intelligence data. API key required.
      </p>

      <div className="space-y-8">
        <section>
          <h2 className="text-lg font-semibold text-ink mb-3">Authentication</h2>
          <div className="rounded-xl border border-line bg-surface p-4">
            <p className="text-sm text-ink-2 mb-3">All requests require a Bearer token:</p>
            <pre className="text-xs font-mono text-ink-3 bg-bg p-3 rounded-lg overflow-x-auto">
{`Authorization: Bearer YOUR_API_KEY`}
            </pre>
            <p className="text-xs text-ink-faint mt-3">
              Get your API key by contacting support@basr.io
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-ink mb-3">Endpoints</h2>
          <div className="space-y-4">
            {[
              { method: "GET", path: "/api/v1/health", desc: "Health check (no auth required)" },
              { method: "GET", path: "/api/v1/sentiment", desc: "Recent sentiment data with sector filtering", params: "?sector=Tech&days=7&limit=50" },
              { method: "GET", path: "/api/v1/topics", desc: "Sector breakdown with sentiment aggregation" },
              { method: "GET", path: "/api/v1/alerts", desc: "Latest anomaly alerts", params: "?limit=20" },
            ].map((ep) => (
              <div key={ep.path} className="rounded-xl border border-line bg-surface p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="rounded-md bg-green-500/10 px-2 py-0.5 text-xs font-bold text-green-400">{ep.method}</span>
                  <code className="text-sm font-mono text-ink">{ep.path}</code>
                </div>
                <p className="text-sm text-ink-3">{ep.desc}</p>
                {ep.params && (
                  <p className="text-xs text-ink-faint mt-2">Query params: <code>{ep.params}</code></p>
                )}
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-ink mb-3">Example</h2>
          <pre className="text-xs font-mono text-ink-3 bg-bg p-4 rounded-xl overflow-x-auto">
{`curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://basr.io/api/v1/sentiment?sector=Real Estate&days=7"`}
          </pre>
        </section>
      </div>
    </div>
  );
}
