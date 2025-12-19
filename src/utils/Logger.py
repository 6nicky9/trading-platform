"""
Logger.py - Enhanced logging system for trades
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

class TradeLogger:
    """Logger for trading operations"""
    
    def __init__(self, log_file: str = "logs/trades.json"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/trading.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("Trading")
    
    def log_trade(self, trade_data: Dict[str, Any]):
        """Log a trade to JSON file"""
        try:
            trade_data['timestamp'] = datetime.now().isoformat()
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(trade_data, default=str) + '\n')
            
            self.logger.info(f"Trade logged: {trade_data}")
        except Exception as e:
            self.logger.error(f"Error logging trade: {e}")
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        try:
            trades = []
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-limit:]  # Last N trades
                for line in lines:
                    trades.append(json.loads(line.strip()))
            return trades
        except FileNotFoundError:
            return []
        except Exception as e:
            self.logger.error(f"Error reading trade history: {e}")
            return []
