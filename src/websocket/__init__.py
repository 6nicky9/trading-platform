"""
WebSocket модуль для получения реальных данных с бирж
"""

from .MarketStreamer import MarketStreamer, get_market_streamer

__all__ = ['MarketStreamer', 'get_market_streamer']
