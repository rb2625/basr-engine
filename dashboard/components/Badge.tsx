export function SentimentBadge({ label }: { label: string | null }) {
  if (!label) return null;
  const cls = "sent-" + label;
  return (
    <span
      className={
        "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold " + cls
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
        "inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold " + cls
      }
    >
      {signal}
    </span>
  );
}
