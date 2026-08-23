"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refreshing: boolean;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useApi<T>(view: string, extra = "", refreshInterval?: number): ApiState<T> {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    error: null,
    loading: true,
    refreshing: false,
    lastUpdated: null,
    refresh: () => {},
  });
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const aliveRef = useRef(true);

  const fetchData = useCallback(() => {
    setState((s) => ({ ...s, refreshing: true, error: null }));
    fetch(`/api/data?view=${view}${extra}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => {
        if (!aliveRef.current) return;
        if (json && json.error) {
          setState((s) => ({ ...s, data: null, error: json.error, loading: false, refreshing: false }));
        } else {
          setState((s) => ({
            ...s,
            data: json as T,
            error: null,
            loading: false,
            refreshing: false,
            lastUpdated: new Date(),
          }));
        }
      })
      .catch((e) => {
        if (aliveRef.current) {
          setState((s) => ({ ...s, data: null, error: String(e), loading: false, refreshing: false }));
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
