
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PredictionCard } from './PredictionCard';
import { PredictionResponse } from '@/types';

// Mock Lucide icons to avoid rendering issues
vi.mock('lucide-react', () => ({
  TrendingUp: () => <div data-testid="icon-up" />,
  TrendingDown: () => <div data-testid="icon-down" />,
  RefreshCw: () => <div data-testid="icon-refresh" />,
  BrainCircuit: () => <div data-testid="icon-brain" />,
  Activity: () => <div data-testid="icon-activity" />,
}));

// Mock Framer Motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className }: any) => <div className={className}>{children}</div>
  }
}));

// Mock Currency Utility
vi.mock('@/utils/currency', () => ({
  formatINR: (val: number) => `₹${val.toFixed(2)}`
}));

describe('PredictionCard', () => {
  const mockPredict = vi.fn();
  const mockTrain = vi.fn();
  const defaultProps = {
    symbol: 'AAPL',
    prediction: null,
    loading: false,
    error: null,
    onPredict: mockPredict,
    onTrain: mockTrain,
  };

  it('renders initial empty state', () => {
    render(<PredictionCard {...defaultProps} />);
    expect(screen.getByText(/AI Forecast/i)).toBeInTheDocument();
    expect(screen.getByText('No Model Available')).toBeInTheDocument();
    expect(screen.getByText('Train Model')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    render(<PredictionCard {...defaultProps} loading={true} />);
    expect(screen.getByText('Train Model')).toBeDisabled(); // Or some loading indicator via class
    // In our component, button text might change or have spinner
    // Let's check if button is disabled
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('displays prediction data', () => {
    const mockPrediction: PredictionResponse = {
      symbol: 'AAPL',
      current_price: 150.00,
      predicted_price: 155.00,
      direction: 'up',
      change_percent: 3.33,
      sentiment_contribution: 0.5, // 0 to 1
      prediction_date: '2023-01-02',
      model_version: 'v1'
    };

    render(<PredictionCard {...defaultProps} prediction={mockPrediction} />);
    
    expect(screen.getByText('₹155.00')).toBeInTheDocument();
    expect(screen.getByText('3.33%')).toBeInTheDocument();
    expect(screen.getByText(/Refresh/i)).toBeInTheDocument();
  });

  it('calls onTrain when Train Model is clicked', async () => {
    mockTrain.mockResolvedValue(true);
    render(<PredictionCard {...defaultProps} />);
    
    const button = screen.getByText('Train Model');
    fireEvent.click(button);
    
    expect(mockTrain).toHaveBeenCalledWith('AAPL');
    expect(screen.getByText('Training...')).toBeInTheDocument();
  });

  it('calls onPredict when Refresh is clicked', () => {
    const mockPrediction: PredictionResponse = {
        symbol: 'AAPL',
        current_price: 150.00,
        predicted_price: 155.00,
        direction: 'up',
        change_percent: 3.33,
        sentiment_contribution: 0.5,
        prediction_date: '2023-01-02',
        model_version: 'v1'
      };
      
    render(<PredictionCard {...defaultProps} prediction={mockPrediction} />);
    
    const button = screen.getByText('Refresh');
    fireEvent.click(button);
    
    expect(mockPredict).toHaveBeenCalled();
  });
});
