#!/usr/bin/env python3
"""
Простая торговая стратегия
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

class SimpleStrategy:
    """Простая стратегия на основе скользящих средних"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.logger = logging.getLogger(self.__class__.__name__)
        self.signals = []  # История сигналов
        
    def calculate_ma_crossover(self, prices: List[float]) -> Optional[str]:
        """
        Рассчитывает сигнал на основе пересечения скользящих средних
        
        Returns:
            'BUY' - бычий сигнал (быстрая MA выше медленной)
            'SELL' - медвежий сигнал (быстрая MA ниже медленной)
            None - нет сигнала
        """
        if len(prices) < self.slow_period:
            return None
        
        # Рассчитываем скользящие средние
        fast_ma = sum(prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(prices[-self.slow_period:]) / self.slow_period
        
        # Определяем сигнал
        if fast_ma > slow_ma * 1.001:  # Быстрая выше медленной на 0.1%
            signal = 'BUY'
        elif fast_ma < slow_ma * 0.999:  # Быстрая ниже медленной на 0.1%
            signal = 'SELL'
        else:
            signal = None
            
        if signal:
            self.logger.info(f"Signal: {signal} | Fast MA: {fast_ma:.2f}, Slow MA: {slow_ma:.2f}")
            self.signals.append({
                'timestamp': datetime.now(),
                'signal': signal,
                'fast_ma': fast_ma,
                'slow_ma': slow_ma
            })
            
        return signal
    
    def calculate_rsi_signal(self, prices: List[float], period: int = 14) -> Optional[str]:
        """
        Рассчитывает сигнал на основе RSI
        
        Returns:
            'BUY' - RSI ниже 30 (перепроданность)
            'SELL' - RSI выше 70 (перекупленность)
            None - в нейтральной зоне
        """
        if len(prices) < period + 1:
            return None
        
        # Рассчитываем RSI (упрощённо)
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [c for c in changes if c > 0]
        losses = [abs(c) for c in changes if c < 0]
        
        if not losses:  # Если нет убытков
            avg_gain = sum(gains[-period:]) / period
            rsi = 100
        elif not gains:  # Если нет прибылей
            avg_loss = sum(losses[-period:]) / period
            rsi = 0
        else:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Определяем сигнал
        if rsi < 30:
            signal = 'BUY'
        elif rsi > 70:
            signal = 'SELL'
        else:
            signal = None
            
        return signal
    
    def generate_signal(self, market_data: Dict) -> Dict:
        """
        Генерирует торговый сигнал на основе различных индикаторов
        """
        signal = {
            'timestamp': datetime.now(),
            'symbol': market_data.get('symbol', 'BTC/USDT'),
            'action': None,
            'confidence': 0.0,
            'indicators': {}
        }
        
        # Получаем цены
        prices = market_data.get('prices', [])
        if not prices:
            return signal
        
        # Проверяем MA кроссовер
        ma_signal = self.calculate_ma_crossover(prices)
        
        # Проверяем RSI
        rsi_signal = self.calculate_rsi_signal(prices)
        
        # Принимаем решение
        if ma_signal == 'BUY' and rsi_signal == 'BUY':
            signal['action'] = 'STRONG_BUY'
            signal['confidence'] = 0.9
        elif ma_signal == 'SELL' and rsi_signal == 'SELL':
            signal['action'] = 'STRONG_SELL'
            signal['confidence'] = 0.9
        elif ma_signal == 'BUY':
            signal['action'] = 'BUY'
            signal['confidence'] = 0.6
        elif ma_signal == 'SELL':
            signal['action'] = 'SELL'
            signal['confidence'] = 0.6
            
        signal['indicators'] = {
            'ma_crossover': ma_signal,
            'rsi': rsi_signal,
            'price': prices[-1] if prices else 0
        }
        
        return signal
