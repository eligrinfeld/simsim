import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Slider } from "./ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip 
} from "recharts";
import { 
  Calculator, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Shield, 
  Target,
  DollarSign,
  RefreshCw,
  Activity,
  Brain,
  BarChart3
} from "lucide-react";
import { RebalancingAlerts } from "./RebalancingAlerts";
import { MonteCarloSimulation } from "./MonteCarloSimulation";
import { MLRiskAnalysis } from "./MLRiskAnalysis";
import { PortfolioBacktesting } from "./PortfolioBacktesting";

interface Position {
  ticker: string;
  shares: number;
  currentPrice: number;
  allocation: number;
  marketValue: number;
  dailyVaR: number;
  beta: number;
  volatility: number;
  maxDrawdown: number;
}

interface RiskMetrics {
  portfolioValue: number;
  portfolioVaR: number;
  portfolioBeta: number;
  sharpeRatio: number;
  maxDrawdown: number;
  diversificationRatio: number;
  expectedReturn: number;
  volatility: number;
}

const mockPositions: Position[] = [
  {
    ticker: "AAPL",
    shares: 100,
    currentPrice: 182.50,
    allocation: 35.2,
    marketValue: 18250,
    dailyVaR: 2.1,
    beta: 1.15,
    volatility: 24.5,
    maxDrawdown: -12.3
  },
  {
    ticker: "MSFT",
    shares: 50,
    currentPrice: 415.20,
    allocation: 40.1,
    marketValue: 20760,
    dailyVaR: 1.8,
    beta: 0.98,
    volatility: 22.1,
    maxDrawdown: -9.8
  },
  {
    ticker: "GOOGL",
    shares: 75,
    currentPrice: 138.40,
    allocation: 20.0,
    marketValue: 10380,
    dailyVaR: 2.5,
    beta: 1.23,
    volatility: 28.2,
    maxDrawdown: -15.1
  },
  {
    ticker: "TSLA",
    shares: 15,
    currentPrice: 245.80,
    allocation: 4.7,
    marketValue: 3687,
    dailyVaR: 4.2,
    beta: 1.67,
    volatility: 45.8,
    maxDrawdown: -28.5
  }
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export function PortfolioManager() {
  const [positions, setPositions] = useState<Position[]>(mockPositions);
  const [portfolioValue, setPortfolioValue] = useState(100000);
  const [riskTolerance, setRiskTolerance] = useState([5]);
  const [activeTab, setActiveTab] = useState("overview");
  const [newPosition, setNewPosition] = useState({
    ticker: "",
    targetAllocation: 0,
    riskScore: 5
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPositions = async () => {
      try {
        const res = await fetch('/data/portfolio_positions.json');
        if (res.ok) {
          const data = await res.json();
          setPositions(data);
        }
      } catch (error) {
        console.warn('Failed to load portfolio positions, using fallback:', error);
      } finally {
        setLoading(false);
      }
    };
    loadPositions();
  }, []);

  // Calculate portfolio risk metrics
  const calculateRiskMetrics = (): RiskMetrics => {
    const totalValue = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
    const portfolioVaR = positions.reduce((sum, pos) => 
      sum + (pos.dailyVaR * pos.allocation / 100), 0
    );
    const portfolioBeta = positions.reduce((sum, pos) => 
      sum + (pos.beta * pos.allocation / 100), 0
    );
    const avgVolatility = positions.reduce((sum, pos) => 
      sum + (pos.volatility * pos.allocation / 100), 0
    );
    const maxDrawdown = Math.min(...positions.map(pos => pos.maxDrawdown));
    
    return {
      portfolioValue: totalValue,
      portfolioVaR,
      portfolioBeta,
      sharpeRatio: 1.25, // Mock calculation
      maxDrawdown,
      diversificationRatio: 0.78, // Mock calculation
      expectedReturn: 12.5, // Mock calculation
      volatility: avgVolatility
    };
  };

  const riskMetrics = calculateRiskMetrics();

  // Position sizing calculator
  const calculateOptimalPosition = (ticker: string, targetAllocation: number, riskScore: number) => {
    const adjustedAllocation = targetAllocation * (riskScore / 10);
    const targetValue = portfolioValue * (adjustedAllocation / 100);
    
    // Mock price for calculation (in real app, would fetch current price)
    const mockPrice = 150;
    const suggestedShares = Math.floor(targetValue / mockPrice);
    
    return {
      suggestedShares,
      targetValue,
      adjustedAllocation
    };
  };

  const getRiskLevel = (value: number) => {
    if (value < 2) return { level: "Low", color: "text-green-600", bg: "bg-green-100" };
    if (value < 4) return { level: "Medium", color: "text-yellow-600", bg: "bg-yellow-100" };
    return { level: "High", color: "text-red-600", bg: "bg-red-100" };
  };

  const allocationData = positions.map(pos => ({
    name: pos.ticker,
    value: pos.allocation,
    marketValue: pos.marketValue
  }));

  const riskData = positions.map(pos => ({
    ticker: pos.ticker,
    var: pos.dailyVaR,
    beta: pos.beta,
    volatility: pos.volatility
  }));

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${riskMetrics.portfolioValue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Expected Return: {riskMetrics.expectedReturn}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio VaR (95%)</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{riskMetrics.portfolioVaR.toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground">
              Daily risk exposure
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Beta</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{riskMetrics.portfolioBeta.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Market correlation
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
            <Shield className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{riskMetrics.sharpeRatio.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              Risk-adjusted return
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Portfolio Management Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="calculator" className="flex items-center gap-2">
            <Calculator className="w-4 h-4" />
            Position Sizing
          </TabsTrigger>
          <TabsTrigger value="rebalancing" className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Rebalancing
          </TabsTrigger>
          <TabsTrigger value="simulation" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Monte Carlo
          </TabsTrigger>
          <TabsTrigger value="ml-analysis" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            ML Analysis
          </TabsTrigger>
          <TabsTrigger value="backtesting" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Backtesting
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Portfolio Allocation */}
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Allocation</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Current position distribution
                </p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={allocationData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {allocationData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      formatter={(value: any, name: any, props: any) => [
                        `${value.toFixed(1)}% ($${props.payload.marketValue.toLocaleString()})`,
                        'Allocation'
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Risk Metrics Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Position Risk Analysis</CardTitle>
                <p className="text-sm text-muted-foreground">
                  VaR and volatility by position
                </p>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={riskData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="ticker" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="var" fill="#ff6b6b" name="VaR %" />
                    <Bar dataKey="volatility" fill="#4ecdc4" name="Volatility %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Current Positions Risk Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Position Risk Breakdown</CardTitle>
              <p className="text-sm text-muted-foreground">
                Detailed risk metrics for each position
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {positions.map((position) => {
                  const riskLevel = getRiskLevel(position.dailyVaR);
                  return (
                    <div key={position.ticker} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div>
                          <h4 className="font-semibold">{position.ticker}</h4>
                          <p className="text-sm text-muted-foreground">
                            {position.shares} shares @ ${position.currentPrice}
                          </p>
                        </div>
                        <Badge className={`${riskLevel.bg} ${riskLevel.color}`}>
                          {riskLevel.level} Risk
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-4 gap-6 text-right">
                        <div>
                          <Label className="text-xs text-muted-foreground">Market Value</Label>
                          <p className="font-semibold">${position.marketValue.toLocaleString()}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Daily VaR</Label>
                          <p className="font-semibold text-red-600">{position.dailyVaR}%</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Beta</Label>
                          <p className="font-semibold">{position.beta}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Max Drawdown</Label>
                          <p className="font-semibold text-red-600">{position.maxDrawdown}%</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Risk Management Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Risk Management Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-yellow-800">High Concentration Risk</p>
                    <p className="text-sm text-yellow-700">
                      Your portfolio has 75.3% allocation in just two positions (AAPL + MSFT). Consider diversifying.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-blue-800">Portfolio Beta Analysis</p>
                    <p className="text-sm text-blue-700">
                      Current beta of {riskMetrics.portfolioBeta.toFixed(2)} indicates moderate market correlation. Consider adding defensive positions.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <Shield className="w-5 h-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-semibold text-green-800">Good Risk-Adjusted Returns</p>
                    <p className="text-sm text-green-700">
                      Sharpe ratio of {riskMetrics.sharpeRatio.toFixed(2)} indicates good risk-adjusted performance.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Position Sizing Calculator Tab */}
        <TabsContent value="calculator" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Position Sizing Calculator
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Calculate optimal position sizes based on risk tolerance
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ticker">Ticker Symbol</Label>
                  <Input
                    id="ticker"
                    placeholder="e.g., AAPL"
                    value={newPosition.ticker}
                    onChange={(e) => setNewPosition(prev => ({ ...prev, ticker: e.target.value.toUpperCase() }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="allocation">Target Allocation (%)</Label>
                  <Input
                    id="allocation"
                    type="number"
                    placeholder="5"
                    value={newPosition.targetAllocation || ""}
                    onChange={(e) => setNewPosition(prev => ({ ...prev, targetAllocation: Number(e.target.value) }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Risk Tolerance: {riskTolerance[0]}/10</Label>
                  <Slider
                    value={riskTolerance}
                    onValueChange={setRiskTolerance}
                    max={10}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                </div>
              </div>

              {newPosition.ticker && newPosition.targetAllocation > 0 && (
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <h4 className="font-semibold mb-3">Position Recommendation</h4>
                  {(() => {
                    const calc = calculateOptimalPosition(
                      newPosition.ticker, 
                      newPosition.targetAllocation, 
                      riskTolerance[0]
                    );
                    return (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <Label className="text-sm text-muted-foreground">Suggested Shares</Label>
                          <p className="text-xl font-semibold">{calc.suggestedShares}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-muted-foreground">Target Value</Label>
                          <p className="text-xl font-semibold">${calc.targetValue.toLocaleString()}</p>
                        </div>
                        <div>
                          <Label className="text-sm text-muted-foreground">Risk-Adjusted Allocation</Label>
                          <p className="text-xl font-semibold">{calc.adjustedAllocation.toFixed(1)}%</p>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rebalancing Tab */}
        <TabsContent value="rebalancing">
          <RebalancingAlerts />
        </TabsContent>

        {/* Monte Carlo Simulation Tab */}
        <TabsContent value="simulation">
          <MonteCarloSimulation />
        </TabsContent>

        {/* ML Analysis Tab */}
        <TabsContent value="ml-analysis">
          <MLRiskAnalysis />
        </TabsContent>

        {/* Backtesting Tab */}
        <TabsContent value="backtesting">
          <PortfolioBacktesting />
        </TabsContent>
      </Tabs>
    </div>
  );
}