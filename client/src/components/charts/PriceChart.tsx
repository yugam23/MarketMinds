/**
 * PriceChart Component
 * Real-time price visualization using Recharts.
 */
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';
import { formatINR } from '@/utils/currency';
import { CandlestickData } from '@/types';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { TrendingUp } from 'lucide-react';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

import { ChartSkeleton } from '@/components/common/Skeleton';
import { ErrorState } from '@/components/common/ErrorState';

interface PriceChartProps {
  data: CandlestickData[];
  symbol: string;
  loading?: boolean;
  error?: string | null;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string | number;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length && label != null) {
    return (
      <div className="bg-slate-900/95 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-xl">
        <p className="text-slate-400 text-xs mb-1">{format(new Date(label), 'MMM dd, yyyy')}</p>
        <p className="text-slate-100 font-mono font-bold text-lg">
          {formatINR(payload[0].value)}
        </p>
      </div>
    );
  }
  return null;
};

import { memo, useMemo } from 'react';

// ... imports remain the same

export const PriceChart = memo(({ data, symbol, loading, error }: PriceChartProps) => {
  if (loading) {
    return <ChartSkeleton />;
  }

  if (error) {
    return (
      <div className="h-[400px] flex items-center justify-center border border-white/10 rounded-2xl bg-white/[0.05] backdrop-blur-xl">
        <ErrorState message={error} />
      </div>
    );
  }

  // Memoize chart data transformation
  const chartData = useMemo(() => {
    return data
      .map(d => ({
        time: d.time,
        price: Number(d.close),
      }))
      .filter(d => !isNaN(d.price));
  }, [data]);

  // Memoize domain calculations
  const { minPrice, maxPrice, isPositive, padding } = useMemo(() => {
    if (chartData.length === 0) {
      return { minPrice: 0, maxPrice: 0, isPositive: false, padding: 0 };
    }
    const prices = chartData.map(d => d.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    return {
      minPrice: min,
      maxPrice: max,
      isPositive: chartData.length > 1 && chartData[chartData.length - 1].price >= chartData[0].price,
      padding: (max - min) * 0.1
    };
  }, [chartData]);

  if (data.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center border border-white/10 rounded-2xl bg-white/[0.05] backdrop-blur-xl">
        <ErrorState message="No price data available" minimal />
      </div>
    );
  }

  return (
    <div 
      className="relative h-[400px] w-full bg-white/[0.05] backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-lg"
      role="img"
      aria-label={`Price chart for ${symbol} showing ${isPositive ? 'positive' : 'negative'} trend over the last 30 days.`}
    >
      <div className="absolute top-6 left-6 z-10 space-y-1 bg-slate-900/60 backdrop-blur-sm px-4 py-3 rounded-xl border border-white/5">
        <div className="flex items-center gap-2">
          <TrendingUp size={20} className="text-[#135bec]" aria-hidden="true" />
          <h3 className="text-slate-100 font-semibold text-xl">Live Market Data</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-slate-300 text-base font-semibold">{symbol}</span>
          <span className="text-slate-500 text-sm" aria-hidden="true">•</span>
          <span className={cn(
            "text-xs px-2.5 py-1 rounded-full font-medium", 
            isPositive ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20" : "bg-red-500/15 text-red-400 border border-red-500/20"
          )}>
             30 Days
          </span>
        </div>
      </div>
      
      <div className="w-full h-full pt-20" style={{ minHeight: "300px" }} aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%" minHeight={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={isPositive ? "#10b981" : "#ef4444"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="time" 
              tickFormatter={(str) => format(new Date(str), 'MMM d')}
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              minTickGap={30}
            />
            <YAxis 
              domain={[minPrice - padding, maxPrice + padding]}
              stroke="rgba(255,255,255,0.2)"
              tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(number) => formatINR(number, 0)}
              width={70}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="price" 
              stroke={isPositive ? "#10b981" : "#ef4444"} 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorPrice)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
});
