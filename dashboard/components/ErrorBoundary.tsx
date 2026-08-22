"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="card border-neg/20 bg-neg/10 p-6 text-center" role="alert">
          <div className="text-sm font-semibold text-neg">Something went wrong</div>
          <div className="mt-1 font-mono text-xs text-neg/70">
            {this.state.error?.message || "Unknown error"}
          </div>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-3 rounded-lg bg-neg/10 px-3 py-1.5 text-xs font-medium text-neg transition-colors hover:bg-neg/20"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
