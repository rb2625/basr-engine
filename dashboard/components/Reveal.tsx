"use client";

import type { CSSProperties, ReactNode } from "react";

export default function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const style: CSSProperties = {
    animationDelay: `${delay}ms`,
  };
  return (
    <div className={`anim-reveal ${className}`} style={style}>
      {children}
    </div>
  );
}
