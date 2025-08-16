import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

import { Badge } from "./ui/badge";
import { TrendingUp, TrendingDown, Activity, Calculator } from "lucide-react";
import { StockTable } from "./StockTable";
import { StockManager } from "./StockManager";
import { PortfolioManager } from "./PortfolioManager";

// Mock data for demonstration
const longStrategyStocks = [
  {
    ticker: "AAPL",
    company: "Apple Inc.",
    strategy: "Momentum",
    confidence: 85,
    upsidePotential: 12.5,
    currentPrice: 182.50,
    targetPrice: 205.30,
    forecast1d: 1.2,
    forecast1w: 3.8,
    forecast1m: 8.5,
    volume: "2.1M",
    lastUpdated: "2 min ago"
  },
  {
    ticker: "MSFT",
    company: "Microsoft Corp.",
    strategy: "Value",
    confidence: 78,
    upsidePotential: 15.3,
    currentPrice: 415.20,
    targetPrice: 478.70,
    forecast1d: 0.8,
    forecast1w: 4.2,
    forecast1m: 11.8,
    volume: "1.8M",
    lastUpdated: "1 min ago"
  },
  {
    ticker: "GOOGL",
    company: "Alphabet Inc.",
    strategy: "Growth",
    confidence: 82,
    upsidePotential: 18.7,
    currentPrice: 138.40,
    targetPrice: 164.30,
    forecast1d: 1.5,
    forecast1w: 5.1,
    forecast1m: 14.2,
    volume: "3.2M",
    lastUpdated: "3 min ago"
  },
  {
    ticker: "TSLA",
    company: "Tesla Inc.",
    strategy: "Momentum",
    confidence: 75,
    upsidePotential: 22.1,
    currentPrice: 245.80,
    targetPrice: 300.20,
    forecast1d: 2.1,
    forecast1w: 6.8,
    forecast1m: 16.5,
    volume: "4.1M",
    lastUpdated: "1 min ago"
  },
  {
    ticker: "NVDA",
    company: "NVIDIA Corp.",
    strategy: "Growth",
    confidence: 88,
    upsidePotential: 25.4,
    currentPrice: 875.30,
    targetPrice: 1098.50,
    forecast1d: 1.8,
    forecast1w: 7.2,
    forecast1m: 19.8,
    volume: "5.6M",
    lastUpdated: "2 min ago"
  }
];

const shortStrategyStocks = [
  {
    ticker: "NFLX",
    company: "Netflix Inc.",
    strategy: "Mean Reversion",
    confidence: 72,
    upsidePotential: -8.5,
    currentPrice: 485.20,
    targetPrice: 444.10,
    forecast1d: -0.8,
    forecast1w: -2.1,
    forecast1m: -6.8,
    volume: "1.2M",
    lastUpdated: "4 min ago"
  },
  {
    ticker: "ZOOM",
    company: "Zoom Video",
    strategy: "Technical",
    confidence: 69,
    upsidePotential: -12.3,
    currentPrice: 68.50,
    targetPrice: 60.10,
    forecast1d: -1.2,
    forecast1w: -3.5,
    forecast1m: -9.1,
    volume: "0.8M",
    lastUpdated: "5 min ago"
  },
  {
    ticker: "PELOTON",
    company: "Peloton Interactive",
    strategy: "Fundamental",
    confidence: 80,
    upsidePotential: -15.7,
    currentPrice: 4.25,
    targetPrice: 3.58,
    forecast1d: -1.8,
    forecast1w: -4.2,
    forecast1m: -11.5,
    volume: "2.5M",
    lastUpdated: "3 min ago"
  }
];

export function StockDashboard() {
  const [activeTab, setActiveTab] = useState("long");
  const [longData, setLongData] = useState(longStrategyStocks);
  const [shortData, setShortData] = useState(shortStrategyStocks);
  const [loading, setLoading] = useState(true);

  const getUniqueStrategies = (data: any[]) => {
    const strategies = [...new Set(data.map(stock => stock.strategy))];
    return strategies.slice(0, 3); // Show max 3 strategies to avoid overflow
  };

  const loadStockData = async () => {
    try {
      // Add cache-busting timestamp to prevent browser caching
      const timestamp = new Date().getTime();
      const [longRes, shortRes] = await Promise.all([
        fetch(`/data/stocks_long.json?t=${timestamp}`).then(r => r.json()).catch(() => longStrategyStocks),
        fetch(`/data/stocks_short.json?t=${timestamp}`).then(r => r.json()).catch(() => shortStrategyStocks)
      ]);

      setLongData(longRes);
      setShortData(shortRes);
      console.log(`📊 Loaded ${longRes.length} long and ${shortRes.length} short positions`);
    } catch (error) {
      console.error('Error loading stock data:', error);
      setLongData(longStrategyStocks);
      setShortData(shortStrategyStocks);
    }
  };

  const handleAddStock = async (ticker: string) => {
    try {
      setLoading(true);
      console.log(`🔍 Adding ${ticker} to dashboard...`);

      // Call the Python service to add the stock
      const response = await fetch('/api/add-stock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), action: 'add' }),
      });

      const responseData = await response.json();

      if (response.ok) {
        console.log(`✅ API Success:`, responseData);

        // Wait a moment for file system to update
        await new Promise(resolve => setTimeout(resolve, 500));

        // Reload the data
        await loadStockData();
        console.log(`✅ Added ${ticker} to dashboard successfully!`);

        // Show success message
        alert(`✅ Successfully added ${ticker} to dashboard!`);
      } else {
        console.error(`❌ API Error:`, responseData);
        alert(`Failed to add ${ticker}: ${responseData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error adding stock:', error);
      alert(`Error adding ${ticker}: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveStock = async (ticker: string, type: 'long' | 'short') => {
    try {
      setLoading(true);
      console.log(`🗑️ Removing ${ticker} from dashboard...`);

      // Call the Python service to remove the stock
      const response = await fetch('/api/add-stock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), action: 'remove' }),
      });

      const responseData = await response.json();

      if (response.ok) {
        console.log(`✅ API Success:`, responseData);

        // Wait a moment for file system to update
        await new Promise(resolve => setTimeout(resolve, 500));

        // Reload the data to ensure consistency
        await loadStockData();
        console.log(`✅ Removed ${ticker} from dashboard successfully!`);

        // Show success message
        alert(`✅ Successfully removed ${ticker} from dashboard!`);
      } else {
        console.error(`❌ API Error:`, responseData);
        alert(`Failed to remove ${ticker}: ${responseData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error removing stock:', error);
      alert(`Error removing ${ticker}: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initializeData = async () => {
      await loadStockData();
      setLoading(false);
    };

    initializeData();
  }, []);

  const totalLongUpside = longData.reduce((sum, stock) => sum + stock.upsidePotential, 0);
  const totalShortUpside = shortData.reduce((sum, stock) => sum + Math.abs(stock.upsidePotential), 0);
  const avgLongConfidence = longData.length > 0 ? longData.reduce((sum, stock) => sum + stock.confidence, 0) / longData.length : 0;
  const avgShortConfidence = shortData.length > 0 ? shortData.reduce((sum, stock) => sum + stock.confidence, 0) / shortData.length : 0;

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="dashboard-title">Stock Trading Dashboard</h1>
            <p className="dashboard-subtitle">
              Monitor your long and short strategy positions with portfolio management
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="live-indicator">
              <div className="live-dot"></div>
              Live Data
            </div>
            <span className="text-sm text-gray-500">
              Last updated: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="stat-label">Long Positions</div>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>
          <div className="stat-value">{longData.length}</div>
          <div className="stat-change positive">
            Avg. Confidence: {avgLongConfidence.toFixed(1)}%
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="stat-label">Short Positions</div>
            <TrendingDown className="h-5 w-5 text-red-600" />
          </div>
          <div className="stat-value">{shortData.length}</div>
          <div className="stat-change negative">
            Avg. Confidence: {avgShortConfidence.toFixed(1)}%
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="stat-label">Long Upside</div>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>
          <div className="stat-value text-green-600">
            +{totalLongUpside.toFixed(1)}%
          </div>
          <div className="stat-change positive">
            Total potential gain
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="stat-label">Short Upside</div>
            <TrendingDown className="h-5 w-5 text-red-600" />
          </div>
          <div className="stat-value text-red-600">
            +{totalShortUpside.toFixed(1)}%
          </div>
          <div className="stat-change negative">
            Total potential gain
          </div>
        </div>
      </div>

      {/* Strategy Selector - Full Width */}
      <div className="strategy-selector-container">
        <div className="strategy-slider">
          <div className="slider-track">
            <div
              className="slider-thumb"
              style={{
                transform: `translateX(${
                  activeTab === 'long' ? '0%' :
                  activeTab === 'short' ? '100%' : '200%'
                })`
              }}
            />
            <button
              className={`slider-option ${activeTab === 'long' ? 'active' : ''}`}
              onClick={() => setActiveTab('long')}
            >
              <TrendingUp className="w-4 h-4" />
              Long Strategy ({longData.length})
            </button>
            <button
              className={`slider-option ${activeTab === 'short' ? 'active' : ''}`}
              onClick={() => setActiveTab('short')}
            >
              <TrendingDown className="w-4 h-4" />
              Short Strategy ({shortData.length})
            </button>
            <button
              className={`slider-option ${activeTab === 'portfolio' ? 'active' : ''}`}
              onClick={() => setActiveTab('portfolio')}
            >
              <Calculator className="w-4 h-4" />
              Portfolio Management
            </button>
          </div>
        </div>
      </div>

      {/* Stock Manager - Only show in Portfolio tab */}
      {activeTab === 'portfolio' && (
        <div style={{ padding: '0 1.5rem' }}>
          <StockManager
            longData={longData}
            shortData={shortData}
            onAddStock={handleAddStock}
            onRemoveStock={handleRemoveStock}
          />
        </div>
      )}

      {/* Content Section */}
      <div className="content-section">
        <div className="section-header">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="section-title">
                {activeTab === 'long' && `Long Strategy Positions`}
                {activeTab === 'short' && `Short Strategy Positions`}
                {activeTab === 'portfolio' && `Portfolio Management`}
              </h2>
              <p className="section-subtitle">
                {activeTab === 'long' && `View AI-selected strategies optimized for upward movement - ${longData.length} active positions`}
                {activeTab === 'short' && `View AI-selected strategies optimized for downward movement - ${shortData.length} active positions`}
                {activeTab === 'portfolio' && `Manage your portfolio: add/remove assets, adjust allocations, and configure risk settings`}
              </p>
            </div>
            {(activeTab === 'long' || activeTab === 'short') && (
              <div className="strategy-summary">
                <div className="text-sm" style={{color: 'var(--muted-foreground)'}}>
                  Strategies: {getUniqueStrategies(activeTab === 'long' ? longData : shortData).join(', ')}
                </div>
                <div className="text-xs mt-1" style={{color: 'var(--muted-foreground)'}}>
                  Based on comprehensive backtesting of 13 HRM strategies
                </div>
              </div>
            )}
          </div>
        </div>

        {activeTab === 'long' && (
          <div className="table-section">
            <StockTable data={longData} type="long" />
          </div>
        )}

        {activeTab === 'short' && (
          <div className="table-section">
            <StockTable data={shortData} type="short" />
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="table-section">
            <PortfolioManager />
          </div>
        )}
      </div>
    </div>
  );
}