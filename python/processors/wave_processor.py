"""
Wave data processor
Handles wave period clamping and validation
"""

from typing import Optional
from ..utils.logger import get_logger


class WaveProcessor:
    """Process wave data for breathing effect"""
    
    def __init__(self, min_period: float = 2.0, max_period: float = 8.0, 
                 default_period: float = 7.0):
        """
        Initialize wave processor
        
        Args:
            min_period: Minimum allowed period in seconds
            max_period: Maximum allowed period in seconds
            default_period: Default period when no data available
        """
        self.min_period = min_period
        self.max_period = max_period
        self.default_period = default_period
        self.logger = get_logger()
    
    def clamp_period(self, period: Optional[float]) -> float:
        """
        Clamp wave period to allowed range
        
        Args:
            period: Wave period in seconds (or None)
        
        Returns:
            Clamped period within min/max range
        """
        if period is None:
            self.logger.warning(f"No wave period provided, using default {self.default_period}s")
            return self.default_period
        
        if period < self.min_period:
            self.logger.info(f"Wave period {period}s below minimum, clamping to {self.min_period}s")
            return self.min_period
        
        if period > self.max_period:
            self.logger.info(f"Wave period {period}s above maximum, clamping to {self.max_period}s")
            return self.max_period
        
        return period
