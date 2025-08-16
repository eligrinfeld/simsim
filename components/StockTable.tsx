import { Badge } from "./ui/badge";

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

interface StockTableProps {
  data: Stock[];
  type: "long" | "short";
}

export function StockTable({ data, type }: StockTableProps) {
  const getStrategyBadge = (strategy: string) => {
    // Map strategy names to their types for styling
    const strategyTypeMap: { [key: string]: string } = {
      'ttm_squeeze': 'momentum',
      'kama': 'momentum',
      'hma': 'momentum',
      'supertrend_adx': 'trend',
      'donchian_turtle': 'trend',
      'ichimoku_cloud': 'trend',
      'billwilliams_alligator': 'trend',
      'avwap_stack': 'trend',
      'dmi_adx_cross': 'trend',
      'fractal_bos': 'structure',
      'keltner_bollinger': 'momentum',
      'chande_kroll': 'risk-management',
      'connors_rsi': 'mean-reversion'
    };

    const strategyKey = strategy.toLowerCase().replace(/[^a-z]/g, '_');
    const styleClass = strategyTypeMap[strategyKey] || 'momentum';

    return <Badge className={`badge ${styleClass}`}>{strategy}</Badge>;
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) {
      return <Badge className="badge high-confidence">High</Badge>;
    } else if (confidence >= 60) {
      return <Badge className="badge medium-confidence">Med</Badge>;
    } else {
      return <Badge className="badge low-confidence">Low</Badge>;
    }
  };

  const formatPercentage = (value: number) => {
    const isPositive = value >= 0;
    const className = isPositive ? "percentage positive" : "percentage negative";
    return <span className={className}>{isPositive ? '+' : ''}{value.toFixed(1)}%</span>;
  };

  return (
    <div className="table-container">
      <table className="data-table">
        <thead className="table-header">
          <tr>
            <th>Ticker</th>
            <th>Strategy</th>
            <th>Confidence</th>
            <th>Current Price</th>
            <th>Target Price</th>
            <th>Upside Potential</th>
            <th>1D Forecast</th>
            <th>1W Forecast</th>
            <th>1M Forecast</th>
            <th>Volume</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {data.map((stock, index) => (
            <tr key={index} className="table-row">
              <td className="table-cell primary">
                <div>
                  <div className="font-semibold">{stock.ticker}</div>
                  <div className="text-xs" style={{color: 'var(--muted-foreground)'}}>{stock.company}</div>
                </div>
              </td>
              <td className="table-cell">
                {getStrategyBadge(stock.strategy)}
              </td>
              <td className="table-cell">
                <div className="flex items-center space-x-2">
                  {getConfidenceBadge(stock.confidence)}
                  <span className="text-sm">{stock.confidence.toFixed(1)}%</span>
                </div>
              </td>
              <td className="table-cell secondary">
                ${stock.currentPrice.toFixed(2)}
              </td>
              <td className="table-cell secondary">
                ${stock.targetPrice.toFixed(2)}
              </td>
              <td className="table-cell">
                {formatPercentage(stock.upsidePotential)}
              </td>
              <td className="table-cell">
                {formatPercentage(stock.forecast1d)}
              </td>
              <td className="table-cell">
                {formatPercentage(stock.forecast1w)}
              </td>
              <td className="table-cell">
                {formatPercentage(stock.forecast1m)}
              </td>
              <td className="table-cell secondary">
                {stock.volume}
              </td>
              <td className="table-cell secondary text-xs">
                {stock.lastUpdated}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}