import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Slider } from "./ui/slider";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  Area,
  AreaChart,
  BarChart,
  Bar
} from "recharts";
import { 
  PlayCircle, 
  PauseCircle, 
  RotateCcw, 
  TrendingDown,
  AlertTriangle,
  Activity,
  Target,
  Zap
} from "lucide-react";
import { Progress } from "./ui/progress";

interface SimulationResult {
  scenario: string;
  probability: number;
  portfolioValue: number;
  maxDrawdown: number;
  volatility: number;
  varAtRisk: number;
  timeToRecovery: number;
}

interface PathResult {
  day: number;
  portfolioValue: number;
  percentile5: number;
  percentile95: number;
  median: number;
}

const scenarios = [
  { name: "Bull Market", probability: 35, expectedReturn: 15.2, volatility: 18.5 },
  { name: "Normal Market", probability: 45, expectedReturn: 8.7, volatility: 12.3 },
  { name: "Bear Market", probability: 15, expectedReturn: -8.2, volatility: 25.1 },
  { name: "Market Crash", probability: 5, expectedReturn: -25.4, volatility: 35.8 }
];

export function MonteCarloSimulation() {
  const [isRunning, setIsRunning] = useState(false);
  const [simulations, setSimulations] = useState(1000);
  const [timeHorizon, setTimeHorizon] = useState([252]); // 1 year in trading days
  const [confidence, setConfidence] = useState([95]);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<SimulationResult[]>([]);
  const [pathData, setPathData] = useState<PathResult[]>([]);
  const [activeScenario, setActiveScenario] = useState("stress-test");

  // Mock simulation results
  const mockResults: SimulationResult[] = [
    {
      scenario: "Bull Market (35%)",
      probability: 35,
      portfolioValue: 127500,
      maxDrawdown: -8.2,
      volatility: 18.5,
      varAtRisk: 3.2,
      timeToRecovery: 45
    },
    {
      scenario: "Normal Market (45%)",
      probability: 45,
      portfolioValue: 108700,
      maxDrawdown: -12.1,
      volatility: 12.3,
      varAtRisk: 4.1,
      timeToRecovery: 67
    },
    {
      scenario: "Bear Market (15%)",
      probability: 15,
      portfolioValue: 91800,
      maxDrawdown: -18.5,
      volatility: 25.1,
      varAtRisk: 8.7,
      timeToRecovery: 156
    },
    {
      scenario: "Market Crash (5%)",
      probability: 5,
      portfolioValue: 74600,
      maxDrawdown: -35.2,
      volatility: 35.8,
      varAtRisk: 15.2,
      timeToRecovery: 389
    }
  ];

  // Generate mock path data
  const generatePathData = () => {
    const data: PathResult[] = [];
    const startValue = 100000;
    let currentValue = startValue;
    
    for (let day = 0; day <= timeHorizon[0]; day++) {
      const dailyReturn = (Math.random() - 0.5) * 0.04; // Random daily return
      currentValue *= (1 + dailyReturn);
      
      data.push({
        day,
        portfolioValue: currentValue,
        percentile5: currentValue * 0.75, // Mock confidence intervals
        percentile95: currentValue * 1.35,
        median: currentValue * 1.05
      });
    }
    return data;
  };

  const runSimulation = async () => {
    setIsRunning(true);
    setProgress(0);
    
    // Simulate progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          setResults(mockResults);
          setPathData(generatePathData());
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const resetSimulation = () => {
    setProgress(0);
    setResults([]);
    setPathData([]);
    setIsRunning(false);
  };

  const getScenarioColor = (scenario: string) => {
    if (scenario.includes("Bull")) return "text-green-600";
    if (scenario.includes("Bear") || scenario.includes("Crash")) return "text-red-600";
    return "text-blue-600";
  };

  const getRiskLevel = (var95: number) => {
    if (var95 < 5) return { level: "Low", color: "text-green-600" };
    if (var95 < 10) return { level: "Medium", color: "text-yellow-600" };
    return { level: "High", color: "text-red-600" };
  };

  return (
    <div className="space-y-6">
      {/* Simulation Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" />
            Monte Carlo Simulation Controls
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Run stress tests and scenario analysis on your portfolio
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <Label>Number of Simulations: {simulations.toLocaleString()}</Label>
              <Slider
                value={[simulations]}
                onValueChange={(value) => setSimulations(value[0])}
                max={10000}
                min={100}
                step={100}
                className="w-full"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Time Horizon: {Math.round(timeHorizon[0] / 252 * 12)} months</Label>
              <Slider
                value={timeHorizon}
                onValueChange={setTimeHorizon}
                max={1260} // 5 years
                min={21} // 1 month
                step={21}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label>Confidence Level: {confidence[0]}%</Label>
              <Slider
                value={confidence}
                onValueChange={setConfidence}
                max={99}
                min={90}
                step={1}
                className="w-full"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              onClick={runSimulation}
              disabled={isRunning}
              className="flex items-center gap-2"
            >
              {isRunning ? (
                <>
                  <PauseCircle className="w-4 h-4" />
                  Running...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4" />
                  Run Simulation
                </>
              )}
            </Button>
            
            <Button
              variant="outline"
              onClick={resetSimulation}
              disabled={isRunning}
              className="flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
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

      {results.length > 0 && (
        <>
          {/* Scenario Results */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-600" />
                Scenario Analysis Results
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Portfolio performance under different market conditions
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {results.map((result, index) => {
                  const riskLevel = getRiskLevel(result.varAtRisk);
                  return (
                    <div key={index} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className={`font-semibold ${getScenarioColor(result.scenario)}`}>
                          {result.scenario}
                        </h4>
                        <Badge className={riskLevel.color}>
                          {riskLevel.level} Risk
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <Label className="text-xs text-muted-foreground">Final Value</Label>
                          <p className="font-semibold">${result.portfolioValue.toLocaleString()}</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Max Drawdown</Label>
                          <p className="font-semibold text-red-600">{result.maxDrawdown}%</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">Volatility</Label>
                          <p className="font-semibold">{result.volatility}%</p>
                        </div>
                        <div>
                          <Label className="text-xs text-muted-foreground">VaR (95%)</Label>
                          <p className="font-semibold">{result.varAtRisk}%</p>
                        </div>
                      </div>
                      
                      <div className="pt-2 border-t">
                        <Label className="text-xs text-muted-foreground">Recovery Time</Label>
                        <p className="text-sm font-semibold">{result.timeToRecovery} days</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Portfolio Path Visualization */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                Portfolio Value Projections
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Simulated portfolio paths with confidence intervals
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={pathData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="day" 
                    tickFormatter={(value) => `${Math.round(value/21)}M`}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${(value/1000).toFixed(0)}K`}
                  />
                  <RechartsTooltip
                    formatter={(value: any, name: any) => [
                      `$${value.toLocaleString()}`,
                      name === 'portfolioValue' ? 'Expected Value' :
                      name === 'percentile5' ? '5th Percentile' :
                      name === 'percentile95' ? '95th Percentile' : 'Median'
                    ]}
                    labelFormatter={(value) => `Day ${value}`}
                  />
                  <Area
                    dataKey="percentile95"
                    stackId="1"
                    stroke="#82ca9d"
                    fill="#82ca9d"
                    fillOpacity={0.1}
                  />
                  <Area
                    dataKey="percentile5"
                    stackId="1"
                    stroke="#82ca9d"
                    fill="#ffffff"
                    fillOpacity={1}
                  />
                  <Line
                    type="monotone"
                    dataKey="median"
                    stroke="#8884d8"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="portfolioValue"
                    stroke="#ff7300"
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Stress Test Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                Stress Test Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
                  <TrendingDown className="w-8 h-8 text-red-600 mx-auto mb-2" />
                  <p className="text-lg font-semibold text-red-600">-35.2%</p>
                  <p className="text-sm text-muted-foreground">Worst-Case Scenario</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    5% probability of occurrence
                  </p>
                </div>
                
                <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <AlertTriangle className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                  <p className="text-lg font-semibold text-yellow-600">389 days</p>
                  <p className="text-sm text-muted-foreground">Max Recovery Time</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Time to break even
                  </p>
                </div>
                
                <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <Target className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <p className="text-lg font-semibold text-blue-600">$108.7K</p>
                  <p className="text-sm text-muted-foreground">Expected Value</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Most likely outcome
                  </p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-semibold mb-2">Key Insights</h4>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• 80% probability of positive returns over the next 12 months</li>
                  <li>• Portfolio shows resilience in normal and bull market scenarios</li>
                  <li>• Consider adding defensive positions to reduce crash scenario impact</li>
                  <li>• Current diversification provides moderate protection during downturns</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}