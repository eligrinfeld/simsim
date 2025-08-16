import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart
} from "recharts";
import { 
  PlayCircle, 
  Calendar,
  TrendingUp, 
  TrendingDown, 
  Target,
  BarChart3,
  PieChart,
  Award,
  AlertCircle,
  Download,
  Settings,
  Clock
} from "lucide-react";

interface BacktestResult {
  date: string;
  portfolioValue: number;
  benchmarkValue: number;
  alpha: number;
  beta: number;
  sharpeRatio: number;
  maxDrawdown: number;
  volatility: number;
  returns: number;
}

interface PerformanceAttribution {
  sector: string;
  contribution: number;
  weight: number;
  return: number;
  benchmark: number;
  attribution: number;
}

interface BacktestSettings {
  startDate: string;
  endDate: string;
  benchmark: string;
  rebalanceFrequency: string;
  initialValue: number;
}

// Generate mock backtest data iteratively to avoid circular reference
const generateMockBacktestData = (): BacktestResult[] => {
  const data: BacktestResult[] = [];
  let previousPortfolioValue = 100000;
  let previousBenchmarkValue = 100000;
  
  for (let i = 0; i < 252; i++) {
    const baseDate = new Date(2024, 0, 1);
    baseDate.setDate(baseDate.getDate() + i);
    
    // Simulate portfolio performance with some volatility
    const portfolioReturn = 0.0005 + Math.sin(i * 0.02) * 0.002 + (Math.random() - 0.5) * 0.01;
    const benchmarkReturn = 0.0003 + Math.sin(i * 0.015) * 0.001 + (Math.random() - 0.5) * 0.008;
    
    const portfolioValue = i === 0 ? 100000 : previousPortfolioValue * (1 + portfolioReturn);
    const benchmarkValue = i === 0 ? 100000 : previousBenchmarkValue * (1 + benchmarkReturn);
    
    data.push({
      date: baseDate.toISOString().split('T')[0],
      portfolioValue,
      benchmarkValue,
      alpha: (portfolioReturn - benchmarkReturn) * 252 * 100, // Annualized alpha
      beta: 0.95 + Math.sin(i * 0.01) * 0.15,
      sharpeRatio: 1.2 + Math.sin(i * 0.005) * 0.3,
      maxDrawdown: Math.min(0, Math.sin(i * 0.03) * 8 - 2),
      volatility: 15 + Math.sin(i * 0.02) * 3,
      returns: portfolioReturn * 100
    });
    
    previousPortfolioValue = portfolioValue;
    previousBenchmarkValue = benchmarkValue;
  }
  
  return data;
};

const mockBacktestData = generateMockBacktestData();

const mockAttribution: PerformanceAttribution[] = [
  {
    sector: "Technology",
    contribution: 2.15,
    weight: 65.2,
    return: 8.3,
    benchmark: 6.1,
    attribution: 1.43
  },
  {
    sector: "Healthcare",
    contribution: 0.42,
    weight: 12.5,
    return: 3.4,
    benchmark: 4.1,
    attribution: -0.09
  },
  {
    sector: "Financial",
    contribution: 0.31,
    weight: 8.7,
    return: 3.6,
    benchmark: 3.2,
    attribution: 0.03
  },
  {
    sector: "Consumer",
    contribution: 0.18,
    weight: 7.2,
    return: 2.5,
    benchmark: 2.8,
    attribution: -0.02
  },
  {
    sector: "Energy",
    contribution: 0.12,
    weight: 4.1,
    return: 2.9,
    benchmark: 1.8,
    attribution: 0.05
  },
  {
    sector: "Other",
    contribution: 0.07,
    weight: 2.3,
    return: 3.1,
    benchmark: 2.4,
    attribution: 0.02
  }
];

export function PortfolioBacktesting() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeTab, setActiveTab] = useState("results");
  const [settings, setSettings] = useState<BacktestSettings>({
    startDate: "2024-01-01",
    endDate: "2024-12-31",
    benchmark: "SPY",
    rebalanceFrequency: "monthly",
    initialValue: 100000
  });
  const [backtestData, setBacktestData] = useState(mockBacktestData);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadBacktestData = async () => {
      try {
        const res = await fetch('/data/backtest_timeseries.json');
        if (res.ok) {
          const data = await res.json();
          setBacktestData(data);
        }
      } catch (error) {
        console.warn('Failed to load backtest data, using fallback:', error);
      } finally {
        setLoading(false);
      }
    };
    loadBacktestData();
  }, []);

  const runBacktest = async () => {
    setIsRunning(true);
    setProgress(0);
    
    // Simulate backtest progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 100;
        }
        return prev + 8;
      });
    }, 200);
  };

  // Calculate key metrics from backtest data
  const finalPortfolioValue = mockBacktestData[mockBacktestData.length - 1]?.portfolioValue || 100000;
  const finalBenchmarkValue = mockBacktestData[mockBacktestData.length - 1]?.benchmarkValue || 100000;
  const totalReturn = ((finalPortfolioValue - settings.initialValue) / settings.initialValue) * 100;
  const benchmarkReturn = ((finalBenchmarkValue - settings.initialValue) / settings.initialValue) * 100;
  const avgSharpe = mockBacktestData.reduce((sum, d) => sum + d.sharpeRatio, 0) / mockBacktestData.length;
  const maxDrawdown = Math.min(...mockBacktestData.map(d => d.maxDrawdown));
  const avgVolatility = mockBacktestData.reduce((sum, d) => sum + d.volatility, 0) / mockBacktestData.length;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-6">
      {/* Backtest Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-600" />
            Backtest Configuration
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Configure historical analysis parameters
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="startDate">Start Date</Label>
              <Input
                id="startDate"
                type="date"
                value={settings.startDate}
                onChange={(e) => setSettings(prev => ({ ...prev, startDate: e.target.value }))}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="endDate">End Date</Label>
              <Input
                id="endDate"
                type="date"
                value={settings.endDate}
                onChange={(e) => setSettings(prev => ({ ...prev, endDate: e.target.value }))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="benchmark">Benchmark</Label>
              <Select value={settings.benchmark} onValueChange={(value) => setSettings(prev => ({ ...prev, benchmark: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SPY">S&P 500 (SPY)</SelectItem>
                  <SelectItem value="QQQ">NASDAQ 100 (QQQ)</SelectItem>
                  <SelectItem value="VTI">Total Market (VTI)</SelectItem>
                  <SelectItem value="IWM">Russell 2000 (IWM)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="rebalance">Rebalancing Frequency</Label>
              <Select value={settings.rebalanceFrequency} onValueChange={(value) => setSettings(prev => ({ ...prev, rebalanceFrequency: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="initialValue">Initial Value ($)</Label>
              <Input
                id="initialValue"
                type="number"
                value={settings.initialValue}
                onChange={(e) => setSettings(prev => ({ ...prev, initialValue: Number(e.target.value) }))}
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              onClick={runBacktest}
              disabled={isRunning}
              className="flex items-center gap-2"
            >
              {isRunning ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  Running Backtest...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4" />
                  Run Backtest
                </>
              )}
            </Button>

            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Results
            </Button>

            {isRunning && (
              <div className="flex items-center gap-2 flex-1">
                <Progress value={progress} className="flex-1" />
                <span className="text-sm text-muted-foreground">{progress}%</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="results" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Results
          </TabsTrigger>
          <TabsTrigger value="attribution" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Attribution
          </TabsTrigger>
          <TabsTrigger value="risk" className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Risk Analysis
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <Award className="w-4 h-4" />
            Metrics
          </TabsTrigger>
        </TabsList>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          {/* Performance Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Return</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">+{totalReturn.toFixed(2)}%</div>
                <p className="text-xs text-muted-foreground">
                  vs {settings.benchmark}: +{benchmarkReturn.toFixed(2)}%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
                <Award className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{avgSharpe.toFixed(2)}</div>
                <p className="text-xs text-muted-foreground">
                  Risk-adjusted return
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
                <TrendingDown className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">{maxDrawdown.toFixed(2)}%</div>
                <p className="text-xs text-muted-foreground">
                  Worst decline
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Volatility</CardTitle>
                <BarChart3 className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{avgVolatility.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  Annualized volatility
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Portfolio vs Benchmark Performance</CardTitle>
              <p className="text-sm text-muted-foreground">
                Cumulative returns over the backtest period
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={backtestData.slice(-60)}> {/* Show last 60 days */}
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${(value/1000).toFixed(0)}K`}
                  />
                  <RechartsTooltip
                    formatter={(value: any, name: any) => [
                      `$${value.toLocaleString()}`,
                      name === 'portfolioValue' ? 'Portfolio' : 'Benchmark'
                    ]}
                    labelFormatter={(value) => formatDate(value)}
                  />
                  <Line
                    type="monotone"
                    dataKey="portfolioValue"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name="Portfolio"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="benchmarkValue"
                    stroke="#6b7280"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="Benchmark"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Rolling Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Rolling Performance Metrics</CardTitle>
              <p className="text-sm text-muted-foreground">
                30-day rolling Sharpe ratio and alpha
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={mockBacktestData.slice(-60)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatDate} />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <RechartsTooltip />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="alpha"
                    fill="#10b981"
                    fillOpacity={0.3}
                    stroke="#10b981"
                    name="Alpha (%)"
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="sharpeRatio"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Sharpe Ratio"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Attribution Tab */}
        <TabsContent value="attribution" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5 text-green-600" />
                Performance Attribution Analysis
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Breakdown of returns by sector and security selection
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockAttribution.map((attr, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div>
                        <h4 className="font-semibold">{attr.sector}</h4>
                        <p className="text-sm text-muted-foreground">
                          Weight: {attr.weight.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-4 gap-6 text-right">
                      <div>
                        <Label className="text-xs text-muted-foreground">Return</Label>
                        <p className="font-semibold text-green-600">+{attr.return.toFixed(1)}%</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Benchmark</Label>
                        <p className="font-semibold">+{attr.benchmark.toFixed(1)}%</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Attribution</Label>
                        <p className={`font-semibold ${attr.attribution >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {attr.attribution >= 0 ? '+' : ''}{attr.attribution.toFixed(2)}%
                        </p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Contribution</Label>
                        <p className="font-semibold">{attr.contribution.toFixed(2)}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">Attribution Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <Label className="text-xs text-muted-foreground">Stock Selection</Label>
                    <p className="font-semibold text-green-600">+1.42%</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Sector Allocation</Label>
                    <p className="font-semibold text-red-600">-0.18%</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Total Alpha</Label>
                    <p className="font-semibold text-green-600">+1.24%</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Analysis Tab */}
        <TabsContent value="risk" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Historical Risk Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={mockBacktestData.slice(-90)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={formatDate} />
                  <YAxis />
                  <RechartsTooltip />
                  <Area
                    type="monotone"
                    dataKey="maxDrawdown"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.3}
                    name="Drawdown (%)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk-Adjusted Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Sharpe Ratio</span>
                  <span className="font-semibold">{avgSharpe.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Sortino Ratio</span>
                  <span className="font-semibold">1.85</span>
                </div>
                <div className="flex justify-between">
                  <span>Calmar Ratio</span>
                  <span className="font-semibold">0.93</span>
                </div>
                <div className="flex justify-between">
                  <span>Information Ratio</span>
                  <span className="font-semibold">0.67</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Beta</span>
                  <span className="font-semibold">0.95</span>
                </div>
                <div className="flex justify-between">
                  <span>Tracking Error</span>
                  <span className="font-semibold">4.2%</span>
                </div>
                <div className="flex justify-between">
                  <span>VaR (95%)</span>
                  <span className="font-semibold text-red-600">-2.1%</span>
                </div>
                <div className="flex justify-between">
                  <span>Expected Shortfall</span>
                  <span className="font-semibold text-red-600">-3.4%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}