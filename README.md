# 🚀 AI-Powered Trading Dashboard

A professional-grade trading dashboard with **live market data**, **AI-powered sentiment analysis**, and **institutional-quality insights**.

## ✨ Features

### 🤖 **AI-Powered Analysis**
- **Grok AI sentiment analysis** with financial NLP
- **Real news sentiment** from 20+ articles per stock
- **Social media sentiment** tracking
- **Professional reasoning** for every recommendation
- **70-75% confidence** scoring with AI assessment

### 📊 **Live Market Data**
- **Real-time prices** from Finnhub, Alpha Vantage, Yahoo Finance
- **Professional technical indicators** (RSI, MACD, ADX, Bollinger Bands)
- **Live volatility calculations** from actual price history
- **Smart caching** with 5-minute refresh cycles

### 🎯 **Trading Intelligence**
- **13 HRM trading strategies** with real backtesting
- **Long/Short positioning** based on market conditions
- **Risk-adjusted recommendations** with confidence scoring
- **Portfolio management** with add/remove functionality

### 💎 **Professional Features**
- **Bloomberg Terminal quality** data and analysis
- **Hedge fund grade** multi-source intelligence
- **Institutional data integration** (Berkshire holdings, insider trading)
- **Real-time processing** with professional error handling

## 🚀 Quick Start

### 1. **Clone Repository**
```bash
git clone https://github.com/eligrinfeld/simsim.git
cd simsim
git checkout Dashboard
```

### 2. **Install Dependencies**
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install yfinance pandas numpy requests python-dotenv TA-Lib
```

### 3. **Setup API Keys**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 4. **Required API Keys**
- **Grok API**: Get from [x.ai](https://x.ai) for AI sentiment analysis
- **News API**: Get from [newsapi.org](https://newsapi.org) for news sentiment
- **Finnhub**: Get from [finnhub.io](https://finnhub.io) for real-time prices
- **Alpha Vantage**: Get from [alphavantage.co](https://alphavantage.co) for backup data

### 5. **Start Dashboard**
```bash
# Start Next.js frontend
npm run dev

# In another terminal, test Python backend
python3 test_live_data.py
```

### 6. **Access Dashboard**
Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📊 **Dashboard Sections**

### **Portfolio Management**
- Add/remove stocks and crypto
- Real-time portfolio tracking
- AI-driven position recommendations

### **Long Strategy Positions**
- View AI-selected long positions
- Real technical analysis and forecasts
- Professional strategy explanations

### **Short Strategy Positions**
- View AI-selected short positions
- Market condition-based recommendations
- Risk-adjusted position sizing

## 🤖 **AI Sentiment Examples**

### **AAPL Analysis:**
```
🤖 Sentiment: Neutral (+0.05)
🎯 Confidence: 75%
🧠 Reasoning: "Berkshire Hathaway reduced stake by 6.7% (bearish) 
              vs Apple Watch feature improvements (bullish)"
📰 News: 20 articles analyzed
📱 Social: Stable sentiment trend
```

### **CRM Analysis:**
```
🤖 Sentiment: Neutral (+0.10)
🎯 Confidence: 70%
🧠 Reasoning: "Analyst 'Moderate Buy' consensus (bullish)
              vs Representative share sales (bearish)"
📰 News: Bullish analyst coverage
📱 Social: Falling retail sentiment
```

## 📈 **Live Data Sources**

- **Finnhub**: Real-time stock prices and company news
- **News API**: 20+ articles per sentiment analysis
- **Alpha Vantage**: Backup financial data and indicators
- **Yahoo Finance**: Crypto prices and historical data
- **Grok AI**: Professional sentiment analysis with financial NLP

## 🎯 **Technical Architecture**

### **Frontend**
- **Next.js** with TypeScript
- **React** components with Tailwind CSS
- **Real-time data** updates with caching
- **Professional UI** with shadcn/ui components

### **Backend**
- **Python** services for data processing
- **Live API integrations** with error handling
- **TA-Lib** for technical indicators
- **Smart caching** for performance optimization

### **AI Integration**
- **Grok-2-1212** model for sentiment analysis
- **Financial NLP** for market language understanding
- **Multi-source analysis** (news + social + institutional)
- **Confidence scoring** with detailed reasoning

## 🔧 **Configuration**

### **API Rate Limits**
- **Grok AI**: 1000 requests/day (sufficient for trading)
- **News API**: 1000 requests/day (cached for 5 minutes)
- **Finnhub**: 60 calls/minute (real-time prices)
- **Alpha Vantage**: 5 calls/minute (backup data)

### **Caching Strategy**
- **Price data**: 5-minute cache
- **Sentiment analysis**: 5-minute cache
- **Technical indicators**: 5-minute cache
- **News articles**: 1-hour cache

## 🎯 **Professional Use Cases**

### **Day Trading**
- Real-time sentiment shifts
- Technical indicator alerts
- AI-powered entry/exit signals

### **Swing Trading**
- Multi-day sentiment trends
- Strategy-based position selection
- Risk-adjusted portfolio management

### **Investment Research**
- Comprehensive market analysis
- AI-powered due diligence
- Professional-grade data quality

## 🚀 **Next Steps**

### **Enhanced Features Available**
- **Real-time alerts** on sentiment changes
- **Social media integration** (Twitter, Reddit)
- **Options flow analysis** for institutional activity
- **Economic data integration** (FRED API)

### **Scaling Options**
- **Database integration** with Supabase
- **Multi-user support** with authentication
- **API rate limit optimization**
- **Professional deployment** on cloud platforms

## 📞 **Support**

For questions or issues:
1. Check the **AI_SENTIMENT_SUMMARY.md** for detailed AI features
2. Review **PREMIUM_DATA_SUMMARY.md** for data source information
3. Test APIs with provided Python scripts
4. Ensure all API keys are properly configured

---

**Built with ❤️ for professional traders and investors**

*This dashboard provides institutional-grade trading intelligence comparable to Bloomberg Terminal and professional trading platforms.*
