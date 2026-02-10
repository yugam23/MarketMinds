/**
 * Spinner Component
 * Animated loading spinner.
 */
import './Spinner.css';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

export function Spinner({ size = 'md' }: SpinnerProps) {
  return <div className={`spinner spinner-${size}`} aria-label="Loading" />;
}
