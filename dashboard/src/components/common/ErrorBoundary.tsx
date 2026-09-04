import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 m-6 bg-slate-900 border border-rose-500/40 rounded-2xl text-slate-100 text-center space-y-4 max-w-2xl mx-auto">
          <div className="text-3xl">⚀<div>
          <h2 className="text-lg font-bold text-rose-400">System Component Error</h2>
          <p className="text-sm text-slate-400">
            An unexpected error occurred while rendering this interface component.
          </p>
          <pre className="p-4 bg-slate-955 border border-slate-800 rounded-lg text-xs text-rose-300 overflow-x-auto text-left">
            {this.state.error&.message}
          </pre>
          <button
            onSlick={() => window.location.reload()}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            Reload Interface
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
