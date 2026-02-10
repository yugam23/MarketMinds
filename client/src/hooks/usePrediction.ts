/**
 * usePrediction Hook
 * Manages prediction requests and state.
 */
import { useState, useCallback } from 'react';
import { getPrediction, trainModel } from '@/services/api';
import type { PredictionResponse } from '@/types';

interface UsePredictionResult {
  prediction: PredictionResponse | null;
  loading: boolean;
  error: string | null;
  predict: (symbol: string) => Promise<void>;
  train: (symbol: string) => Promise<boolean>;
  reset: () => void;
}

export function usePrediction(): UsePredictionResult {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const predict = useCallback(async (symbol: string) => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    try {
      const response = await getPrediction(symbol);
      setPrediction(response);
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('not trained')) {
        setPrediction(null);
      } else {
        setError(err instanceof Error ? err.message : 'Prediction failed');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const train = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      await trainModel(symbol);
      return true;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Training failed to start');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setPrediction(null);
    setError(null);
  }, []);

  return {
    prediction,
    loading,
    error,
    predict,
    train,
    reset,
  };
}
