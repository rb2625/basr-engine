export function SentimentBadge({ label }: { label: string | null }) {
  if (!label) return null;
  const cls =
    label === "positive"
      ? "badge-positive"
      : label === "negative"
        ? "badge-negative"
        : label === "mixed"
          ? "badge-mixed"
          : "badge-neutral";
  return (
    <span
      className={`${cls} inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide`}
    >
      {label}
    </span>
  );
}

export function SignalBadge({ signal }: { signal: string | null }) {
  if (!signal) return null;
  const cls =
    signal === "stress"
      ? "sig-stress"
      : signal === "closure"
        ? "sig-closure"
        : signal === "opportunity"
          ? "sig-opportunity"
          : "sig-neutral";
  return (
    <span
      className={`${cls} inline-flex items-center rounded-md px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide`}
    >
      {signal}
    </span>
  );
}
