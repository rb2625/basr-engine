export function SentimentBadge({ label }: { label: string | null }) {
  if (!label) return null;
  const cls = "sent-" + label;
  return (
    <span
      className={
        "inline-flex items-center rounded-lg px-2.5 py-1 font-mono text-[10.5px] font-semibold uppercase tracking-wider " +
        cls
      }
    >
      {label}
    </span>
  );
}

export function SignalBadge({ signal }: { signal: string | null }) {
  if (!signal) return null;
  const cls = "sig-" + signal;
  return (
    <span
      className={
        "inline-flex items-center rounded-lg px-2.5 py-1 font-mono text-[10.5px] font-semibold uppercase tracking-wider " +
        cls
      }
    >
      {signal}
    </span>
  );
}
