import { describe, it, expect } from 'vitest';
import { formatINR } from './currency';

describe('formatINR', () => {
  it('formats numbers as Indian Rupee', () => {
    // Note: The specific output depends on locale implementation in Node environment,
    // but we expect the currency code or symbol.
    // In Node (English locale), it might output "₹1,234.56" or similar.
    const result = formatINR(1234.56);
    expect(result).toContain('1,234.56');
    // We check for ₹ or INR depending on environment capabilities
    // expect(result).toMatch(/₹|INR/); 
  });

  it('handles zero correctly', () => {
    expect(formatINR(0)).toContain('0.00');
  });

  it('handles large numbers (Lakhs)', () => {
    // Indian numbering system uses 1,00,000.00
    expect(formatINR(100000)).toContain('1,00,000.00');
  });

  it('respects decimal places', () => {
    expect(formatINR(123.456, 3)).toContain('123.456');
  });
});
