export default function PrivacyPage() {
  return (
    <div className="prose prose-sm max-w-3xl">
      <h1 className="text-2xl font-bold text-text1">Privacy Policy</h1>
      <p className="text-mute">Last updated: August 2026</p>

      <h2 className="text-lg font-semibold text-text1 mt-6">What We Collect</h2>
      <p className="text-mute">
        BASR analyzes publicly available data from Reddit, news RSS feeds, YouTube comments,
        Apple App Store reviews, and Bluesky posts. We do not collect private messages,
        personal profiles, or non-public content.
      </p>

      <h2 className="text-lg font-semibold text-text1 mt-6">How We Use Data</h2>
      <ul className="text-mute list-disc pl-5 space-y-1">
        <li>Aggregate sentiment analysis (positive/negative/neutral)</li>
        <li>Trend detection and anomaly alerts</li>
        <li>Topic classification (housing, jobs, prices, etc.)</li>
        <li>Entity sentiment tracking (locations, companies, authorities)</li>
      </ul>
      <p className="text-mute mt-2">
        All analysis is aggregated. We never store or display individual user identities
        or make accusations about specific people.
      </p>

      <h2 className="text-lg font-semibold text-text1 mt-6">Data Sources</h2>
      <ul className="text-mute list-disc pl-5 space-y-1">
        <li><strong>Reddit:</strong> Public posts from r/dubai, r/abudhabi, r/UAE via Arctic Shift archive</li>
        <li><strong>News RSS:</strong> Khaleej Times, Gulf News, The National, WAM, and 7 more</li>
        <li><strong>YouTube:</strong> Public comments on UAE-related videos</li>
        <li><strong>App Store:</strong> Public app reviews for UAE apps</li>
        <li><strong>Bluesky:</strong> Public posts mentioning UAE topics</li>
      </ul>

      <h2 className="text-lg font-semibold text-text1 mt-6">Cookies and Tracking</h2>
      <p className="text-mute">
        We do not use cookies, analytics trackers, or advertising pixels.
        The dashboard is served through Vercel&apos;s CDN.
      </p>

      <h2 className="text-lg font-semibold text-text1 mt-6">Data Retention</h2>
      <p className="text-mute">
        Aggregated sentiment data is retained indefinitely for trend analysis.
        Raw source text is stored for up to 90 days for debugging and reprocessing.
      </p>

      <h2 className="text-lg font-semibold text-text1 mt-6">Open Source</h2>
      <p className="text-mute">
        BASR is open source under the Apache 2.0 license.
        You can audit our code at{" "}
        <a href="https://github.com/rb2625/basr-engine" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
          github.com/rb2625/basr-engine
        </a>.
      </p>

      <h2 className="text-lg font-semibold text-text1 mt-6">Contact</h2>
      <p className="text-mute">
        For privacy questions, open an issue on GitHub or use the feedback form on the dashboard.
      </p>
    </div>
  );
}
