"""
Market data module
"""

class MarketData:
    def __init__(self):
        self.connections = []
        
    def connect_exchange(self, exchange_name: str):
        """Connect to exchange"""
        print(f"Connecting to {exchange_name}")
        self.connections.append(exchange_name)
        return True
        
    def get_ticker(self, symbol: str):
        """Get ticker data"""
        return {
            "symbol": symbol,
            "price": 0.0,
            "volume": 0.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
