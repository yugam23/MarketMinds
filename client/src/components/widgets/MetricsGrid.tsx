/**
 * MetricsGrid Component
 * Displays key financial metrics (Market Cap, P/E Ratio, Beta, Volatility)
 */
import { TrendingUp, Activity, BarChart3, AlertCircle } from 'lucide-react';

// MetricItem interface removed as it is no longer used explicitly

interface MetricsGridProps {
  symbol?: string;
  loading?: boolean;
  metrics?: {
    marketCap?: string;
    peRatio?: number;
    beta?: number;
    volatility?: string;
  };
}

import { Skeleton } from '@/components/common/Skeleton';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function MetricsGrid({ metrics, loading }: MetricsGridProps) {
  // Default values or fetched metrics
  const defaultMetrics = [
    {
      label: 'Market Cap',
      value: metrics?.marketCap || '2.8T',
      icon: <TrendingUp size={20} />,
      color: 'text-blue-400',
      bgColor: 'bg-blue-400/10',
      borderColor: 'border-blue-400/20',
    },
    {
      label: 'P/E Ratio',
      value: metrics?.peRatio || '28.4',
      icon: <BarChart3 size={20} />,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10',
      borderColor: 'border-emerald-400/20',
    },
    {
      label: 'Beta',
      value: metrics?.beta || '1.28',
      icon: <Activity size={20} />,
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/10',
      borderColor: 'border-purple-400/20',
    },
    {
      label: 'Volatility',
      value: metrics?.volatility || 'Medium',
      icon: <AlertCircle size={20} />,
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      borderColor: 'border-amber-400/20',
    },
  ];

  return (
    <div className="w-full">
      <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
        <Activity size={18} className="text-[#135bec]" />
        Key Metrics
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        {loading ? (
           [...Array(4)].map((_, i) => (
             <div key={i} className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 animate-pulse">
                <div className="flex items-center gap-2 mb-3">
                   <Skeleton className="h-8 w-8 rounded-lg" />
                   <Skeleton className="h-3 w-16" />
                </div>
                <Skeleton className="h-6 w-24" />
             </div>
           ))
        ) : (
          defaultMetrics.map((metric, index) => (
            <div
              key={index}
              className={cn(
                "group relative overflow-hidden bg-white/[0.03] backdrop-blur-md border border-white/[0.08] rounded-xl p-4 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg card-hover",
                `hover:${metric.borderColor}`
              )}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={cn("p-2 rounded-lg transition-colors group-hover:bg-opacity-20", metric.bgColor, metric.color)}>
                  {metric.icon}
                </div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  {metric.label}
                </span>
              </div>
              
              <div className="text-2xl font-bold text-slate-100 tracking-tight">
                {metric.value}
              </div>
              
              {/* Decorative gradient blob */}
              <div className={cn(
                "absolute -right-4 -bottom-4 w-16 h-16 rounded-full blur-2xl opacity-0 group-hover:opacity-20 transition-opacity duration-500",
                metric.color.replace('text-', 'bg-')
              )} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
