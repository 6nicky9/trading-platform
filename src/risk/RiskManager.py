"""
RiskManager.py - Advanced risk management system
Implements portfolio risk calculation, position sizing, and risk controls
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
import json


class RiskLevel(Enum):
    """Risk level classification"""
    CONSERVATIVE = 1
    MODERATE = 2
    AGGRESSIVE = 3


class RiskMetric(Enum):
    """Risk metrics enumeration"""
    VAR = "value_at_risk"
    CVAR = "conditional_var"
    SHARPE = "sharpe_ratio"
    SORTINO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    BETA = "beta"


@dataclass
class PositionRisk:
    """Individual position risk metrics"""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    volatility: float = 0.0
    value_at_risk: float = 0.0
    expected_loss: float = 0.0
    risk_reward_ratio: float = 0.0
    margin_requirement: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics"""
    total_value: float
    total_risk: float
    value_at_risk_95: float
    conditional_var_95: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    correlation_matrix: Optional[pd.DataFrame] = None
    beta_coefficients: Optional[Dict[str, float]] = None
    calculated_at: datetime = field(default_factory=datetime.now)


class RiskManager:
    """Advanced risk management system"""
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        max_portfolio_risk: float = 0.10,  # 10% max portfolio risk
        risk_level: RiskLevel = RiskLevel.MODERATE,
        enable_correlation_checks: bool = True
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.risk_level = risk_level
        self.enable_correlation_checks = enable_correlation_checks
        
        self.positions: Dict[str, PositionRisk] = {}
        self.trade_history: List[Dict] = []
        self.risk_metrics_history: List[PortfolioRisk] = []
        
        self.logger = self._setup_logger()
        
        # Risk limits based on risk level
        self.risk_limits = {
            RiskLevel.CONSERVATIVE: {
                'max_position_size': 0.05,  # 5% of capital
                'max_correlation': 0.3,
                'min_risk_reward': 2.0,
                'stop_loss_pct': 0.02,  # 2% stop loss
                'max_concurrent_trades': 3
            },
            RiskLevel.MODERATE: {
                'max_position_size': 0.10,  # 10% of capital
                'max_correlation': 0.5,
                'min_risk_reward': 1.5,
                'stop_loss_pct': 0.05,  # 5% stop loss
                'max_concurrent_trades': 5
            },
            RiskLevel.AGGRESSIVE: {
                'max_position_size': 0.20,  # 20% of capital
                'max_correlation': 0.7,
                'min_risk_reward': 1.0,
                'stop_loss_pct': 0.10,  # 10% stop loss
                'max_concurrent_trades': 10
            }
        }
        
        self.logger.info(f"RiskManager initialized with {risk_level.name} risk level")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        risk_amount: Optional[float] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate optimal position size using Kelly Criterion and risk-based sizing
        
        Returns:
            Tuple of (position_size, risk_metrics)
        """
        if risk_amount is None:
            risk_amount = self.current_capital * self.risk_per_trade
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            self.logger.warning("Stop loss price equals entry price, no risk calculation possible")
            return 0.0, {}
        
        # Basic position sizing
        basic_position_size = risk_amount / risk_per_unit
        
        # Apply Kelly Criterion (simplified)
        win_rate = 0.55  # Assumed win rate, should be calibrated
        avg_win = 2.0    # Assumed average win ratio (2:1)
        avg_loss = 1.0
        
        kelly_fraction = win_rate - ((1 - win_rate) / avg_win)
        kelly_position_size = self.current_capital * kelly_fraction / risk_per_unit
        
        # Apply risk level constraints
        max_position_by_capital = self.current_capital * self.risk_limits[self.risk_level]['max_position_size']
        max_position_by_price = max_position_by_capital / entry_price
        
        # Choose the most conservative sizing
        position_size = min(
            basic_position_size,
            kelly_position_size,
            max_position_by_price
        )
        
        # Round to appropriate decimal places
        if entry_price > 1000:
            position_size = round(position_size, 3)
        elif entry_price > 100:
            position_size = round(position_size, 2)
        else:
            position_size = round(position_size, 1)
        
        risk_metrics = {
            'basic_position_size': basic_position_size,
            'kelly_position_size': kelly_position_size,
            'max_allowed_position': max_position_by_price,
            'risk_per_trade': risk_amount,
            'risk_per_unit': risk_per_unit,
            'position_size': position_size,
            'position_value': position_size * entry_price,
            'position_percentage': (position_size * entry_price) / self.current_capital * 100
        }
        
        return position_size, risk_metrics
    
    def calculate_var(
        self,
        returns: List[float],
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """Calculate Value at Risk (VaR) using historical and parametric methods"""
        if not returns:
            return {'historical_var': 0.0, 'parametric_var': 0.0, 'cvar': 0.0}
        
        returns_array = np.array(returns)
        
        # Historical VaR
        historical_var = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        # Parametric VaR (assuming normal distribution)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array)
        z_score = stats.norm.ppf(1 - confidence_level)
        parametric_var = mean_return + z_score * std_return
        
        # Conditional VaR (Expected Shortfall)
        cvar = returns_array[returns_array <= historical_var].mean()
        
        return {
            'historical_var': abs(historical_var),
            'parametric_var': abs(parametric_var),
            'cvar': abs(cvar) if not np.isnan(cvar) else 0.0,
            'mean_return': mean_return,
            'std_return': std_return
        }
    
    def calculate_portfolio_metrics(
        self,
        position_metrics: Dict[str, PositionRisk],
        historical_returns: Optional[Dict[str, List[float]]] = None
    ) -> PortfolioRisk:
        """Calculate comprehensive portfolio risk metrics"""
        
        total_value = sum(pos.position_size * pos.current_price for pos in position_metrics.values())
        
        # Calculate individual position values
        position_values = {
            symbol: pos.position_size * pos.current_price
            for symbol, pos in position_metrics.items()
        }
        
        # Calculate weights
        weights = {
            symbol: value / total_value if total_value > 0 else 0
            for symbol, value in position_values.items()
        }
        
        # Calculate portfolio volatility if we have historical returns
        portfolio_volatility = 0.0
        correlation_matrix = None
        beta_coefficients = None
        
        if historical_returns and len(historical_returns) > 1:
            # Create returns DataFrame
            returns_df = pd.DataFrame(historical_returns)
            
            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()
            
            # Calculate portfolio volatility
            cov_matrix = returns_df.cov()
            weights_array = np.array(list(weights.values()))
            portfolio_variance = weights_array.T @ cov_matrix.values @ weights_array
            portfolio_volatility = np.sqrt(portfolio_variance) * np.sqrt(252)  # Annualized
            
            # Calculate beta coefficients (simplified)
            if 'BTC' in historical_returns:
                market_returns = historical_returns['BTC']
                beta_coefficients = {}
                
                for symbol in historical_returns:
                    if symbol != 'BTC' and len(historical_returns[symbol]) == len(market_returns):
                        covariance = np.cov(historical_returns[symbol], market_returns)[0, 1]
                        market_variance = np.var(market_returns)
                        beta = covariance / market_variance if market_variance != 0 else 0
                        beta_coefficients[symbol] = beta
        
        # Calculate VaR for portfolio
        portfolio_returns = []
        if historical_returns:
            # Combine returns for portfolio (simplified)
            for i in range(min(len(r) for r in historical_returns.values())):
                portfolio_return = sum(
                    weights[symbol] * historical_returns[symbol][i]
                    for symbol in historical_returns
                    if i < len(historical_returns[symbol])
                )
                portfolio_returns.append(portfolio_return)
        
        var_metrics = self.calculate_var(portfolio_returns) if portfolio_returns else {}
        
        # Calculate drawdown
        if portfolio_returns:
            cumulative_returns = np.cumprod([1 + r for r in portfolio_returns])
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
            current_drawdown = abs(drawdowns[-1]) if len(drawdowns) > 0 else 0
        else:
            max_drawdown = 0.0
            current_drawdown = 0.0
        
        # Calculate Sharpe and Sortino ratios (simplified)
        risk_free_rate = 0.02  # 2% annual risk-free rate
        sharpe_ratio = 0.0
        sortino_ratio = 0.0
        
        if portfolio_returns and len(portfolio_returns) > 1:
            avg_return = np.mean(portfolio_returns) * 252  # Annualized
            std_return = np.std(portfolio_returns) * np.sqrt(252)
            
            if std_return > 0:
                sharpe_ratio = (avg_return - risk_free_rate) / std_return
            
            # Sortino ratio (only downside deviation)
            downside_returns = [r for r in portfolio_returns if r < 0]
            if downside_returns:
                downside_std = np.std(downside_returns) * np.sqrt(252)
                if downside_std > 0:
                    sortino_ratio = (avg_return - risk_free_rate) / downside_std
        
        return PortfolioRisk(
            total_value=total_value,
            total_risk=portfolio_volatility,
            value_at_risk_95=var_metrics.get('historical_var', 0.0),
            conditional_var_95=var_metrics.get('cvar', 0.0),
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            volatility=portfolio_volatility,
            correlation_matrix=correlation_matrix,
            beta_coefficients=beta_coefficients
        )
    
    def validate_trade(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        position_value: float,
        existing_positions: Dict[str, PositionRisk]
    ) -> Tuple[bool, List[str]]:
        """Validate trade against all risk rules"""
        errors = []
        
        # 1. Check position size against capital
        position_percentage = (position_value / self.current_capital) * 100
        max_position_pct = self.risk_limits[self.risk_level]['max_position_size'] * 100
        
        if position_percentage > max_position_pct:
            errors.append(f"Position size {position_percentage:.1f}% exceeds maximum {max_position_pct}%")
        
        # 2. Check risk-reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk > 0:
            risk_reward_ratio = reward / risk
            min_rr = self.risk_limits[self.risk_level]['min_risk_reward']
            
            if risk_reward_ratio < min_rr:
                errors.append(f"Risk-reward ratio {risk_reward_ratio:.2f} below minimum {min_rr}")
        else:
            errors.append("Invalid stop loss (same as entry price)")
        
        # 3. Check maximum concurrent trades
        max_trades = self.risk_limits[self.risk_level]['max_concurrent_trades']
        current_trades = len(existing_positions)
        
        if current_trades >= max_trades:
            errors.append(f"Maximum concurrent trades ({max_trades}) reached")
        
        # 4. Check portfolio concentration
        total_exposure = sum(
            pos.position_size * pos.current_price 
            for pos in existing_positions.values()
        ) + position_value
        
        concentration_limit = self.current_capital * 0.8  # 80% maximum exposure
        if total_exposure > concentration_limit:
            errors.append(f"Total portfolio exposure {total_exposure:.2f} exceeds limit {concentration_limit:.2f}")
        
        # 5. Check stop loss distance
        stop_loss_pct = abs(entry_price - stop_loss) / entry_price
        max_stop_loss = self.risk_limits[self.risk_level]['stop_loss_pct']
        
        if stop_loss_pct > max_stop_loss:
            errors.append(f"Stop loss distance {stop_loss_pct*100:.1f}% exceeds maximum {max_stop_loss*100}%")
        
        # 6. Check daily loss limit (simplified)
        daily_loss_limit = self.current_capital * 0.05  # 5% daily loss limit
        estimated_loss = position_value * stop_loss_pct
        
        if estimated_loss > daily_loss_limit:
            errors.append(f"Estimated loss {estimated_loss:.2f} exceeds daily limit {daily_loss_limit:.2f}")
        
        return len(errors) == 0, errors
    
    def update_position_risk(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        take_profit: float,
        volatility: float = 0.0
    ) -> None:
        """Update or add position risk metrics"""
        
        # Calculate risk metrics for this position
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Calculate estimated VaR (simplified)
        estimated_var = position_size * current_price * volatility * 1.65  # 95% confidence
        
        position_risk = PositionRisk(
            symbol=symbol,
            position_size=position_size,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volatility=volatility,
            value_at_risk=estimated_var,
            expected_loss=position_size * risk,
            risk_reward_ratio=risk_reward,
            margin_requirement=position_size * current_price * 0.1  # 10% margin
        )
        
        self.positions[symbol] = position_risk
        self.logger.info(f"Updated risk metrics for {symbol}")
    
    def calculate_stress_test_scenarios(
        self,
        positions: Dict[str, PositionRisk],
        scenarios: List[Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate portfolio impact under stress scenarios"""
        
        results = {}
        
        for scenario in scenarios:
            scenario_name = scenario.get('name', 'Unnamed Scenario')
            scenario_results = {
                'total_loss': 0.0,
                'max_position_loss': 0.0,
                'positions_affected': 0
            }
            
            for symbol, position in positions.items():
                price_shock = scenario.get(symbol, 0.0)
                if price_shock != 0:
                    shock_multiplier = 1 + (price_shock / 100)
                    shocked_value = position.position_size * position.current_price * shock_multiplier
                    current_value = position.position_size * position.current_price
                    loss = current_value - shocked_value
                    
                    scenario_results['total_loss'] += loss
                    scenario_results['max_position_loss'] = max(
                        scenario_results['max_position_loss'],
                        abs(loss)
                    )
                    scenario_results['positions_affected'] += 1
            
            results[scenario_name] = scenario_results
        
        return results
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        
        portfolio_metrics = self.calculate_portfolio_metrics(self.positions)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'capital_metrics': {
                'initial_capital': self.initial_capital,
                'current_capital': self.current_capital,
                'total_pnl': self.current_capital - self.initial_capital,
                'pnl_percentage': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
            },
            'risk_settings': {
                'risk_level': self.risk_level.name,
                'risk_per_trade': self.risk_per_trade,
                'max_portfolio_risk': self.max_portfolio_risk,
                'current_limits': self.risk_limits[self.risk_level]
            },
            'portfolio_metrics': {
                'total_value': portfolio_metrics.total_value,
                'total_risk': portfolio_metrics.total_risk,
                'var_95': portfolio_metrics.value_at_risk_95,
                'cvar_95': portfolio_metrics.conditional_var_95,
                'sharpe_ratio': portfolio_metrics.sharpe_ratio,
                'sortino_ratio': portfolio_metrics.sortino_ratio,
                'max_drawdown': portfolio_metrics.max_drawdown * 100,  # Convert to percentage
                'current_drawdown': portfolio_metrics.current_drawdown * 100
            },
            'positions': {
                symbol: {
                    'size': pos.position_size,
                    'value': pos.position_size * pos.current_price,
                    'unrealized_pnl': (pos.current_price - pos.entry_price) * pos.position_size,
                    'risk_metrics': {
                        'stop_loss': pos.stop_loss,
                        'take_profit': pos.take_profit,
                        'risk_reward': pos.risk_reward_ratio,
                        'var': pos.value_at_risk,
                        'volatility': pos.volatility
                    }
                }
                for symbol, pos in self.positions.items()
            },
            'risk_assessment': self._assess_risk_level(portfolio_metrics)
        }
        
        return report
    
    def _assess_risk_level(self, metrics: PortfolioRisk) -> Dict[str, Any]:
        """Assess current risk level based on metrics"""
        
        risk_score = 0
        
        # Volatility assessment
        if metrics.volatility > 0.4:
            risk_score += 3
        elif metrics.volatility > 0.2:
            risk_score += 2
        elif metrics.volatility > 0.1:
            risk_score += 1
        
        # Drawdown assessment
        if metrics.current_drawdown > 0.2:
            risk_score += 3
        elif metrics.current_drawdown > 0.1:
            risk_score += 2
        elif metrics.current_drawdown > 0.05:
            risk_score += 1
        
        # VaR assessment
        if metrics.value_at_risk_95 > self.current_capital * 0.1:
            risk_score += 2
        elif metrics.value_at_risk_95 > self.current_capital * 0.05:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 5:
            risk_assessment = "HIGH RISK"
            action = "Consider reducing positions"
        elif risk_score >= 3:
            risk_assessment = "MEDIUM RISK"
            action = "Monitor closely"
        else:
            risk_assessment = "LOW RISK"
            action = "Within normal parameters"
        
        return {
            'risk_score': risk_score,
            'assessment': risk_assessment,
            'recommended_action': action,
            'warning_level': 'red' if risk_score >= 5 else 'yellow' if risk_score >= 3 else 'green'
        }
    
    def save_risk_report(self, filepath: str) -> None:
        """Save risk report to file"""
        report = self.generate_risk_report()
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Risk report saved to {filepath}")


# Example usage
def example_usage():
    """Example of how to use the RiskManager class"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create risk manager
    risk_manager = RiskManager(
        initial_capital=10000.0,
        risk_per_trade=0.02,
        risk_level=RiskLevel.MODERATE
    )
    
    # Simulate some positions
    risk_manager.update_position_risk(
        symbol="BTC/USDT",
        position_size=0.1,
        entry_price=50000.0,
        current_price=51000.0,
        stop_loss=49000.0,
        take_profit=55000.0,
        volatility=0.02
    )
    
    risk_manager.update_position_risk(
        symbol="ETH/USDT",
        position_size=2.0,
        entry_price=3000.0,
        current_price=3100.0,
        stop_loss=2900.0,
        take_profit=3500.0,
        volatility=0.03
    )
    
    # Calculate position size for new trade
    position_size, metrics = risk_manager.calculate_position_size(
        entry_price=100.0,
        stop_loss_price=95.0,
        risk_amount=200.0  # $200 risk on this trade
    )
    
    print(f"Calculated position size: {position_size}")
    print(f"Position metrics: {metrics}")
    
    # Validate a trade
    is_valid, errors = risk_manager.validate_trade(
        symbol="ADA/USDT",
        entry_price=0.5,
        stop_loss=0.45,
        take_profit=0.6,
        position_size=1000.0,
        position_value=500.0,
        existing_positions=risk_manager.positions
    )
    
    print(f"\nTrade validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    # Generate risk report
    report = risk_manager.generate_risk_report()
    print(f"\nRisk Report Summary:")
    print(f"  Total Value: ${report['portfolio_metrics']['total_value']:.2f}")
    print(f"  Current Risk: {report['risk_assessment']['assessment']}")
    print(f"  Recommended: {report['risk_assessment']['recommended_action']}")
    
    # Calculate VaR for sample returns
    sample_returns = [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, -0.005]
    var_metrics = risk_manager.calculate_var(sample_returns)
    
    print(f"\nVaR Metrics:")
    print(f"  Historical VaR (95%): {var_metrics['historical_var']*100:.2f}%")
    print(f"  Conditional VaR: {var_metrics['cvar']*100:.2f}%")
    
    # Stress test
    scenarios = [
        {'name': 'Market Crash', 'BTC/USDT': -20, 'ETH/USDT': -25},
        {'name': 'Volatility Spike', 'BTC/USDT': -10, 'ETH/USDT': -15}
    ]
    
    stress_results = risk_manager.calculate_stress_test_scenarios(
        risk_manager.positions,
        scenarios
    )
    
    print(f"\nStress Test Results:")
    for scenario, results in stress_results.items():
        print(f"  {scenario}: ${results['total_loss']:.2f} total loss")


if __name__ == "__main__":
    example_usage()