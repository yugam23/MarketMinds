import { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, RefreshCw, Activity, Brain } from 'lucide-react';
import { PredictionResponse } from '@/types';
import { formatINR } from '@/utils/currency';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Skeleton } from '@/components/common/Skeleton';
import { ErrorState } from '@/components/common/ErrorState';

// Utility for tailwind classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface PredictionCardProps {
  symbol: string;
  prediction: PredictionResponse | null;
  loading: boolean;
  error: string | null;
  onPredict: () => void;
  onTrain?: (symbol: string) => Promise<boolean>;
}

export function PredictionCard({
  symbol,
  prediction,
  loading,
  error,
  onPredict,
  onTrain
}: PredictionCardProps) {
  const [training, setTraining] = useState(false);

  const handleTrain = async () => {
    if (!onTrain) return;
    setTraining(true);
    try {
      const success = await onTrain(symbol);
      if (success) {
         // Poll for completion or just wait
         setTimeout(() => {
           onPredict();
           setTraining(false);
         }, 5000);
      } else {
         setTraining(false);
      }
    } catch (e) {
      setTraining(false);
    }
  };

  const isBullish = prediction?.direction === 'up';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-xl p-6 shadow-lg transition-all hover:border-[#135bec]/30 group min-h-[220px] flex flex-col justify-between"
      )}
    >
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none group-hover:opacity-10 transition-opacity duration-500">
        <Brain size={120} className="text-[#135bec]" />
      </div>

      <div className="relative z-10 flex flex-col h-full justify-between">
        <div>
          <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-1">
            <Activity size={14} className="text-[#135bec]" />
            AI Forecast (24h)
          </h3>
          
          {/* Consensus Label */}
          <div className="mb-4">
            <span className="text-sm font-medium text-slate-500">Consensus</span>
          </div>
          
          <div className="flex items-baseline gap-3 flex-wrap mb-4 min-h-[3rem]" aria-live="polite">
            {loading ? (
               <Skeleton className="h-10 w-48 rounded-lg" />
            ) : error ? (
              <ErrorState message={error} minimal className="w-full py-2 bg-transparent border-0 p-0 text-left items-start" />
            ) : prediction ? (
              <>
                <span className="text-4xl font-bold text-slate-100 tracking-tight" aria-label={`Predicted price: ${formatINR(prediction.predicted_price)}`}>
                  {typeof prediction.predicted_price === 'number' ? formatINR(prediction.predicted_price) : '---'}
                </span>
                <span className={cn(
                  "flex items-center text-sm font-semibold px-3 py-1 rounded-full transition-colors animate-in fade-in zoom-in duration-300",
                  isBullish ? "text-emerald-400 bg-emerald-400/15 border border-emerald-400/20" : "text-red-400 bg-red-400/15 border border-red-400/20"
                )}
                aria-label={`Prediction trend: ${isBullish ? 'Up' : 'Down'} by ${prediction.change_percent} percent`}
                >
                  {isBullish ? <TrendingUp size={14} className="mr-1" aria-hidden="true" /> : <TrendingDown size={14} className="mr-1" aria-hidden="true" />}
                  {prediction.change_percent}%
                </span>
              </>
            ) : (
                <span className="text-xl text-slate-500 italic">No Model Available</span>
            )}
          </div>

          {/* Prediction Badge */}
          {loading ? (
            <Skeleton className="h-6 w-24 rounded-lg" />
          ) : prediction && !error && (
            <div className="inline-flex animate-in fade-in slide-in-from-bottom-2 duration-500 delay-100">
              <span className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wide shadow-sm",
                isBullish 
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" 
                  : "bg-red-500/20 text-red-300 border border-red-500/30"
              )}>
                {isBullish ? 'Strong Buy' : 'Strong Sell'}
              </span>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-between items-end">
           {loading ? (
             <Skeleton className="h-4 w-32" />
           ) : prediction && !error && (
             <div className="text-xs text-slate-500 animate-in fade-in duration-700">
                <div>Confidence: <span className="text-[#135bec] font-medium">High</span></div>
                {Number(prediction.sentiment_contribution) !== 0 && (
                  <div className="mt-1 flex items-center gap-1">
                    Sentiment Impact: 
                    <span className={Number(prediction.sentiment_contribution) > 0 ? "text-emerald-400" : "text-red-400"}>
                        {Number(prediction.sentiment_contribution) > 0 ? "+" : ""}{Number(prediction.sentiment_contribution).toFixed(4)}
                    </span>
                  </div>
                )}
             </div>
           )}

           <button
             onClick={prediction ? onPredict : handleTrain}
             disabled={training || loading}
             aria-label={training ? "Training model in progress" : prediction ? "Refresh prediction" : "Train AI model"}
             className={cn(
               "flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold transition-all text-sm ml-auto z-20",
               training || loading
                 ? "bg-[#135bec]/20 text-[#135bec]/60 cursor-wait"
                 : "bg-gradient-to-br from-[#135bec] to-[#0d47c4] hover:shadow-lg hover:shadow-[#135bec]/30 text-white active:scale-95 text-high-contrast"
             )}
           >
             <RefreshCw size={14} className={cn("transition-transform", (training || loading) && "animate-spin")} aria-hidden="true" />
             {training ? "Training..." : prediction ? "Refresh" : "Train Model"}
           </button>
        </div>
      </div>
    </motion.div>
  );
}
