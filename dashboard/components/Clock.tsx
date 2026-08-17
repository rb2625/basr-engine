"use client";

import { useEffect, useState } from "react";

function fmt(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export default function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const dubai = now
    ? new Date(now.getTime() + 4 * 3600 * 1000)
    : null;
  return (
    <span className="hidden items-baseline gap-1.5 font-mono text-[11px] tracking-widest text-mute md:flex">
      <span className="text-golddim">DXB</span>
      <span className="tabular-nums text-text1">
        {dubai ? fmt(dubai) : "--:--:--"}
      </span>
    </span>
  );
}
