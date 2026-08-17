export function SentimentBadge({ label }: { label: string | null }) {
  if (!label) return null;
  const cls = "sent-" + label;
  return (
    <span
      className={
        "inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-wide " +
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
        "inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[10.5px] font-medium uppercase tracking-wide " +
        cls
      }
    >
      {signal}
    </span>
  );
}
