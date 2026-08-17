"use client";

import { useEffect, useState } from "react";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

export function useApi<T>(view: string, extra = ""): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: true,
  });
  useEffect(() => {
    let alive = true;
    setState({ data: null, error: null, loading: true });
    fetch(`/api/data?view=${view}${extra}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => {
        if (!alive) return;
        if (json && json.error) {
          setState({ data: null, error: json.error, loading: false });
        } else {
          setState({ data: json as T, error: null, loading: false });
        }
      })
      .catch((e) => {
        if (alive) setState({ data: null, error: String(e), loading: false });
      });
    return () => {
      alive = false;
    };
  }, [view, extra]);
  return state;
}
