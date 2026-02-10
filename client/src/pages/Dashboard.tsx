/**
 * MarketMinds Dashboard
 * Main dashboard view.
 */
import { useState, lazy, Suspense } from 'react';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { SentimentOverlay } from '@/components/charts/SentimentOverlay';
import { PredictionCard } from '@/components/widgets/PredictionCard';
import { MetricsGrid } from '@/components/widgets/MetricsGrid';
import { usePrices } from '@/hooks/usePrices';
import { useSentiment } from '@/hooks/useSentiment';
import { usePrediction } from '@/hooks/usePrediction';
import { ChartSkeleton, NewsLoadingSkeleton } from '@/components/common/Skeleton';
import '../styles/animations.css'; // Adjust path if needed or keep using App.css globally

// Lazy load heavy components
const PriceChart = lazy(() => import('@/components/charts/PriceChart').then(module => ({ default: module.PriceChart })));
const NewsPanel = lazy(() => import('@/components/widgets/NewsPanel').then(module => ({ default: module.NewsPanel })));

export function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('RELIANCE.NS');
  
  // Fetch data
  const { candlestickData, loading: _pricesLoading } = usePrices(selectedSymbol, 30);
  const { data: sentimentData } = useSentiment(selectedSymbol, 30);
  const { prediction, loading: predictionLoading, error: predictionError, predict, train } = usePrediction();

  const handlePredict = () => {
    predict(selectedSymbol);
  };

  return (
    <div className="dashboard bg-slate-950 min-h-screen text-white relative overflow-hidden">
      {/* Background Gradients */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#135bec]/10 rounded-full blur-[120px] will-change-transform" />
        <div className="absolute top-[20%] right-[-10%] w-[40%] h-[40%] bg-purple-500/8 rounded-full blur-[120px] will-change-transform" />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-indigo-500/8 rounded-full blur-[120px] will-change-transform" />
      </div>

      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Header
        selectedSymbol={selectedSymbol}
        onSymbolChange={setSelectedSymbol}
      />
      
      <main id="main-content" className="main-content pt-28 pb-12 relative z-10">
        <div className="container mx-auto px-6 max-w-7xl">
          {/* Hero Section */}
          <section className="hero-section mb-12 text-center">
            <h2 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 leading-tight">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#135bec] via-blue-400 to-indigo-400">AI-Powered</span>{' '}
              <span className="text-slate-100">Market Predictions</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
              Advanced financial forecasting combining LSTM neural networks with FinBERT sentiment analysis for <span className="text-[#135bec] font-semibold">high-precision</span> next-day price targets.
            </p>
          </section>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
            {/* Chart Column - Takes 2/3 width on desktop, full on tablet/mobile */}
            <div className="md:col-span-2 lg:col-span-2 space-y-4 md:space-y-6">
              <Suspense fallback={<ChartSkeleton />}>
                <PriceChart
                  data={candlestickData}
                  symbol={selectedSymbol}
                />
              </Suspense>
            </div>

            {/* Sidebar - Takes 1/3 width on desktop, full on tablet/mobile */}
            <div className="md:col-span-2 lg:col-span-1 space-y-4 md:space-y-6">
              <PredictionCard
                symbol={selectedSymbol}
                prediction={prediction}
                loading={predictionLoading}
                error={predictionError}
                onPredict={handlePredict}
                onTrain={train}
              />

              <MetricsGrid 
                symbol={selectedSymbol}
              />
              
              <SentimentOverlay
                data={Array.isArray(sentimentData) ? sentimentData.map(s => ({
                  date: s.date,
                  avg_sentiment: s.avg_sentiment !== undefined ? Number(s.avg_sentiment) : null
                })) : []}
                symbol={selectedSymbol}
              />
            </div>
          </div>

          {/* News Section */}
          <section className="news-section">
            <Suspense fallback={<NewsLoadingSkeleton />}>
              <NewsPanel symbol={selectedSymbol} />
            </Suspense>
          </section>
        </div>
      </main>
      
      <Footer />
    </div>
  );
}
