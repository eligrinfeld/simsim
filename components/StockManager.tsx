import React, { useState } from 'react';
import { Badge } from "./ui/badge";
import { Plus, X, Search, TrendingUp, TrendingDown, Calculator, Coins } from "lucide-react";

interface Stock {
  ticker: string;
  company: string;
  strategy: string;
  confidence: number;
  upsidePotential: number;
  currentPrice: number;
  targetPrice: number;
  forecast1d: number;
  forecast1w: number;
  forecast1m: number;
  volume: string;
  lastUpdated: string;
}

interface StockManagerProps {
  longData: Stock[];
  shortData: Stock[];
  onAddStock: (ticker: string) => void;
  onRemoveStock: (ticker: string, type: 'long' | 'short') => void;
}

export function StockManager({ longData, shortData, onAddStock, onRemoveStock }: StockManagerProps) {
  const [isAddingStock, setIsAddingStock] = useState(false);
  const [newTicker, setNewTicker] = useState('');
  const [searchResults, setSearchResults] = useState<string[]>([]);

  // Popular stock and crypto suggestions
  const popularAssets = [
    // Popular Stocks
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX',
    'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'UBER', 'SPOT',
    'COIN', 'SQ', 'ROKU', 'ZM', 'SNOW', 'PLTR', 'RBLX', 'HOOD',

    // Major Cryptocurrencies
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD',
    'SOL-USD', 'DOT-USD', 'MATIC-USD', 'AVAX-USD', 'LINK-USD', 'UNI-USD',
    'ATOM-USD', 'LTC-USD', 'BCH-USD', 'ALGO-USD', 'VET-USD', 'ICP-USD'
  ];

  const allCurrentTickers = [...longData.map(s => s.ticker), ...shortData.map(s => s.ticker)];

  const handleSearch = (query: string) => {
    setNewTicker(query.toUpperCase());
    if (query.length >= 1) {
      const filtered = popularAssets
        .filter(ticker =>
          ticker.includes(query.toUpperCase()) &&
          !allCurrentTickers.includes(ticker)
        )
        .slice(0, 8);
      setSearchResults(filtered);
    } else {
      setSearchResults([]);
    }
  };

  const handleAddStock = (ticker: string) => {
    if (ticker && !allCurrentTickers.includes(ticker)) {
      onAddStock(ticker);
      setNewTicker('');
      setSearchResults([]);
      setIsAddingStock(false);
    }
  };

  const handleRemoveStock = (ticker: string) => {
    const isLong = longData.some(s => s.ticker === ticker);
    const isShort = shortData.some(s => s.ticker === ticker);
    
    if (isLong) {
      onRemoveStock(ticker, 'long');
    } else if (isShort) {
      onRemoveStock(ticker, 'short');
    }
  };

  const getPositionIcon = (ticker: string) => {
    const isLong = longData.some(s => s.ticker === ticker);
    const isShort = shortData.some(s => s.ticker === ticker);
    const isCrypto = ticker.includes('-USD');

    if (isCrypto) {
      if (isLong) return <Coins className="w-4 h-4 text-green-600" />;
      if (isShort) return <Coins className="w-4 h-4 text-red-600" />;
      return <Coins className="w-4 h-4 text-orange-500" />;
    }

    if (isLong) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (isShort) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Calculator className="w-4 h-4 text-gray-400" />;
  };

  const getPositionBadge = (ticker: string) => {
    const isLong = longData.some(s => s.ticker === ticker);
    const isShort = shortData.some(s => s.ticker === ticker);
    
    if (isLong) return <Badge className="badge trend text-xs">Long</Badge>;
    if (isShort) return <Badge className="badge risk-management text-xs">Short</Badge>;
    return null;
  };

  return (
    <div className="stock-manager">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="section-title">Portfolio Management</h3>
          <p className="section-subtitle">
            Add or remove stocks & crypto from your trading portfolio
          </p>
        </div>
        <button
          onClick={() => setIsAddingStock(!isAddingStock)}
          className="add-stock-button"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Asset
        </button>
      </div>

      {/* Add Stock Interface */}
      {isAddingStock && (
        <div className="add-stock-section">
          <div className="search-container">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Enter ticker (e.g., AAPL, BTC-USD, ETH-USD)"
              value={newTicker}
              onChange={(e) => handleSearch(e.target.value)}
              className="search-input"
              autoFocus
            />
            {newTicker && (
              <button
                onClick={() => handleAddStock(newTicker)}
                className="add-button"
              >
                Add
              </button>
            )}
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="search-results">
              <div className="text-sm text-gray-600 mb-2">Suggestions:</div>
              <div className="flex flex-wrap gap-2">
                {searchResults.map(ticker => (
                  <button
                    key={ticker}
                    onClick={() => handleAddStock(ticker)}
                    className="suggestion-chip"
                  >
                    {ticker}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Current Stocks List */}
      <div className="current-stocks">
        <div className="stocks-grid">
          {allCurrentTickers.map(ticker => {
            const stock = [...longData, ...shortData].find(s => s.ticker === ticker);
            return (
              <div key={ticker} className="stock-item">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getPositionIcon(ticker)}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">{ticker}</span>
                        {getPositionBadge(ticker)}
                      </div>
                      <div className="text-xs text-gray-500">{stock?.company}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {stock && (
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          {stock.strategy}
                        </div>
                        <div className="text-xs text-gray-500">
                          {stock.confidence.toFixed(1)}% confidence
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => handleRemoveStock(ticker)}
                      className="remove-button"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {allCurrentTickers.length === 0 && (
          <div className="empty-state">
            <Calculator className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No assets in your portfolio</p>
            <p className="text-sm text-gray-500">Add stocks or crypto to start building your portfolio</p>
          </div>
        )}
      </div>

      {/* Portfolio Stats Summary */}
      <div className="stats-summary">
        <div className="flex justify-between text-sm">
          <span>Portfolio Assets: {allCurrentTickers.length}</span>
          <span>Long Positions: {longData.length} | Short Positions: {shortData.length}</span>
        </div>
      </div>
    </div>
  );
}
