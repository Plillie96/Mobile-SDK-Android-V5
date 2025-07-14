"""
Base strategy class for all trading strategies
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}
        self.signals = []
        self.performance = {}
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on market data
        
        Args:
            data: OHLCV market data
            
        Returns:
            Dictionary containing signal information
        """
        pass
    
    @abstractmethod
    def calculate_confidence(self, data: pd.DataFrame) -> float:
        """
        Calculate confidence level for the signal (0-1)
        
        Args:
            data: OHLCV market data
            
        Returns:
            Confidence score between 0 and 1
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data format and requirements
        
        Args:
            data: OHLCV market data
            
        Returns:
            True if data is valid, False otherwise
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        if data.empty:
            return False
            
        if not all(col in data.columns for col in required_columns):
            return False
            
        if len(data) < 50:  # Minimum data points required
            return False
            
        return True
    
    def calculate_risk_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate risk metrics for the strategy
        
        Args:
            data: OHLCV market data
            
        Returns:
            Dictionary of risk metrics
        """
        returns = data['close'].pct_change().dropna()
        
        metrics = {
            'volatility': returns.std() * np.sqrt(252),  # Annualized volatility
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(data['close']),
            'var_95': np.percentile(returns, 5),  # 95% VaR
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }
        
        return metrics
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return drawdown.min()
    
    def update_parameters(self, new_parameters: Dict[str, Any]):
        """Update strategy parameters"""
        self.parameters.update(new_parameters)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters"""
        return self.parameters.copy()
    
    def log_signal(self, signal: Dict[str, Any]):
        """Log generated signal"""
        signal['timestamp'] = datetime.utcnow()
        signal['strategy'] = self.name
        self.signals.append(signal)
    
    def get_recent_signals(self, limit: int = 100) -> list:
        """Get recent signals"""
        return self.signals[-limit:] if self.signals else []
    
    def reset(self):
        """Reset strategy state"""
        self.signals = []
        self.performance = {}