
import { AlertCircle, RotateCcw } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
  minimal?: boolean;
}

export function ErrorState({ message = "Something went wrong", onRetry, className, minimal = false }: ErrorStateProps) {
  if (minimal) {
    return (
      <div className={cn("flex flex-col items-center justify-center p-4 text-center text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg", className)} role="alert">
        <div className="flex items-center gap-2">
            <AlertCircle size={16} aria-hidden="true" />
            <span className="text-sm font-medium">{message}</span>
        </div>
        {onRetry && (
            <button 
                onClick={onRetry} 
                className="mt-2 text-xs flex items-center gap-1 hover:underline opacity-80 hover:opacity-100 transition-opacity"
            >
                <RotateCcw size={12} /> Retry
            </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col items-center justify-center py-12 px-4 text-center rounded-2xl bg-slate-900/50 border border-white/5 backdrop-blur-sm", className)} role="alert" aria-live="polite">
      <div className="bg-red-500/10 p-4 rounded-full mb-4 ring-1 ring-red-500/20">
        <AlertCircle className="text-red-400" size={32} aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-slate-200 mb-1">Unable to Load Data</h3>
      <p className="text-slate-400 text-sm mb-6 max-w-xs">{message}</p>
      {onRetry && (
        <button 
            onClick={onRetry}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-200 rounded-lg transition-colors border border-white/10 text-sm font-medium"
        >
            <RotateCcw size={16} />
            <span>Try Again</span>
        </button>
      )}
    </div>
  );
}
