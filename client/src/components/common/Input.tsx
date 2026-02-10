import React, { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    const inputId = props.id || React.useId();
    
    return (
      <div className="space-y-2">
        {label && (
          <label 
            htmlFor={inputId} 
            className="text-sm font-medium text-slate-300"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`
            flex h-10 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 
            text-sm placeholder:text-slate-500 text-slate-100
            focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:border-transparent
            disabled:cursor-not-allowed disabled:opacity-50
            transition-all duration-200
            aria-[invalid=true]:border-red-500 aria-[invalid=true]:ring-red-500/20
            ${error ? 'border-red-500 ring-red-500/20' : ''}
            ${className}
          `}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-xs text-red-500" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
