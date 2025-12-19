"""
Risk management module for trading platform
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Risk management system for monitoring and controlling trading risks
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize risk manager with configuration
        
        Args:
            config: Risk configuration dictionary
        """
        self.config = config or {
            "max_position_size": 1000.0,      # Maximum position size in base currency
            "max_daily_loss": 500.0,          # Maximum daily loss allowed
            "max_open_positions": 5,          # Maximum number of simultaneous open positions
            "max_leverage": 10.0,             # Maximum leverage allowed
            "stop_loss_percentage": 2.0,      # Default stop loss percentage
            "take_profit_percentage": 5.0,    # Default take profit percentage
            "risk_per_trade": 0.02,           # Risk per trade (2% of capital)
        }
        
        self.today_pnl = 0.0                  # Today's profit/loss
        self.open_positions = []              # List of open positions
        self.trade_history = []               # History of all trades
        self.daily_stats = {
            "date": datetime.now().date().isoformat(),
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
        }
        
        logger.info("Risk Manager initialized")
    
    def can_open_position(
        self,
        symbol: str,
        size: float,
        price: float,
        leverage: float = 1.0,
        position_type: str = "long"
    ) -> Dict:
        """
        Check if a new position can be opened
        
        Args:
            symbol: Trading pair symbol
            size: Position size
            price: Entry price
            leverage: Leverage to use
            position_type: 'long' or 'short'
            
        Returns:
            Dict: Result with 'allowed' flag and 'reason' if not allowed
        """
        checks = []
        
        # 1. Check position size limit
        position_value = size * price * leverage
        if position_value > self.config["max_position_size"]:
            checks.append(False)
            return {
                "allowed": False,
                "reason": f"Position value ${position_value:.2f} exceeds max ${self.config['max_position_size']:.2f}"
            }
        
        # 2. Check leverage limit
        if leverage > self.config["max_leverage"]:
            checks.append(False)
            return {
                "allowed": False,
                "reason": f"Leverage {leverage}x exceeds max {self.config['max_leverage']}x"
            }
        
        # 3. Check open positions count
        if len(self.open_positions) >= self.config["max_open_positions"]:
            checks.append(False)
            return {
                "allowed": False,
                "reason": f"Open positions ({len(self.open_positions)}) exceed max {self.config['max_open_positions']}"
            }
        
        # 4. Check daily loss limit
        if self.today_pnl < -self.config["max_daily_loss"]:
            checks.append(False)
            return {
                "allowed": False,
                "reason": f"Daily loss ${self.today_pnl:.2f} exceeds limit ${-self.config['max_daily_loss']:.2f}"
            }
        
        # 5. Risk per trade check
        risk_amount = position_value * self.config["risk_per_trade"]
        if risk_amount > self.config["max_position_size"] * 0.1:
            checks.append(False)
            return {
                "allowed": False,
                "reason": f"Risk per trade ${risk_amount:.2f} too high"
            }
        
        checks.append(True)
        
        return {
            "allowed": True,
            "checks_passed": len([c for c in checks if c]),
            "position_value": position_value,
            "risk_amount": risk_amount,
            "max_loss": position_value * (self.config["stop_loss_percentage"] / 100),
            "max_profit": position_value * (self.config["take_profit_percentage"] / 100),
        }
    
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss_price: float,
        risk_percentage: Optional[float] = None
    ) -> Dict:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_percentage: Risk percentage (optional, uses config if not provided)
            
        Returns:
            Dict: Position sizing details
        """
        risk_pct = risk_percentage or self.config["risk_per_trade"]
        risk_amount = capital * risk_pct
        
        # Calculate price difference
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return {
                "error": "Stop loss price equals entry price",
                "position_size": 0,
                "risk_amount": risk_amount,
            }
        
        # Calculate position size
        position_size = risk_amount / price_diff
        
        # Apply position size limits
        max_position_value = self.config["max_position_size"]
        max_position_size = max_position_value / entry_price
        
        if position_size > max_position_size:
            position_size = max_position_size
            risk_amount = position_size * price_diff
            logger.warning(f"Position size capped at {max_position_size}")
        
        return {
            "position_size": position_size,
            "risk_amount": risk_amount,
            "risk_percentage": risk_pct,
            "stop_loss_percentage": (price_diff / entry_price) * 100,
            "position_value": position_size * entry_price,
        }
    
    def add_position(
        self,
        position_id: str,
        symbol: str,
        size: float,
        entry_price: float,
        position_type: str = "long",
        leverage: float = 1.0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Add a new position to tracking
        
        Args:
            position_id: Unique position ID
            symbol: Trading pair
            size: Position size
            entry_price: Entry price
            position_type: 'long' or 'short'
            leverage: Leverage used
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            bool: True if position added successfully
        """
        # Use default stop/take profit if not provided
        if stop_loss is None:
            if position_type == "long":
                stop_loss = entry_price * (1 - self.config["stop_loss_percentage"] / 100)
            else:
                stop_loss = entry_price * (1 + self.config["stop_loss_percentage"] / 100)
        
        if take_profit is None:
            if position_type == "long":
                take_profit = entry_price * (1 + self.config["take_profit_percentage"] / 100)
            else:
                take_profit = entry_price * (1 - self.config["take_profit_percentage"] / 100)
        
        position = {
            "id": position_id,
            "symbol": symbol,
            "size": size,
            "entry_price": entry_price,
            "current_price": entry_price,
            "position_type": position_type,
            "leverage": leverage,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "entry_time": datetime.now().isoformat(),
            "pnl": 0.0,
            "pnl_percentage": 0.0,
            "status": "open",
        }
        
        self.open_positions.append(position)
        logger.info(f"Position added: {position_id} ({symbol})")
        
        return True
    
    def update_position_price(self, position_id: str, current_price: float) -> Dict:
        """
        Update position with current price and calculate PnL
        
        Args:
            position_id: Position ID to update
            current_price: Current market price
            
        Returns:
            Dict: Updated position info with PnL
        """
        for position in self.open_positions:
            if position["id"] == position_id:
                position["current_price"] = current_price
                
                # Calculate PnL
                if position["position_type"] == "long":
                    pnl = (current_price - position["entry_price"]) * position["size"]
                else:  # short
                    pnl = (position["entry_price"] - current_price) * position["size"]
                
                pnl_percentage = (pnl / (position["entry_price"] * position["size"])) * 100
                
                position["pnl"] = pnl
                position["pnl_percentage"] = pnl_percentage
                
                # Check stop loss and take profit
                if position["position_type"] == "long":
                    if current_price <= position["stop_loss"]:
                        position["status"] = "stopped"
                        logger.warning(f"Position {position_id} hit stop loss")
                    elif current_price >= position["take_profit"]:
                        position["status"] = "taken"
                        logger.info(f"Position {position_id} hit take profit")
                else:  # short
                    if current_price >= position["stop_loss"]:
                        position["status"] = "stopped"
                        logger.warning(f"Position {position_id} hit stop loss")
                    elif current_price <= position["take_profit"]:
                        position["status"] = "taken"
                        logger.info(f"Position {position_id} hit take profit")
                
                return position
        
        logger.error(f"Position {position_id} not found")
        return {}
    
    def close_position(self, position_id: str, exit_price: float) -> Dict:
        """
        Close a position and record PnL
        
        Args:
            position_id: Position ID to close
            exit_price: Exit price
            
        Returns:
            Dict: Closed position summary
        """
        for i, position in enumerate(self.open_positions):
            if position["id"] == position_id:
                # Calculate final PnL
                if position["position_type"] == "long":
                    pnl = (exit_price - position["entry_price"]) * position["size"]
                else:  # short
                    pnl = (position["entry_price"] - exit_price) * position["size"]
                
                pnl_percentage = (pnl / (position["entry_price"] * position["size"])) * 100
                
                # Update daily stats
                self.today_pnl += pnl
                self.daily_stats["total_pnl"] += pnl
                self.daily_stats["total_trades"] += 1
                
                if pnl > 0:
                    self.daily_stats["winning_trades"] += 1
                else:
                    self.daily_stats["losing_trades"] += 1
                
                # Record trade history
                closed_trade = {
                    **position,
                    "exit_price": exit_price,
                    "final_pnl": pnl,
                    "final_pnl_percentage": pnl_percentage,
                    "exit_time": datetime.now().isoformat(),
                    "status": "closed",
                }
                
                self.trade_history.append(closed_trade)
                
                # Remove from open positions
                self.open_positions.pop(i)
                
                logger.info(f"Position closed: {position_id}, PnL: ${pnl:.2f} ({pnl_percentage:.2f}%)")
                
                return closed_trade
        
        logger.error(f"Position {position_id} not found for closing")
        return {}
    
    def get_risk_summary(self) -> Dict:
        """
        Get current risk summary
        
        Returns:
            Dict: Summary of current risk metrics
        """
        total_exposure = 0.0
        total_pnl = 0.0
        
        for position in self.open_positions:
            position_value = position["size"] * position["current_price"] * position["leverage"]
            total_exposure += position_value
            total_pnl += position["pnl"]
        
        return {
            "open_positions": len(self.open_positions),
            "total_exposure": total_exposure,
            "total_pnl": total_pnl,
            "today_pnl": self.today_pnl,
            "daily_stats": self.daily_stats,
            "config": self.config,
            "max_position_usage": (total_exposure / self.config["max_position_size"]) * 100,
            "daily_loss_usage": abs(self.today_pnl) / self.config["max_daily_loss"] * 100,
        }
    
    def reset_daily_stats(self) -> None:
        """Reset daily statistics"""
        self.today_pnl = 0.0
        self.daily_stats = {
            "date": datetime.now().date().isoformat(),
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
        }
        logger.info("Daily stats reset")
    
    def save_state(self, filepath: str = "risk_state.json") -> bool:
        """Save current risk state to file"""
        try:
            state = {
                "config": self.config,
                "today_pnl": self.today_pnl,
                "open_positions": self.open_positions,
                "trade_history": self.trade_history[-100:],  # Keep last 100 trades
                "daily_stats": self.daily_stats,
                "saved_at": datetime.now().isoformat(),
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Risk state saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save risk state: {e}")
            return False
    
    def load_state(self, filepath: str = "risk_state.json") -> bool:
        """Load risk state from file"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.config = state.get("config", self.config)
            self.today_pnl = state.get("today_pnl", 0.0)
            self.open_positions = state.get("open_positions", [])
            self.trade_history = state.get("trade_history", [])
            self.daily_stats = state.get("daily_stats", self.daily_stats)
            
            logger.info(f"Risk state loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load risk state: {e}")
            return False

# Export main class
__all__ = ['RiskManager']
