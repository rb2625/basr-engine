export default function Section({
  kicker,
  title,
  right,
  children,
}: {
  kicker?: string;
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          {kicker && (
            <div className="font-label-sm uppercase tracking-widest text-accent mb-2">
              {kicker}
            </div>
          )}
          <h3 className="font-display-sm text-ink">{title}</h3>
        </div>
        {right && <div className="shrink-0">{right}</div>}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
