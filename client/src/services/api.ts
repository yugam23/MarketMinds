/**
 * MarketMinds API Service
 * Axios-based HTTP client for backend communication.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Asset,
  PriceListResponse,
  SentimentListResponse,
  Headline,
  PaginatedResponse, // Import this
  PredictionResponse,
  TrainingResponse,
  HealthResponse,
  ApiError,
} from '@/types';



// Create axios instance with defaults
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    
    // Only log in development
    if (import.meta.env.DEV) {
      console.error('API Error:', message);
    }
    
    return Promise.reject(new Error(message));
  }
);

// Health Check
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

// Assets
export const getAssets = async (): Promise<Asset[]> => {
  const response = await api.get<Asset[]>('/assets');
  return response.data;
};

export const getAsset = async (symbol: string): Promise<Asset> => {
  const response = await api.get<Asset>(`/assets/${symbol}`);
  return response.data;
};

export const createAsset = async (asset: Asset): Promise<Asset> => {
  const response = await api.post<Asset>('/assets', asset);
  return response.data;
};

// Prices
export const getPrices = async (symbol: string, days: number = 30): Promise<PriceListResponse> => {
  const response = await api.get<PriceListResponse>(`/prices/${symbol}`, {
    params: { days },
  });
  return response.data;
};

export const getLatestPrice = async (symbol: string): Promise<PriceListResponse['data'][0]> => {
  const response = await api.get<PriceListResponse['data'][0]>(`/prices/${symbol}/latest`);
  return response.data;
};

// Sentiment
export const getSentiment = async (symbol: string, days: number = 30): Promise<SentimentListResponse> => {
  const response = await api.get<SentimentListResponse>(`/sentiment/${symbol}`, {
    params: { days },
  });
  return response.data;
};

export const getLatestSentiment = async (symbol: string): Promise<SentimentListResponse['data'][0]> => {
  const response = await api.get<SentimentListResponse['data'][0]>(`/sentiment/${symbol}/latest`);
  return response.data;
};

// Headlines
export const getHeadlines = async (
  symbol: string,
  days: number = 7,
  limit: number = 50,
  offset: number = 0
): Promise<PaginatedResponse<Headline>> => {
  const response = await api.get<PaginatedResponse<Headline>>(`/headlines/${symbol}`, {
    params: { days, limit, offset },
  });
  return response.data;
};

// Predictions
// Predictions
export const getPrediction = async (symbol: string): Promise<PredictionResponse> => {
  const response = await api.get<PredictionResponse>(`/predict/${symbol}`);
  return response.data;
};

export const trainModel = async (symbol: string): Promise<TrainingResponse> => {
  const response = await api.post<TrainingResponse>(`/predict/train/${symbol}`);
  return response.data;
};

export default api;
