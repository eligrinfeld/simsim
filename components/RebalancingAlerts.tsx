import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { 
  AlertTriangle, 
  Bell, 
  TrendingUp, 
  Target, 
  RefreshCw,
  CheckCircle,
  XCircle,
  Settings
} from "lucide-react";
import { Separator } from "./ui/separator";

interface RebalancingAlert {
  id: string;
  ticker: string;
  currentAllocation: number;
  targetAllocation: number;
  drift: number;
  severity: "low" | "medium" | "high";
  recommendation: string;
  estimatedCost: number;
  timeGenerated: Date;
}

interface OptimizationSuggestion {
  type: "reduce" | "increase" | "add" | "remove";
  ticker: string;
  currentWeight: number;
  suggestedWeight: number;
  reason: string;
  expectedImpact: {
    sharpeRatio: number;
    volatility: number;
    expectedReturn: number;
  };
  priority: "high" | "medium" | "low";
}

const mockAlerts: RebalancingAlert[] = [
  {
    id: "1",
    ticker: "AAPL",
    currentAllocation: 35.2,
    targetAllocation: 25.0,
    drift: 10.2,
    severity: "high",
    recommendation: "Reduce AAPL position by $5,300 to maintain target allocation",
    estimatedCost: 25.50,
    timeGenerated: new Date(Date.now() - 1000 * 60 * 15) // 15 minutes ago
  },
  {
    id: "2",
    ticker: "MSFT",
    currentAllocation: 40.1,
    targetAllocation: 30.0,
    drift: 10.1,
    severity: "high",
    recommendation: "Reduce MSFT position by $5,200 to maintain target allocation",
    estimatedCost: 31.20,
    timeGenerated: new Date(Date.now() - 1000 * 60 * 12) // 12 minutes ago
  },
  {
    id: "3",
    ticker: "GOOGL",
    currentAllocation: 20.0,
    targetAllocation: 25.0,
    drift: -5.0,
    severity: "medium",
    recommendation: "Increase GOOGL position by $2,500 to reach target allocation",
    estimatedCost: 18.75,
    timeGenerated: new Date(Date.now() - 1000 * 60 * 8) // 8 minutes ago
  }
];

const mockOptimizations: OptimizationSuggestion[] = [
  {
    type: "add",
    ticker: "VTI",
    currentWeight: 0,
    suggestedWeight: 15,
    reason: "Add broad market ETF to reduce concentration risk and improve diversification",
    expectedImpact: {
      sharpeRatio: 0.15,
      volatility: -3.2,
      expectedReturn: 0.8
    },
    priority: "high"
  },
  {
    type: "reduce",
    ticker: "TSLA",
    currentWeight: 4.7,
    suggestedWeight: 2.0,
    reason: "Reduce high-volatility position to lower portfolio risk while maintaining growth exposure",
    expectedImpact: {
      sharpeRatio: 0.08,
      volatility: -2.1,
      expectedReturn: -0.3
    },
    priority: "medium"
  },
  {
    type: "add",
    ticker: "BND",
    currentWeight: 0,
    suggestedWeight: 10,
    reason: "Add bond allocation to provide downside protection during market volatility",
    expectedImpact: {
      sharpeRatio: 0.12,
      volatility: -4.5,
      expectedReturn: -1.2
    },
    priority: "medium"
  }
];

export function RebalancingAlerts() {
  const [alerts, setAlerts] = useState<RebalancingAlert[]>(mockAlerts);
  const [optimizations, setOptimizations] = useState<OptimizationSuggestion[]>(mockOptimizations);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [autoRebalance, setAutoRebalance] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-red-600 bg-red-100 border-red-200";
      case "medium": return "text-yellow-600 bg-yellow-100 border-yellow-200";
      case "low": return "text-blue-600 bg-blue-100 border-blue-200";
      default: return "text-gray-600 bg-gray-100 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-600";
      case "medium": return "text-yellow-600";
      case "low": return "text-green-600";
      default: return "text-gray-600";
    }
  };

  const formatTimeAgo = (date: Date) => {
    const minutes = Math.floor((Date.now() - date.getTime()) / (1000 * 60));
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const executeRebalancing = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
    // In a real app, this would trigger actual trading
  };

  const dismissAlert = (alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Automated Rebalancing</h3>
          <p className="text-sm text-muted-foreground">
            Monitor portfolio drift and receive optimization suggestions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={alertsEnabled ? "default" : "outline"}
            size="sm"
            onClick={() => setAlertsEnabled(!alertsEnabled)}
          >
            <Bell className="w-4 h-4 mr-1" />
            {alertsEnabled ? "Alerts On" : "Alerts Off"}
          </Button>
          <Button
            variant={autoRebalance ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRebalance(!autoRebalance)}
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            {autoRebalance ? "Auto: On" : "Auto: Off"}
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            Active Rebalancing Alerts ({alerts.length})
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Positions that have drifted from their target allocations
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <p className="text-lg font-semibold">Portfolio is Balanced</p>
              <p className="text-sm text-muted-foreground">
                All positions are within their target allocation ranges
              </p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className={`p-4 border rounded-lg ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className="bg-white">
                        {alert.ticker}
                      </Badge>
                      <Badge variant={alert.severity === "high" ? "destructive" : "secondary"}>
                        {alert.drift > 0 ? "+" : ""}{alert.drift.toFixed(1)}% drift
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatTimeAgo(alert.timeGenerated)}
                      </span>
                    </div>
                    
                    <p className="text-sm font-medium mb-2">{alert.recommendation}</p>
                    
                    <div className="flex items-center gap-4 text-xs">
                      <div>
                        <span className="text-muted-foreground">Current: </span>
                        <span className="font-semibold">{alert.currentAllocation}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Target: </span>
                        <span className="font-semibold">{alert.targetAllocation}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Est. Cost: </span>
                        <span className="font-semibold">${alert.estimatedCost}</span>
                      </div>
                    </div>

                    <div className="mt-2">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                        <span>Allocation Progress</span>
                      </div>
                      <Progress 
                        value={(alert.currentAllocation / alert.targetAllocation) * 100} 
                        className="h-2"
                      />
                    </div>
                  </div>
                  
                  <div className="flex gap-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => executeRebalancing(alert.id)}
                      className="bg-white text-primary hover:bg-primary/10"
                    >
                      Execute
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => dismissAlert(alert.id)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <XCircle className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Portfolio Optimization Suggestions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Portfolio Optimization Suggestions
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            AI-powered recommendations to improve risk-adjusted returns
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {optimizations.map((opt, index) => (
            <div key={index} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Badge variant={opt.type === "add" ? "default" : 
                    opt.type === "increase" ? "secondary" : "outline"}>
                    {opt.type.charAt(0).toUpperCase() + opt.type.slice(1)} {opt.ticker}
                  </Badge>
                  <Badge className={getPriorityColor(opt.priority)}>
                    {opt.priority.charAt(0).toUpperCase() + opt.priority.slice(1)} Priority
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground">
                  {opt.currentWeight}% → {opt.suggestedWeight}%
                </div>
              </div>
              
              <p className="text-sm mb-3">{opt.reason}</p>
              
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div className="text-center p-2 bg-muted rounded">
                  <div className="font-semibold text-green-600">
                    +{opt.expectedImpact.sharpeRatio.toFixed(2)}
                  </div>
                  <div className="text-muted-foreground">Sharpe Ratio</div>
                </div>
                <div className="text-center p-2 bg-muted rounded">
                  <div className={`font-semibold ${opt.expectedImpact.volatility < 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {opt.expectedImpact.volatility > 0 ? '+' : ''}{opt.expectedImpact.volatility.toFixed(1)}%
                  </div>
                  <div className="text-muted-foreground">Volatility</div>
                </div>
                <div className="text-center p-2 bg-muted rounded">
                  <div className={`font-semibold ${opt.expectedImpact.expectedReturn > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {opt.expectedImpact.expectedReturn > 0 ? '+' : ''}{opt.expectedImpact.expectedReturn.toFixed(1)}%
                  </div>
                  <div className="text-muted-foreground">Expected Return</div>
                </div>
              </div>
              
              <div className="flex gap-2 mt-3">
                <Button size="sm" variant="outline">
                  Apply Suggestion
                </Button>
                <Button size="sm" variant="ghost">
                  Learn More
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Rebalancing History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-green-600" />
            Recent Rebalancing Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <div>
                  <p className="text-sm font-semibold">Rebalancing Completed</p>
                  <p className="text-xs text-muted-foreground">
                    Reduced NVDA by 2.1% and increased VTI allocation
                  </p>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">
                2 hours ago
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-blue-600" />
                <div>
                  <p className="text-sm font-semibold">Auto-Rebalancing Activated</p>
                  <p className="text-xs text-muted-foreground">
                    Portfolio will automatically rebalance when drift exceeds 5%
                  </p>
                </div>
              </div>
              <div className="text-xs text-muted-foreground">
                1 day ago
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}