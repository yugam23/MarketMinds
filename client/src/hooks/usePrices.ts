/**
 * usePrices Hook
 * Fetches and manages OHLCV price data for an asset.
 */
import { useState, useEffect, useCallback } from 'react';
import { getPrices } from '@/services/api';
import type { PriceData, CandlestickData } from '@/types';

interface UsePricesResult {
  data: PriceData[];
  candlestickData: CandlestickData[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function usePrices(symbol: string, days: number = 30): UsePricesResult {
  const [data, setData] = useState<PriceData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrices = useCallback(async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getPrices(symbol, days);
      setData(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch prices');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [symbol, days]);

  useEffect(() => {
    fetchPrices();
  }, [fetchPrices]);

  // Transform to candlestick format for charts
  const candlestickData: CandlestickData[] = Array.isArray(data) ? data.map((price) => ({
    time: price.date,
    open: price.open,
    high: price.high,
    low: price.low,
    close: price.close,
  })) : [];

  return {
    data,
    candlestickData,
    loading,
    error,
    refetch: fetchPrices,
  };
}
