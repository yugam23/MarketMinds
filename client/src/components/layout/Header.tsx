/**
 * Header Component
 * Navigation header with logo and asset selector.
 */
import { LineChart } from 'lucide-react';

interface HeaderProps {
  selectedSymbol: string;
  onSymbolChange: (symbol: string) => void;
}

// Default supported assets
const ASSETS = [
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries' },
  { symbol: 'TCS.NS', name: 'Tata Consultancy Services' },
  { symbol: 'HDFCBANK.NS', name: 'HDFC Bank' },
  { symbol: 'ICICIBANK.NS', name: 'ICICI Bank' },
  { symbol: 'INFY.NS', name: 'Infosys' },
  { symbol: 'HINDUNILVR.NS', name: 'Hindustan Unilever' },
  { symbol: 'ITC.NS', name: 'ITC' },
  { symbol: 'SBIN.NS', name: 'State Bank of India' },
  { symbol: 'BHARTIARTL.NS', name: 'Bharti Airtel' },
  { symbol: 'KOTAKBANK.NS', name: 'Kotak Mahindra Bank' },
];

// Duplicate import removed
import { useMediaQuery } from '@/hooks/use-media-query';

export function Header({ selectedSymbol, onSymbolChange }: HeaderProps) {
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-slate-900/80 backdrop-blur-xl">
      <div className="container mx-auto px-4 md:px-6 h-16 md:h-20 flex items-center justify-between max-w-7xl">
        {/* Logo Section */}
        <div className="flex items-center gap-2 md:gap-3 select-none">
          <div 
             className="flex h-10 w-10 md:h-12 md:w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#135bec]/20 to-[#0d47c4]/20 border border-[#135bec]/20 shadow-lg shadow-[#135bec]/10"
             aria-hidden="true"
          >
            <LineChart className="text-[#135bec]" size={isMobile ? 20 : 24} />
          </div>
          <div className="flex flex-col justify-center">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-100 leading-tight">
              MarketMinds
            </h1>
            <span className="text-[10px] md:text-[11px] font-medium uppercase tracking-widest text-[#135bec]/80 hidden sm:block">
              AI Analytics
            </span>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex items-center gap-4" aria-label="Main Navigation">
          <div className="relative group">
            <label htmlFor="asset-select" className="sr-only">Select Stock or Crypto</label>
            <select
              id="asset-select"
              className="
                appearance-none 
                bg-white/[0.05] backdrop-blur-md
                border border-white/10
                rounded-lg 
                pl-3 pr-8 py-2 md:px-5 md:py-2.5 md:pr-12
                text-xs md:text-sm font-medium text-slate-200
                outline-none 
                focus:border-[#135bec]/50 focus:ring-2 focus:ring-[#135bec]/20
                transition-all duration-200
                hover:bg-white/[0.08] hover:border-white/20
                cursor-pointer 
                w-[140px] md:w-auto md:min-w-[220px]
                truncate
              "
              value={selectedSymbol}
              onChange={(e) => onSymbolChange(e.target.value)}
              aria-label="Select asset to analyze"
            >
              {ASSETS.map((asset) => (
                <option key={asset.symbol} value={asset.symbol} className="bg-slate-900 text-slate-100">
                  {isMobile ? asset.symbol : `${asset.symbol} - ${asset.name}`}
                </option>
              ))}
            </select>
            <div className="absolute right-3 md:right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
}
