/**
 * Formats a number as Indian Rupee (INR).
 * @param amount - The amount to format.
 * @param decimals - The number of decimal places (default 2).
 * @returns Formatted currency string (e.g., ₹1,234.56).
 */
export function formatINR(amount: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount);
}
