"""
MarketStreamer.py - WebSocket клиент для получения реальных данных с бирж
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional, Any
import websockets
import ccxt.pro as ccxtpro
from datetime import datetime
import threading
from queue import Queue
import pandas as pd


class MarketStreamer:
    """WebSocket клиент для потоковых данных с бирж"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.connections: Dict[str, Any] = {}
        self.subscriptions: Dict[str, List[str]] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.data_cache: Dict[str, Any] = {}
        self.running = False
        self.event_loop = None
        self.thread = None
        
    def _setup_logger(self) -> logging.Logger:
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
    
    async def connect_binance_ws(self, streams: List[str]):
        """Подключение к WebSocket Binance"""
        try:
            # Публичный WebSocket Binance
            url = f"wss://stream.binance.com:9443/ws"
            
            # Подписка на несколько потоков
            params = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": 1
            }
            
            async with websockets.connect(url) as websocket:
                await websocket.send(json.dumps(params))
                
                self.logger.info(f"Connected to Binance WebSocket, streams: {streams}")
                
                while self.running:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Обработка разных типов данных
                        if 'e' in data:  # Тип события
                            event_type = data['e']
                            
                            if event_type == 'kline':  # Свечные данные
                                await self._process_kline(data)
                            elif event_type == 'trade':  # Торги
                                await self._process_trade(data)
                            elif event_type == 'depthUpdate':  # Стакан ордеров
                                await self._process_orderbook(data)
                            elif event_type == '24hrTicker':  # 24-часовой тикер
                                await self._process_ticker(data)
                        
                    except Exception as e:
                        self.logger.error(f"Error receiving WebSocket data: {e}")
                        break
                        
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance WebSocket: {e}")
    
    async def connect_bybit_ws(self, streams: List[str]):
        """Подключение к WebSocket Bybit"""
        try:
            url = "wss://stream.bybit.com/v5/public/spot"
            
            # Создаем подписки
            subscriptions = []
            for stream in streams:
                if 'kline' in stream:
                    symbol = stream.split('_')[0]
                    interval = stream.split('_')[1]
                    subscriptions.append(f"kline.{interval}.{symbol}")
                elif 'tickers' in stream:
                    symbol = stream.replace('tickers.', '')
                    subscriptions.append(f"tickers.{symbol}")
            
            async with websockets.connect(url) as websocket:
                # Подписываемся на все потоки
                for sub in subscriptions:
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [sub]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                
                self.logger.info(f"Connected to Bybit WebSocket, streams: {subscriptions}")
                
                while self.running:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if data.get('topic', '').startswith('kline'):
                            await self._process_bybit_kline(data)
                        elif data.get('topic', '').startswith('tickers'):
                            await self._process_bybit_ticker(data)
                            
                    except Exception as e:
                        self.logger.error(f"Error receiving Bybit WebSocket data: {e}")
                        break
                        
        except Exception as e:
            self.logger.error(f"Failed to connect to Bybit WebSocket: {e}")
    
    async def _process_kline(self, data: Dict):
        """Обработка свечных данных"""
        try:
            symbol = data['s'].lower()
            candle = {
                'timestamp': datetime.fromtimestamp(data['k']['t'] / 1000),
                'open': float(data['k']['o']),
                'high': float(data['k']['h']),
                'low': float(data['k']['l']),
                'close': float(data['k']['c']),
                'volume': float(data['k']['v']),
                'is_closed': data['k']['x'],
                'interval': data['k']['i']
            }
            
            # Сохраняем в кеш
            cache_key = f"{symbol}_{data['k']['i']}"
            if cache_key not in self.data_cache:
                self.data_cache[cache_key] = []
            
            candles = self.data_cache[cache_key]
            
            if candle['is_closed']:
                # Добавляем новую свечу
                candles.append(candle)
                # Ограничиваем количество свечей
                if len(candles) > 1000:
                    candles.pop(0)
            else:
                # Обновляем текущую свечу
                if candles and not candles[-1]['is_closed']:
                    candles[-1] = candle
                else:
                    candles.append(candle)
            
            # Вызываем колбэки
            if cache_key in self.callbacks:
                for callback in self.callbacks[cache_key]:
                    try:
                        await callback(candle)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing kline: {e}")
    
    async def _process_trade(self, data: Dict):
        """Обработка данных о торгах"""
        try:
            trade = {
                'symbol': data['s'],
                'price': float(data['p']),
                'quantity': float(data['q']),
                'timestamp': datetime.fromtimestamp(data['T'] / 1000),
                'is_buyer_maker': data['m']
            }
            
            cache_key = f"trades_{data['s'].lower()}"
            if cache_key not in self.data_cache:
                self.data_cache[cache_key] = []
            
            trades = self.data_cache[cache_key]
            trades.append(trade)
            
            if len(trades) > 100:
                trades.pop(0)
            
            # Вызываем колбэки для тикеров
            ticker_key = f"ticker_{data['s'].lower()}"
            if ticker_key in self.callbacks:
                for callback in self.callbacks[ticker_key]:
                    try:
                        await callback({
                            'symbol': data['s'],
                            'last_price': float(data['p']),
                            'volume': float(data['q']),
                            'timestamp': datetime.now()
                        })
                    except Exception as e:
                        self.logger.error(f"Ticker callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing trade: {e}")
    
    async def _process_orderbook(self, data: Dict):
        """Обработка стакана ордеров"""
        try:
            symbol = data['s'].lower()
            cache_key = f"orderbook_{symbol}"
            
            # Инициализируем стакан если его нет
            if cache_key not in self.data_cache:
                self.data_cache[cache_key] = {
                    'bids': [],
                    'asks': [],
                    'last_update_id': data['u']
                }
            
            orderbook = self.data_cache[cache_key]
            
            # Обновляем стакан (упрощенно)
            orderbook['bids'] = data.get('b', orderbook['bids'])
            orderbook['asks'] = data.get('a', orderbook['asks'])
            orderbook['last_update_id'] = data['u']
            orderbook['timestamp'] = datetime.now()
            
            # Вызываем колбэки
            if cache_key in self.callbacks:
                for callback in self.callbacks[cache_key]:
                    try:
                        await callback(orderbook)
                    except Exception as e:
                        self.logger.error(f"Orderbook callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing orderbook: {e}")
    
    async def _process_ticker(self, data: Dict):
        """Обработка тикерных данных"""
        try:
            ticker = {
                'symbol': data['s'],
                'last_price': float(data['c']),
                'high_24h': float(data['h']),
                'low_24h': float(data['l']),
                'volume_24h': float(data['v']),
                'price_change': float(data['p']),
                'price_change_percent': float(data['P']),
                'timestamp': datetime.now()
            }
            
            cache_key = f"ticker_{data['s'].lower()}"
            self.data_cache[cache_key] = ticker
            
            # Вызываем колбэки
            if cache_key in self.callbacks:
                for callback in self.callbacks[cache_key]:
                    try:
                        await callback(ticker)
                    except Exception as e:
                        self.logger.error(f"Ticker callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing ticker: {e}")
    
    async def _process_bybit_kline(self, data: Dict):
        """Обработка свечных данных Bybit"""
        try:
            topic = data['topic']
            symbol = topic.split('.')[-1]
            interval = topic.split('.')[2]
            
            candle_data = data['data'][0]
            candle = {
                'timestamp': datetime.fromtimestamp(int(candle_data['start']) / 1000),
                'open': float(candle_data['open']),
                'high': float(candle_data['high']),
                'low': float(candle_data['low']),
                'close': float(candle_data['close']),
                'volume': float(candle_data['volume']),
                'interval': interval,
                'is_closed': candle_data['confirm']
            }
            
            cache_key = f"{symbol}_{interval}"
            if cache_key not in self.data_cache:
                self.data_cache[cache_key] = []
            
            candles = self.data_cache[cache_key]
            
            if candle['is_closed']:
                candles.append(candle)
                if len(candles) > 1000:
                    candles.pop(0)
            else:
                if candles and not candles[-1]['is_closed']:
                    candles[-1] = candle
                else:
                    candles.append(candle)
            
            if cache_key in self.callbacks:
                for callback in self.callbacks[cache_key]:
                    try:
                        await callback(candle)
                    except Exception as e:
                        self.logger.error(f"Bybit callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing Bybit kline: {e}")
    
    async def _process_bybit_ticker(self, data: Dict):
        """Обработка тикерных данных Bybit"""
        try:
            ticker_data = data['data']
            ticker = {
                'symbol': ticker_data['symbol'],
                'last_price': float(ticker_data['lastPrice']),
                'high_24h': float(ticker_data['highPrice24h']),
                'low_24h': float(ticker_data['lowPrice24h']),
                'volume_24h': float(ticker_data['volume24h']),
                'price_change': float(ticker_data['price24hPcnt']),
                'timestamp': datetime.now()
            }
            
            cache_key = f"ticker_{ticker_data['symbol'].lower()}"
            self.data_cache[cache_key] = ticker
            
            if cache_key in self.callbacks:
                for callback in self.callbacks[cache_key]:
                    try:
                        await callback(ticker)
                    except Exception as e:
                        self.logger.error(f"Bybit ticker callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error processing Bybit ticker: {e}")
    
    def subscribe(self, exchange: str, symbol: str, stream_type: str, callback: Callable):
        """Подписка на поток данных"""
        try:
            stream_key = f"{exchange}_{symbol}_{stream_type}"
            
            if stream_key not in self.callbacks:
                self.callbacks[stream_key] = []
            
            self.callbacks[stream_key].append(callback)
            
            # Запускаем соединение если еще не запущено
            if not self.running:
                self.start()
            
            self.logger.info(f"Subscribed to {stream_key}")
            
        except Exception as e:
            self.logger.error(f"Error subscribing to stream: {e}")
    
    def unsubscribe(self, exchange: str, symbol: str, stream_type: str, callback: Callable):
        """Отписка от потока данных"""
        try:
            stream_key = f"{exchange}_{symbol}_{stream_type}"
            
            if stream_key in self.callbacks:
                if callback in self.callbacks[stream_key]:
                    self.callbacks[stream_key].remove(callback)
                    
                if not self.callbacks[stream_key]:
                    del self.callbacks[stream_key]
            
            self.logger.info(f"Unsubscribed from {stream_key}")
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from stream: {e}")
    
    def get_latest_data(self, exchange: str, symbol: str, stream_type: str, limit: int = 100):
        """Получение последних данных из кеша"""
        try:
            cache_key = f"{exchange}_{symbol}_{stream_type}"
            
            if cache_key in self.data_cache:
                data = self.data_cache[cache_key]
                
                if isinstance(data, list):
                    return data[-limit:] if len(data) > limit else data
                else:
                    return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest data: {e}")
            return None
    
    def start(self):
        """Запуск WebSocket клиента в отдельном потоке"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            self.logger.info("WebSocket client started")
    
    def stop(self):
        """Остановка WebSocket клиента"""
        if self.running:
            self.running = False
            
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
            
            if self.thread:
                self.thread.join(timeout=5)
            
            self.logger.info("WebSocket client stopped")
    
    def _run_event_loop(self):
        """Запуск асинхронного event loop в отдельном потоке"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        
        # Запускаем подключения к биржам
        tasks = []
        
        # Пример подключения к Binance
        binance_streams = [
            "btcusdt@kline_1m",
            "btcusdt@trade",
            "btcusdt@depth20@100ms",
            "ethusdt@kline_1m",
            "ethusdt@trade"
        ]
        
        tasks.append(self.event_loop.create_task(self.connect_binance_ws(binance_streams)))
        
        # Запускаем все задачи
        try:
            self.event_loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            self.logger.error(f"Event loop error: {e}")
        finally:
            self.event_loop.close()


# Синглтон для глобального доступа
market_streamer = MarketStreamer()


def get_market_streamer():
    """Получение глобального экземпляра MarketStreamer"""
    return market_streamer


if __name__ == "__main__":
    # Пример использования
    import time
    
    def print_candle(candle):
        print(f"New candle: {candle['close']} at {candle['timestamp']}")
    
    def print_trade(trade):
        print(f"Trade: {trade['symbol']} {trade['price']} x {trade['quantity']}")
    
    # Создаем и запускаем стример
    streamer = MarketStreamer()
    
    # Подписываемся на данные
    streamer.subscribe("binance", "btcusdt", "kline_1m", print_candle)
    streamer.subscribe("binance", "btcusdt", "trade", print_trade)
    
    # Запускаем
    streamer.start()
    
    try:
        # Ждем 30 секунд
        time.sleep(30)
    finally:
        # Останавливаем
        streamer.stop()
