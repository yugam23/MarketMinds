import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
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
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white p-4">
            <div className="max-w-md w-full bg-black/50 border border-red-500/50 rounded-lg p-6 backdrop-blur-xl">
              <h2 className="text-xl font-bold text-red-400 mb-4">Something went wrong</h2>
              <p className="text-gray-300 mb-4">The application encountered an urgent error and had to stop.</p>
              <div className="bg-black/50 p-4 rounded border border-white/10 overflow-auto max-h-48 text-xs font-mono text-red-300">
                {this.state.error?.toString()}
              </div>
              <button
                className="mt-6 w-full py-2 bg-red-600 hover:bg-red-500 rounded font-medium transition-colors"
                onClick={() => window.location.reload()}
              >
                Reload Application
              </button>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
