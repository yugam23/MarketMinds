/**
 * useSentiment Hook
 * Fetches and manages sentiment data for an asset.
 */
import { useState, useEffect, useCallback } from 'react';
import { getSentiment } from '@/services/api';
import type { DailySentiment } from '@/types';

interface UseSentimentResult {
  data: DailySentiment[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useSentiment(symbol: string, days: number = 30): UseSentimentResult {
  const [data, setData] = useState<DailySentiment[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSentiment = useCallback(async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getSentiment(symbol, days);
      setData(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sentiment');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [symbol, days]);

  useEffect(() => {
    fetchSentiment();
  }, [fetchSentiment]);

  return {
    data,
    loading,
    error,
    refetch: fetchSentiment,
  };
}
