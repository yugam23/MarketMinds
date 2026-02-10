import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Newspaper, ExternalLink } from 'lucide-react';
import { getHeadlines } from '@/services/api';
import { Headline } from '@/types';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NewsPanelProps {
  symbol: string;
}

import { NewsLoadingSkeleton } from '@/components/common/Skeleton';
import { ErrorState } from '@/components/common/ErrorState';

export function NewsPanel({ symbol }: NewsPanelProps) {
  const [headlines, setHeadlines] = useState<Headline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getHeadlines(symbol);
        setHeadlines(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch news", err);
        setError("Failed to load latest news");
      } finally {
        setLoading(false);
      }
    };

    if (symbol) fetchNews();
  }, [symbol]);

  const getSentimentColor = (score?: number) => {
    if (score === undefined) return "border-slate-700 bg-slate-500/10 text-slate-400";
    if (score > 0.2) return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    if (score < -0.2) return "border-red-500/30 bg-red-500/10 text-red-400";
    return "border-slate-500/30 bg-slate-500/10 text-slate-400";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <Newspaper size={18} className="text-[#135bec]" />
          Market Intelligence
        </h3>
        <span className="text-xs text-slate-500 bg-white/5 px-3 py-1.5 rounded-full font-medium border border-white/10">
          {headlines.length} Sources
        </span>
      </div>

      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
        {loading ? (
           <NewsLoadingSkeleton />
        ) : error ? (
           <ErrorState message={error} minimal />
        ) : headlines.length > 0 ? (
          headlines.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={cn(
                "p-4 rounded-xl border backdrop-blur-md transition-all hover:bg-white/[0.08] hover:border-[#135bec]/20 card-hover",
                getSentimentColor(item.sentiment_score)
              )}
            >
              <div className="flex justify-between items-start gap-4">
                <a 
                  href={item.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="font-medium text-sm text-slate-200 hover:text-[#135bec] transition-colors leading-snug line-clamp-2 focus:outline-none focus:underline"
                  aria-label={`Read full article: ${item.title} (opens in a new tab)`}
                >
                  {item.title}
                </a>
                <ExternalLink size={14} className="flex-shrink-0 text-slate-500 hover:text-[#135bec] transition-colors" aria-hidden="true" />
              </div>
              <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                <span className="font-medium">{item.source || 'Unknown Source'}</span>
                <span className="font-mono">
                   {item.date ? new Date(item.date).toLocaleDateString() : ''}
                </span>
              </div>
            </motion.div>
          ))
        ) : (
          <div className="text-center py-8 text-slate-500 bg-white/[0.02] rounded-xl border border-white/5">
            No recent news found for {symbol}.
          </div>
        )}
      </div>
       <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(19, 91, 236, 0.3);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(19, 91, 236, 0.5);
        }
      `}</style>
    </div>
  );
}
