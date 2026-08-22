"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useApi<T>(view: string, extra = "", refreshInterval?: number): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: true,
    lastUpdated: null,
    refresh: () => {},
  });
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const aliveRef = useRef(true);

  const fetchData = useCallback(() => {
    setState((s) => ({ ...s, loading: s.data === null, error: null }));
    fetch(`/api/data?view=${view}${extra}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => {
        if (!aliveRef.current) return;
        if (json && json.error) {
          setState((s) => ({ ...s, data: null, error: json.error, loading: false }));
        } else {
          setState((s) => ({
            ...s,
            data: json as T,
            error: null,
            loading: false,
            lastUpdated: new Date(),
          }));
        }
      })
      .catch((e) => {
        if (aliveRef.current) {
          setState((s) => ({ ...s, data: null, error: String(e), loading: false }));
        }
      });
  }, [view, extra]);

  useEffect(() => {
    aliveRef.current = true;
    fetchData();

    if (refreshInterval && refreshInterval > 0) {
      timerRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      aliveRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchData, refreshInterval]);

  return { ...state, refresh: fetchData };
}
