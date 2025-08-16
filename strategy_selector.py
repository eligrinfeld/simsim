#!/usr/bin/env python3
"""
Strategy Selector: Comprehensive evaluation and selection of best performing strategies
Based on TradingView metrics and HRM backtesting report criteria.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json
import warnings
warnings.filterwarnings('ignore')

from strategy_backtester import (
    SuperTrendADXStrategy, DonchianTurtleStrategy, IchimokuCloudStrategy,
    TTMSqueezeStrategy, DMIADXCrossStrategy, KAMAStrategy, HMAStrategy,
    AVWAPStackStrategy, BillWilliamsAlligatorFractalsAOStrategy,
    KeltnerBollingerBandWalkStrategy, ChandeKrollStopStrategy,
    FractalBoSStrategy, ConnorsRSIStrategy, StrategyBacktester
)


@dataclass
class StrategyEvaluation:
    """Complete strategy evaluation with TradingView metrics."""
    strategy_name: str
    
    # Core Performance (from HRM report)
    total_return: float
    excess_return: float  # vs buy-and-hold
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    
    # TradingView Metrics
    net_profit: float
    profit_factor: float
    sortino_ratio: float
    average_trade: float
    expectancy: float
    buy_hold_return: float
    
    # Composite Score (0-100)
    performance_score: float
    
    # Strategy Classification
    strategy_type: str  # "Trend", "Momentum", "Mean Reversion", "Hybrid"
    confidence_level: str  # "High", "Medium", "Low"
    
    # Risk Assessment
    risk_level: str  # "Conservative", "Moderate", "Aggressive"
    recommended_allocation: float  # 0.0 to 1.0


class StrategySelector:
    """Evaluates all strategies and selects the best performer for each ticker."""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.strategies = self._initialize_strategies()
        
    def _initialize_strategies(self) -> List[Tuple]:
        """Initialize all 13 strategies with their classifications."""
        return [
            # Trend + Structure Systems
            (SuperTrendADXStrategy(10, 3.0, 25), "SuperTrend_ADX", "Trend", "High"),
            (DonchianTurtleStrategy(20, 10), "Donchian_Turtle", "Trend", "High"),
            (IchimokuCloudStrategy(), "Ichimoku_Cloud", "Trend", "Medium"),
            (AVWAPStackStrategy([], 2), "AVWAP_Stack", "Trend", "Medium"),
            (BillWilliamsAlligatorFractalsAOStrategy(13, 8, 5, 2, 5, 34), "BillWilliams_Alligator", "Trend", "Medium"),
            
            # Momentum/Volatility Hybrids
            (TTMSqueezeStrategy(20, 2.0, 1.5), "TTM_Squeeze", "Momentum", "High"),
            (KeltnerBollingerBandWalkStrategy(20, 2.0, 1.5), "Keltner_Bollinger", "Momentum", "Medium"),
            (ChandeKrollStopStrategy(10, 3.0), "Chande_Kroll", "Momentum", "Low"),
            
            # Regime & Confirmation
            (DMIADXCrossStrategy(25), "DMI_ADX_Cross", "Trend", "Medium"),
            
            # Structure & Microstructure
            (FractalBoSStrategy(2, 1.0), "Fractal_BoS", "Trend", "Low"),
            
            # Quant-leaning Extensions
            (KAMAStrategy(10, 2, 30), "KAMA", "Momentum", "High"),
            (HMAStrategy(55), "HMA", "Momentum", "High"),
            (ConnorsRSIStrategy(3, 2, 100), "Connors_RSI", "Mean Reversion", "Medium"),
        ]
    
    def calculate_performance_score(self, eval_result: StrategyEvaluation) -> float:
        """Calculate composite performance score based on HRM report criteria."""
        score = 0
        
        # Excess Return vs Buy-and-Hold (40% weight) - Most important per HRM report
        excess_score = min(max(eval_result.excess_return * 100, -50), 50) * 0.4
        score += excess_score
        
        # Win Rate (20% weight) - High importance per HRM report
        win_rate_score = eval_result.win_rate * 0.2
        score += win_rate_score
        
        # Sharpe Ratio (15% weight) - Risk-adjusted returns
        sharpe_score = min(max(eval_result.sharpe_ratio * 10, -15), 15)
        score += sharpe_score
        
        # Max Drawdown penalty (15% weight) - Risk management
        dd_penalty = -abs(eval_result.max_drawdown) * 0.15
        score += dd_penalty
        
        # Trade Frequency bonus (10% weight) - Lower frequency preferred per HRM report
        if eval_result.total_trades <= 20:
            freq_bonus = 10
        elif eval_result.total_trades <= 30:
            freq_bonus = 5
        else:
            freq_bonus = 0
        score += freq_bonus
        
        # Normalize to 0-100 scale
        return max(0, min(100, score + 50))
    
    def classify_risk_level(self, eval_result: StrategyEvaluation) -> str:
        """Classify strategy risk level based on drawdown and volatility."""
        if abs(eval_result.max_drawdown) <= 0.10:
            return "Conservative"
        elif abs(eval_result.max_drawdown) <= 0.20:
            return "Moderate"
        else:
            return "Aggressive"
    
    def calculate_recommended_allocation(self, eval_result: StrategyEvaluation) -> float:
        """Calculate recommended portfolio allocation based on performance and risk."""
        base_allocation = 0.2  # 20% base
        
        # Adjust based on excess return
        if eval_result.excess_return > 0.20:  # >20% excess return
            base_allocation += 0.3
        elif eval_result.excess_return > 0.10:  # >10% excess return
            base_allocation += 0.2
        elif eval_result.excess_return > 0:  # Positive excess return
            base_allocation += 0.1
        
        # Adjust based on risk
        if eval_result.risk_level == "Conservative":
            base_allocation += 0.1
        elif eval_result.risk_level == "Aggressive":
            base_allocation -= 0.1
        
        # Adjust based on win rate
        if eval_result.win_rate > 0.70:
            base_allocation += 0.1
        elif eval_result.win_rate < 0.50:
            base_allocation -= 0.1
        
        return max(0.05, min(1.0, base_allocation))

    def evaluate_strategy_for_ticker(self, ticker: str, strategy_info: Tuple,
                                   start_date: str = "2021-01-01",
                                   end_date: str = "2024-01-01") -> StrategyEvaluation:
        """Evaluate a single strategy for a specific ticker."""
        strategy, name, strategy_type, confidence = strategy_info

        try:
            # Get data and backtest
            backtester = StrategyBacktester(ticker, start_date, end_date, self.initial_capital)
            result = backtester.backtest_strategy(strategy, transaction_cost=0.001)

            # Calculate TradingView metrics
            net_profit = result.total_return * self.initial_capital
            profit_factor = 2.0 if result.win_rate > 0.6 else 1.5 if result.win_rate > 0.5 else 1.0
            sortino_ratio = result.sharpe_ratio * 1.2  # Estimate
            average_trade = net_profit / max(result.total_trades, 1)
            expectancy = average_trade

            # Create evaluation
            eval_result = StrategyEvaluation(
                strategy_name=name,
                total_return=result.total_return,
                excess_return=result.excess_return,
                win_rate=result.win_rate,
                total_trades=result.total_trades,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                net_profit=net_profit,
                profit_factor=profit_factor,
                sortino_ratio=sortino_ratio,
                average_trade=average_trade,
                expectancy=expectancy,
                buy_hold_return=result.buy_hold_return,
                performance_score=0,  # Will be calculated
                strategy_type=strategy_type,
                confidence_level=confidence,
                risk_level="",  # Will be calculated
                recommended_allocation=0  # Will be calculated
            )

            # Calculate derived metrics
            eval_result.performance_score = self.calculate_performance_score(eval_result)
            eval_result.risk_level = self.classify_risk_level(eval_result)
            eval_result.recommended_allocation = self.calculate_recommended_allocation(eval_result)

            return eval_result

        except Exception as e:
            print(f"❌ Error evaluating {name} for {ticker}: {e}")
            # Return default evaluation
            return StrategyEvaluation(
                strategy_name=name, total_return=0, excess_return=0, win_rate=0,
                total_trades=0, max_drawdown=0, sharpe_ratio=0, net_profit=0,
                profit_factor=1, sortino_ratio=0, average_trade=0, expectancy=0,
                buy_hold_return=0, performance_score=0, strategy_type=strategy_type,
                confidence_level="Low", risk_level="Conservative", recommended_allocation=0.05
            )

    def select_best_strategy_for_ticker(self, ticker: str,
                                      start_date: str = "2021-01-01",
                                      end_date: str = "2024-01-01") -> StrategyEvaluation:
        """Evaluate all strategies and select the best performer for a ticker."""
        print(f"\n🔍 Evaluating all strategies for {ticker}...")

        evaluations = []
        for strategy_info in self.strategies:
            eval_result = self.evaluate_strategy_for_ticker(ticker, strategy_info, start_date, end_date)
            evaluations.append(eval_result)

            # Print immediate results
            status = "✅ BEATS B&H" if eval_result.excess_return > 0 else "❌ UNDERPERFORMS"
            print(f"{status} {eval_result.strategy_name}: {eval_result.total_return:+.1%} "
                  f"(+{eval_result.excess_return:+.1%} vs B&H), Score: {eval_result.performance_score:.1f}")

        # Sort by performance score (highest first)
        evaluations.sort(key=lambda x: x.performance_score, reverse=True)

        best_strategy = evaluations[0]
        print(f"\n🏆 BEST STRATEGY for {ticker}: {best_strategy.strategy_name}")
        print(f"   📊 Performance Score: {best_strategy.performance_score:.1f}/100")
        print(f"   💰 Total Return: {best_strategy.total_return:+.1%}")
        print(f"   🎯 Excess Return: {best_strategy.excess_return:+.1%}")
        print(f"   🏅 Win Rate: {best_strategy.win_rate:.1%}")
        print(f"   📉 Max Drawdown: {best_strategy.max_drawdown:.1%}")
        print(f"   ⚡ Sharpe Ratio: {best_strategy.sharpe_ratio:.2f}")
        print(f"   🎲 Recommended Allocation: {best_strategy.recommended_allocation:.1%}")

        return best_strategy

    def generate_strategy_recommendations(self, tickers: List[str]) -> Dict[str, StrategyEvaluation]:
        """Generate strategy recommendations for multiple tickers."""
        recommendations = {}

        for ticker in tickers:
            try:
                best_strategy = self.select_best_strategy_for_ticker(ticker)
                recommendations[ticker] = best_strategy
            except Exception as e:
                print(f"❌ Error processing {ticker}: {e}")

        return recommendations

    def export_to_dashboard_format(self, recommendations: Dict[str, StrategyEvaluation],
                                 output_file: str = "strategy_recommendations.json"):
        """Export recommendations in format suitable for dashboard."""
        dashboard_data = {}

        for ticker, strategy in recommendations.items():
            dashboard_data[ticker] = {
                "strategy": strategy.strategy_name,
                "strategy_type": strategy.strategy_type,
                "confidence": strategy.confidence_level,
                "performance_score": strategy.performance_score,
                "total_return": strategy.total_return,
                "excess_return": strategy.excess_return,
                "win_rate": strategy.win_rate,
                "max_drawdown": strategy.max_drawdown,
                "sharpe_ratio": strategy.sharpe_ratio,
                "risk_level": strategy.risk_level,
                "recommended_allocation": strategy.recommended_allocation,
                "total_trades": strategy.total_trades
            }

        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        print(f"📁 Strategy recommendations exported to {output_file}")
        return dashboard_data


def main():
    """Main execution function."""
    # Initialize selector
    selector = StrategySelector(initial_capital=10000)

    # Test tickers (from your universe)
    tickers = ["NVDA", "AAPL", "MSFT", "META", "TSLA"]

    print("🚀 Starting comprehensive strategy evaluation...")
    print("=" * 80)

    # Generate recommendations
    recommendations = selector.generate_strategy_recommendations(tickers)

    # Export for dashboard
    dashboard_data = selector.export_to_dashboard_format(recommendations)

    # Summary report
    print("\n" + "=" * 80)
    print("📊 STRATEGY SELECTION SUMMARY")
    print("=" * 80)

    for ticker, strategy in recommendations.items():
        print(f"\n{ticker}: {strategy.strategy_name} ({strategy.strategy_type})")
        print(f"  Score: {strategy.performance_score:.1f}/100 | "
              f"Return: {strategy.total_return:+.1%} | "
              f"Excess: {strategy.excess_return:+.1%}")

    return recommendations


if __name__ == "__main__":
    main()
