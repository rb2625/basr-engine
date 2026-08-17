import type { ReactNode } from "react";

export default function Section({
  kicker,
  title,
  right,
  children,
  className = "",
  delay = 0,
}: {
  kicker?: string;
  title?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <section
      className={`card p-5 sm:p-6 ${className}`}
      style={delay ? { animationDelay: `${delay}ms` } : undefined}
    >
      {(kicker || title) && (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div>
            {kicker && (
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-gold">
                {kicker}
              </div>
            )}
            {title && (
              <h2 className="mt-1 text-[15px] font-semibold text-text1">
                {title}
              </h2>
            )}
          </div>
          {right}
        </header>
      )}
      {children}
    </section>
  );
}
