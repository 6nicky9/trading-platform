#!/usr/bin/env python3
"""
Enhanced trading bot runner
"""

import yaml
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.strategies.SimpleStrategy import SimpleStrategy
from src.risk.RiskManager import RiskManager, RiskLevel
from src.exchange.BinanceClient import BinanceClient
from src.utils.Logger import TradeLogger

class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config_file: str = 'config.yaml'):
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.initialize_components()
        
    def load_config(self, config_file: str):
        """Load configuration file"""
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("TradingBot")
    
    def initialize_components(self):
        """Initialize all bot components"""
        # Strategy
        strategy_cfg = self.config['strategy']['parameters']
        self.strategy = SimpleStrategy(
            fast_period=strategy_cfg['fast_period'],
            slow_period=strategy_cfg['slow_period']
        )
        
        # Risk Manager
        self.risk_manager = RiskManager(
            initial_capital=self.config['trading']['initial_balance'],
            risk_per_trade=self.config['risk']['risk_per_trade'],
            risk_level=RiskLevel.MODERATE
        )
        
        # Exchange Client
        self.exchange = BinanceClient(
            testnet=self.config['trading']['test_mode']
        )
        
        # Trade Logger
        self.trade_logger = TradeLogger()
        
        self.logger.info("All components initialized")
    
    def run(self):
        """Main bot loop"""
        self.logger.info("Starting trading bot...")
        
        # Get account info
        balance = self.exchange.get_account_balance()
        self.logger.info(f"Account balance: {balance}")
        
        # Monitor symbols
        symbols = self.config['trading']['symbols']
        
        for symbol in symbols[:2]:  # Test with first 2 symbols
            price = self.exchange.get_ticker_price(symbol)
            if price:
                self.logger.info(f"{symbol} price: ${price}")
                
                # Get historical data
                klines = self.exchange.get_klines(symbol, '1h', 50)
                if klines:
                    prices = [float(k['close']) for k in klines]
                    
                    # Generate signal
                    market_data = {
                        'symbol': symbol,
                        'prices': prices,
                        'current_price': float(price)
                    }
                    
                    signal = self.strategy.generate_signal(market_data)
                    
                    if signal['action']:
                        self.execute_trade(symbol, signal, float(price))
    
    def execute_trade(self, symbol: str, signal: Dict, price: float):
        """Execute a trade based on signal"""
        self.logger.info(f"Signal detected: {signal}")
        
        # Calculate position size
        stop_loss = price * (1 - self.config['risk']['stop_loss_pct'])
        position_size, metrics = self.risk_manager.calculate_position_size(
            entry_price=price,
            stop_loss_price=stop_loss
        )
        
        # Log trade
        trade_data = {
            'symbol': symbol,
            'action': signal['action'],
            'price': price,
            'size': float(position_size),
            'value': float(metrics.get('position_value', 0)),
            'confidence': signal['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.trade_logger.log_trade(trade_data)
        self.logger.info(f"Trade executed: {trade_data}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 ENHANCED TRADING BOT v1.0")
    print("="*60)
    
    bot = TradingBot()
    bot.run()
