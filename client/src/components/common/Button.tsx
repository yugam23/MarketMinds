/**
 * Button Component
 * Styled button with variants and loading state.
 */
import React from 'react';
import { Spinner } from './Spinner';
import './Button.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

import { twMerge } from 'tailwind-merge';
import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  // Map variant to Tailwind classes for better control than CSS modules sometimes allow
  // keeping the CSS classes for backward compat if needed, but adding focus ring
  
  return (
    <button
      className={cn(
        `btn-component btn-${variant} btn-size-${size}`,
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "transition-all duration-200",
        className
      )}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && <Spinner size="sm" aria-hidden="true" />}
      {children}
    </button>
  );
}
