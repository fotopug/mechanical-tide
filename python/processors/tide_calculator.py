"""
Tide position calculator
Calculates current position in tidal cycle for LED display
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from ..utils.logger import get_logger


class TideCalculator:
    """Calculate tide position for clock-style display"""
    
    TIDE_CYCLE_HOURS = 12.4  # Average semidiurnal tide cycle
    
    def __init__(self, num_leds: int = 10):
        """
        Initialize tide calculator
        
        Args:
            num_leds: Number of LEDs in the display ring
        """
        self.num_leds = num_leds
        self.logger = get_logger()
    
    def calculate_position(self, current_time: datetime, 
                          predictions: List[Dict]) -> Optional[float]:
        """
        Calculate current tide position for LED display
        
        Args:
            current_time: Current time (UTC)
            predictions: List of prediction dicts with 'time' and 'water_level_ft'
        
        Returns:
            LED position (0.0 - 9.999) or None if cannot calculate
        """
        if not predictions or len(predictions) < 2:
            self.logger.warning("Insufficient predictions for position calculation")
            return None
        
        # Find high and low tides around current time
        last_high, next_low = self._find_bracketing_tides(current_time, predictions)
        
        if last_high is None or next_low is None:
            # Fallback: interpolate from nearest predictions
            return self._interpolate_position(current_time, predictions)
        
        # Calculate elapsed time since last high tide
        elapsed = (current_time - last_high['time']).total_seconds() / 3600  # hours
        
        # Map to LED position (0 = high tide at top)
        position = (elapsed / self.TIDE_CYCLE_HOURS) * self.num_leds
        position = position % self.num_leds  # Wrap around
        
        return position
    
    def _find_bracketing_tides(self, current_time: datetime, 
                               predictions: List[Dict]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Find last high tide and next low tide around current time
        
        Args:
            current_time: Current time
            predictions: List of predictions
        
        Returns:
            Tuple of (last_high, next_low) or (None, None)
        """
        # Sort predictions by time
        sorted_preds = sorted(predictions, key=lambda p: p['time'])
        
        # Find local maxima (high tides) and minima (low tides)
        highs = []
        lows = []
        
        for i in range(1, len(sorted_preds) - 1):
            prev_level = sorted_preds[i-1]['water_level_ft']
            curr_level = sorted_preds[i]['water_level_ft']
            next_level = sorted_preds[i+1]['water_level_ft']
            
            # Local maximum (high tide)
            if prev_level < curr_level > next_level:
                highs.append(sorted_preds[i])
            # Local minimum (low tide)
            elif prev_level > curr_level < next_level:
                lows.append(sorted_preds[i])
        
        # Find last high tide before current time
        last_high = None
        for high in reversed(highs):
            if high['time'] <= current_time:
                last_high = high
                break
        
        # Find next low tide after current time
        next_low = None
        for low in lows:
            if low['time'] >= current_time:
                next_low = low
                break
        
        return last_high, next_low
    
    def _interpolate_position(self, current_time: datetime, 
                             predictions: List[Dict]) -> Optional[float]:
        """
        Interpolate position from nearest predictions
        
        Args:
            current_time: Current time
            predictions: List of predictions
        
        Returns:
            Estimated LED position or None
        """
        # Find predictions bracketing current time
        sorted_preds = sorted(predictions, key=lambda p: p['time'])
        
        before = None
        after = None
        
        for pred in sorted_preds:
            if pred['time'] <= current_time:
                before = pred
            elif pred['time'] > current_time and after is None:
                after = pred
                break
        
        if before is None or after is None:
            return None
        
        # Linear interpolation of water level
        time_fraction = ((current_time - before['time']).total_seconds() / 
                        (after['time'] - before['time']).total_seconds())
        
        current_level = (before['water_level_ft'] + 
                        time_fraction * (after['water_level_ft'] - before['water_level_ft']))
        
        # Estimate position based on water level
        # This is rough, but works when we don't have clear high/low tides
        # Assume water level correlates with position in cycle
        
        # Find min/max water levels in predictions
        levels = [p['water_level_ft'] for p in predictions]
        min_level = min(levels)
        max_level = max(levels)
        
        if max_level == min_level:
            return 0.0  # No variation
        
        # Normalize current level to 0-1
        normalized = (current_level - min_level) / (max_level - min_level)
        
        # Map to LED position (high water = 0, low water = 5)
        # This is approximate
        position = (1.0 - normalized) * (self.num_leds / 2)
        
        return position % self.num_leds
    
    def interpolate_water_level(self, current_time: datetime, 
                               predictions: List[Dict]) -> Optional[float]:
        """
        Interpolate current water level from predictions
        
        Args:
            current_time: Current time
            predictions: List of predictions
        
        Returns:
            Interpolated water level in feet, or None
        """
        if not predictions:
            return None
        
        sorted_preds = sorted(predictions, key=lambda p: p['time'])
        
        # Find bracketing predictions
        before = None
        after = None
        
        for pred in sorted_preds:
            if pred['time'] <= current_time:
                before = pred
            elif pred['time'] > current_time and after is None:
                after = pred
                break
        
        if before is None:
            return sorted_preds[0]['water_level_ft']
        if after is None:
            return sorted_preds[-1]['water_level_ft']
        
        # Linear interpolation
        time_fraction = ((current_time - before['time']).total_seconds() / 
                        (after['time'] - before['time']).total_seconds())
        
        water_level = (before['water_level_ft'] + 
                      time_fraction * (after['water_level_ft'] - before['water_level_ft']))
        
        return water_level
