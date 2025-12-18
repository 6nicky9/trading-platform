"""
Trading bots module
"""

from abc import ABC, abstractmethod

class BaseTradingBot(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_running = False
        
    @abstractmethod
    def on_market_data(self, data: dict):
        """Process market data"""
        pass
        
    @abstractmethod
    def execute_strategy(self):
        """Execute trading strategy"""
        pass
        
    def start(self):
        """Start the bot"""
        self.is_running = True
        print(f"Starting bot: {self.name}")
        
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        print(f"Stopping bot: {self.name}")
