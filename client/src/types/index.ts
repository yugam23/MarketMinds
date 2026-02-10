/**
 * MarketMinds Type Definitions
 * Core TypeScript interfaces for the application.
 */

// Asset Types
export interface Asset {
  symbol: string;
  name: string;
  asset_type: 'stock' | 'crypto';
}

// Price Types
export interface PriceData {
  id: number;
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceListResponse {
  symbol: string;
  data: PriceData[];
  count: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    offset: number;
    limit: number;
    days: number;
  };
}

// Candlestick Data for Charts
export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

// Headline Types
export interface Headline {
  id: number;
  symbol: string;
  date: string;
  title: string;
  source?: string;
  url?: string;
  sentiment_score?: number;
}

// Sentiment Types
export interface DailySentiment {
  id: number;
  symbol: string;
  date: string;
  avg_sentiment?: number;
  headline_count?: number;
  top_headline?: string;
}

export interface SentimentListResponse {
  symbol: string;
  data: DailySentiment[];
  count: number;
}

// Prediction Types
export interface PredictionRequest {
  symbol: string;
}

export interface PredictionResponse {
  symbol: string;
  current_price: number;
  predicted_price: number;
  direction: 'up' | 'down';
  change_percent: number;
  sentiment_contribution: number;
  prediction_date: string;
  model_version: string;
}

export interface TrainingResponse {
  status: string;
  message: string;
  final_loss?: number;
  data_points?: number;
}

// Health Check
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  db: 'connected' | 'disconnected';
  version: string;
}

// API Error
export interface ApiError {
  detail: string;
}

// Loading State
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}
