/**
 * AssetSelector Component
 * Dropdown for selecting tracked assets.
 */
import './AssetSelector.css';

interface Asset {
  symbol: string;
  name: string;
}

interface AssetSelectorProps {
  assets: Asset[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

export function AssetSelector({ assets, selectedSymbol, onSelect }: AssetSelectorProps) {
  return (
    <div className="asset-selector-container">
      <label htmlFor="asset-select" className="selector-label">
        Select Asset
      </label>
      <select
        id="asset-select"
        className="select asset-select"
        value={selectedSymbol}
        onChange={(e) => onSelect(e.target.value)}
      >
        {assets.map((asset) => (
          <option key={asset.symbol} value={asset.symbol}>
            {asset.symbol} - {asset.name}
          </option>
        ))}
      </select>
    </div>
  );
}
