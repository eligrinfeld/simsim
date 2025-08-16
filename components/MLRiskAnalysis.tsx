import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
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
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from "recharts";
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Activity,
  Zap,
  Target,
  Eye,
  BarChart3,
  Lightbulb,
  Shield,
  Cpu
} from "lucide-react";

interface MarketRegime {
  regime: "Bull Market" | "Bear Market" | "Sideways" | "High Volatility";
  probability: number;
  confidence: number;
  duration: number;
  characteristics: string[];
  riskLevel: "Low" | "Medium" | "High";
}

interface RiskPrediction {
  ticker: string;
  currentRisk: number;
  predictedRisk: number;
  volatilityForecast: number;
  correlation: number;
  beta: number;
  momentum: number;
  sentiment: number;
  technicalScore: number;
}

interface MLModel {
  name: string;
  type: "Classification" | "Regression" | "Time Series";
  accuracy: number;
  lastTrained: Date;
  features: string[];
  status: "Active" | "Training" | "Offline";
}

const mockRegimes: MarketRegime[] = [
  {
    regime: "Bull Market",
    probability: 45,
    confidence: 78,
    duration: 127,
    characteristics: ["Rising prices", "Low volatility", "High volume"],
    riskLevel: "Low"
  },
  {
    regime: "Sideways",
    probability: 35,
    confidence: 82,
    duration: 89,
    characteristics: ["Range-bound", "Medium volatility", "Mixed signals"],
    riskLevel: "Medium"
  },
  {
    regime: "High Volatility",
    probability: 15,
    confidence: 65,
    duration: 34,
    characteristics: ["High volatility", "Uncertain direction", "News-driven"],
    riskLevel: "High"
  },
  {
    regime: "Bear Market",
    probability: 5,
    confidence: 71,
    duration: 21,
    characteristics: ["Declining prices", "High volatility", "Risk-off"],
    riskLevel: "High"
  }
];

const mockPredictions: RiskPrediction[] = [
  {
    ticker: "AAPL",
    currentRisk: 2.1,
    predictedRisk: 2.8,
    volatilityForecast: 24.5,
    correlation: 0.67,
    beta: 1.15,
    momentum: 0.23,
    sentiment: 0.71,
    technicalScore: 0.84
  },
  {
    ticker: "MSFT",
    currentRisk: 1.8,
    predictedRisk: 2.2,
    volatilityForecast: 22.1,
    correlation: 0.72,
    beta: 0.98,
    momentum: 0.31,
    sentiment: 0.68,
    technicalScore: 0.79
  },
  {
    ticker: "GOOGL",
    currentRisk: 2.5,
    predictedRisk: 3.1,
    volatilityForecast: 28.2,
    correlation: 0.59,
    beta: 1.23,
    momentum: 0.18,
    sentiment: 0.62,
    technicalScore: 0.72
  },
  {
    ticker: "TSLA",
    currentRisk: 4.2,
    predictedRisk: 5.1,
    volatilityForecast: 45.8,
    correlation: 0.41,
    beta: 1.67,
    momentum: 0.45,
    sentiment: 0.55,
    technicalScore: 0.68
  }
];

const mockModels: MLModel[] = [
  {
    name: "Market Regime Classifier",
    type: "Classification",
    accuracy: 78.4,
    lastTrained: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    features: ["VIX", "SPY momentum", "Sector rotation", "Volume patterns"],
    status: "Active"
  },
  {
    name: "Volatility Forecaster",
    type: "Time Series",
    accuracy: 82.1,
    lastTrained: new Date(Date.now() - 1000 * 60 * 60 * 6), // 6 hours ago
    features: ["Historical volatility", "Options flow", "Economic indicators"],
    status: "Active"
  },
  {
    name: "Risk Predictor",
    type: "Regression",
    accuracy: 75.8,
    lastTrained: new Date(Date.now() - 1000 * 60 * 60 * 1), // 1 hour ago
    features: ["Price momentum", "Volume", "Correlation", "Beta"],
    status: "Training"
  },
  {
    name: "Sentiment Analyzer",
    type: "Classification",
    accuracy: 71.2,
    lastTrained: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 hours ago
    features: ["News sentiment", "Social media", "Options positioning"],
    status: "Active"
  }
];

export function MLRiskAnalysis() {
  const [activeTab, setActiveTab] = useState("regimes");
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null);

  // Generate time series data for regime prediction
  const regimeTimeData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    bullProb: Math.max(0, Math.sin(i * 0.2) * 30 + 45 + Math.random() * 10),
    bearProb: Math.max(0, Math.cos(i * 0.3) * 15 + 10 + Math.random() * 5),
    sidewaysProb: Math.max(0, 35 + Math.sin(i * 0.15) * 15 + Math.random() * 8),
    volatilityProb: Math.max(0, Math.random() * 25)
  }));

  // Correlation matrix data
  const correlationData = [
    { asset: "AAPL", AAPL: 1.0, MSFT: 0.67, GOOGL: 0.52, TSLA: 0.31 },
    { asset: "MSFT", AAPL: 0.67, MSFT: 1.0, GOOGL: 0.72, TSLA: 0.28 },
    { asset: "GOOGL", AAPL: 0.52, MSFT: 0.72, GOOGL: 1.0, TSLA: 0.33 },
    { asset: "TSLA", AAPL: 0.31, MSFT: 0.28, GOOGL: 0.33, TSLA: 1.0 }
  ];

  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case "Bull Market": return "text-green-600 bg-green-100";
      case "Bear Market": return "text-red-600 bg-red-100";
      case "Sideways": return "text-blue-600 bg-blue-100";
      case "High Volatility": return "text-yellow-600 bg-yellow-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case "Low": return "text-green-600";
      case "Medium": return "text-yellow-600";
      case "High": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  const getModelStatusColor = (status: string) => {
    switch (status) {
      case "Active": return "text-green-600 bg-green-100";
      case "Training": return "text-yellow-600 bg-yellow-100";
      case "Offline": return "text-red-600 bg-red-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  const formatTimeAgo = (date: Date) => {
    const hours = Math.floor((Date.now() - date.getTime()) / (1000 * 60 * 60));
    return `${hours}h ago`;
  };

  const retrainModel = (modelName: string) => {
    setIsTraining(true);
    setTrainingProgress(0);
    
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsTraining(false);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            Machine Learning Risk Analysis
          </h3>
          <p className="text-sm text-muted-foreground">
            AI-powered market regime detection and predictive risk modeling
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-sm">
            <Cpu className="w-3 h-3 mr-1" />
            4 Models Active
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="regimes" className="flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Market Regimes
          </TabsTrigger>
          <TabsTrigger value="predictions" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Risk Predictions
          </TabsTrigger>
          <TabsTrigger value="models" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            ML Models
          </TabsTrigger>
          <TabsTrigger value="correlations" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Correlations
          </TabsTrigger>
        </TabsList>

        {/* Market Regimes Tab */}
        <TabsContent value="regimes" className="space-y-6">
          {/* Current Regime */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                Current Market Regime Analysis
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                AI-powered classification of current market conditions
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  {mockRegimes.map((regime, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRegimeColor(regime.regime)}`}>
                          {regime.regime}
                        </div>
                        <Badge className={getRiskLevelColor(regime.riskLevel)}>
                          {regime.riskLevel} Risk
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold">{regime.probability}%</p>
                        <p className="text-xs text-muted-foreground">
                          {regime.confidence}% confidence
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div>
                  <h4 className="font-semibold mb-3">Regime Characteristics</h4>
                  <div className="space-y-2">
                    {mockRegimes[0].characteristics.map((char, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        {char}
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-3 bg-muted rounded-lg">
                    <p className="text-sm">
                      <strong>Expected Duration:</strong> {mockRegimes[0].duration} days
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Based on historical regime analysis
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Regime Probability Over Time */}
          <Card>
            <CardHeader>
              <CardTitle>Regime Probability Trends</CardTitle>
              <p className="text-sm text-muted-foreground">
                30-day rolling probability predictions for different market regimes
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={regimeTimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <RechartsTooltip />
                  <Area
                    type="monotone"
                    dataKey="bullProb"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                    name="Bull Market"
                  />
                  <Area
                    type="monotone"
                    dataKey="sidewaysProb"
                    stackId="1"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.6}
                    name="Sideways"
                  />
                  <Area
                    type="monotone"
                    dataKey="volatilityProb"
                    stackId="1"
                    stroke="#f59e0b"
                    fill="#f59e0b"
                    fillOpacity={0.6}
                    name="High Volatility"
                  />
                  <Area
                    type="monotone"
                    dataKey="bearProb"
                    stackId="1"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.6}
                    name="Bear Market"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Predictions Tab */}
        <TabsContent value="predictions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                AI Risk Predictions
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Machine learning forecasts for individual position risks
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockPredictions.map((pred, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold">{pred.ticker}</h4>
                        {pred.predictedRisk > pred.currentRisk ? (
                          <Badge variant="destructive" className="flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" />
                            Risk Rising
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <TrendingDown className="w-3 h-3" />
                            Risk Stable
                          </Badge>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Predicted Risk</p>
                        <p className="text-lg font-semibold">{pred.predictedRisk.toFixed(1)}%</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <Label className="text-xs text-muted-foreground">Current Risk</Label>
                        <p className="font-semibold">{pred.currentRisk.toFixed(1)}%</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Vol Forecast</Label>
                        <p className="font-semibold">{pred.volatilityForecast.toFixed(1)}%</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Correlation</Label>
                        <p className="font-semibold">{pred.correlation.toFixed(2)}</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Beta</Label>
                        <p className="font-semibold">{pred.beta.toFixed(2)}</p>
                      </div>
                    </div>

                    <div className="mt-4">
                      <ResponsiveContainer width="100%" height={100}>
                        <BarChart data={[{
                          momentum: pred.momentum * 100,
                          sentiment: pred.sentiment * 100,
                          technical: pred.technicalScore * 100
                        }]}>
                          <XAxis hide />
                          <YAxis hide />
                          <Bar dataKey="momentum" fill="#3b82f6" name="Momentum" />
                          <Bar dataKey="sentiment" fill="#10b981" name="Sentiment" />
                          <Bar dataKey="technical" fill="#f59e0b" name="Technical" />
                          <RechartsTooltip 
                            formatter={(value: any, name: any) => [`${value.toFixed(1)}%`, name]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ML Models Tab */}
        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" />
                Active ML Models
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Monitor and manage machine learning model performance
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockModels.map((model, index) => (
                  <div key={index} className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold">{model.name}</h4>
                      <Badge className={getModelStatusColor(model.status)}>
                        {model.status}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <Label className="text-xs text-muted-foreground">Type</Label>
                        <p className="font-medium">{model.type}</p>
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground">Accuracy</Label>
                        <p className="font-medium">{model.accuracy}%</p>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs text-muted-foreground">Features</Label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {model.features.map((feature, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t">
                      <span className="text-xs text-muted-foreground">
                        Last trained: {formatTimeAgo(model.lastTrained)}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => retrainModel(model.name)}
                        disabled={isTraining}
                      >
                        Retrain
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {isTraining && (
                <div className="mt-6 p-4 bg-muted rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Model Training in Progress</span>
                    <span className="text-sm text-muted-foreground">{trainingProgress}%</span>
                  </div>
                  <Progress value={trainingProgress} className="w-full" />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Correlations Tab */}
        <TabsContent value="correlations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                Dynamic Correlation Analysis
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Real-time correlation matrix and diversification insights
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3">Correlation Matrix</h4>
                  <div className="grid grid-cols-5 gap-1 text-xs">
                    <div></div>
                    <div className="text-center font-medium">AAPL</div>
                    <div className="text-center font-medium">MSFT</div>
                    <div className="text-center font-medium">GOOGL</div>
                    <div className="text-center font-medium">TSLA</div>
                    
                    {correlationData.map((row) => (
                      <div key={row.asset} className="contents">
                        <div className="font-medium">{row.asset}</div>
                        <div className={`text-center p-2 rounded ${row.AAPL === 1.0 ? 'bg-blue-500 text-white' : 
                          row.AAPL > 0.5 ? 'bg-blue-200' : 'bg-blue-100'}`}>
                          {row.AAPL.toFixed(2)}
                        </div>
                        <div className={`text-center p-2 rounded ${row.MSFT === 1.0 ? 'bg-blue-500 text-white' : 
                          row.MSFT > 0.5 ? 'bg-blue-200' : 'bg-blue-100'}`}>
                          {row.MSFT.toFixed(2)}
                        </div>
                        <div className={`text-center p-2 rounded ${row.GOOGL === 1.0 ? 'bg-blue-500 text-white' : 
                          row.GOOGL > 0.5 ? 'bg-blue-200' : 'bg-blue-100'}`}>
                          {row.GOOGL.toFixed(2)}
                        </div>
                        <div className={`text-center p-2 rounded ${row.TSLA === 1.0 ? 'bg-blue-500 text-white' : 
                          row.TSLA > 0.5 ? 'bg-blue-200' : 'bg-blue-100'}`}>
                          {row.TSLA.toFixed(2)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-3">Diversification Insights</h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-4 h-4 text-yellow-600" />
                        <p className="font-medium text-yellow-800">High Correlation Warning</p>
                      </div>
                      <p className="text-sm text-yellow-700">
                        MSFT and GOOGL show 72% correlation, reducing diversification benefits.
                      </p>
                    </div>

                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <Shield className="w-4 h-4 text-green-600" />
                        <p className="font-medium text-green-800">Good Diversifier</p>
                      </div>
                      <p className="text-sm text-green-700">
                        TSLA shows low correlation (31-33%) with other positions.
                      </p>
                    </div>

                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <Lightbulb className="w-4 h-4 text-blue-600" />
                        <p className="font-medium text-blue-800">Optimization Suggestion</p>
                      </div>
                      <p className="text-sm text-blue-700">
                        Consider adding bonds or commodities to reduce overall portfolio correlation.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}