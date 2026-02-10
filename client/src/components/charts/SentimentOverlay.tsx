/**
 * SentimentOverlay Component
 * Displays sentiment gauge with glassmorphism styling.
 */
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SentimentData {
  date: string;
  avg_sentiment: number | null;
}

interface SentimentOverlayProps {
  data: SentimentData[];
  symbol: string;
}

export function SentimentOverlay({ data, symbol }: SentimentOverlayProps) {
  // Calculate average sentiment
  const validData = data.filter((d) => d.avg_sentiment !== null);
  const avgSentiment = validData.length > 0
    ? validData.reduce((sum, d) => sum + (d.avg_sentiment || 0), 0) / validData.length
    : 0;

  const getSentimentLabel = (score: number) => {
    if (score > 0.3) return { label: 'Bullish', icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' };
    if (score < -0.3) return { label: 'Bearish', icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/30' };
    return { label: 'Neutral', icon: Minus, color: 'text-slate-400', bg: 'bg-slate-500/15', border: 'border-slate-500/30' };
  };

  const sentiment = getSentimentLabel(avgSentiment);
  const Icon = sentiment.icon;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-xl p-6 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h4 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <Icon size={18} className="text-[#135bec]" />
          Market Sentiment
        </h4>
        <span className="text-xs text-slate-500 bg-white/5 px-3 py-1.5 rounded-full font-medium border border-white/10">
          {symbol}
        </span>
      </div>
      
      <div className="space-y-6">
        <div className={`rounded-xl border ${sentiment.border} ${sentiment.bg} p-5 text-center transition-all`}>
          <div className="flex items-center justify-center gap-3 mb-2">
            <Icon size={24} className={sentiment.color} />
            <span className={`text-4xl font-bold ${sentiment.color}`}>
              {avgSentiment.toFixed(2)}
            </span>
          </div>
          <span className={`text-sm font-semibold uppercase tracking-wide ${sentiment.color}`}>
            {sentiment.label}
          </span>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-red-400">-1.0 Bearish</span>
            <span className="text-emerald-400">+1.0 Bullish</span>
          </div>
          <div className="relative h-2 bg-white/5 rounded-full overflow-hidden border border-white/10">
            <div 
              className="absolute top-0 h-full w-1 bg-[#135bec] rounded-full shadow-lg shadow-[#135bec]/50 transition-all duration-500"
              style={{ left: `${((avgSentiment + 1) / 2) * 100}%`, transform: 'translateX(-50%)' }}
            />
          </div>
        </div>
      </div>
      
      {validData.length === 0 && (
        <p className="mt-4 text-center text-sm text-slate-500">No sentiment data available</p>
      )}
    </div>
  );
}
