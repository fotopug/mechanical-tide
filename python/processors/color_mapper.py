"""
Color mapping for water level visualization
Maps water level relative to MSL to heat-map colors
"""

from typing import Tuple, Dict
import numpy as np


class ColorMapper:
    """Map water level to RGB colors using heat-map"""
    
    def __init__(self, thresholds: Dict[float, Tuple[int, int, int]]):
        """
        Initialize color mapper
        
        Args:
            thresholds: Dict mapping water level (ft) to RGB tuples
                       Example: {-2.0: (0, 50, 255), 0.0: (0, 255, 0), 2.0: (255, 100, 0)}
        """
        # Sort thresholds by water level
        self.thresholds = sorted(thresholds.items(), key=lambda x: float(x[0]))
    
    def height_to_rgb(self, height_ft: float) -> Tuple[int, int, int]:
        """
        Convert water height to RGB color using smooth interpolation
        
        Args:
            height_ft: Water level in feet relative to MSL
        
        Returns:
            RGB tuple (0-255, 0-255, 0-255)
        """
        # Handle out-of-range values
        if height_ft <= self.thresholds[0][0]:
            return self.thresholds[0][1]
        if height_ft >= self.thresholds[-1][0]:
            return self.thresholds[-1][1]
        
        # Find bracketing thresholds
        for i in range(len(self.thresholds) - 1):
            low_h, low_c = self.thresholds[i]
            high_h, high_c = self.thresholds[i + 1]
            
            if low_h <= height_ft <= high_h:
                # Linear interpolation
                t = (height_ft - low_h) / (high_h - low_h)
                
                r = int(low_c[0] + t * (high_c[0] - low_c[0]))
                g = int(low_c[1] + t * (high_c[1] - low_c[1]))
                b = int(low_c[2] + t * (high_c[2] - low_c[2]))
                
                # Clamp to valid range
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                
                return (r, g, b)
        
        # Fallback (should never reach here)
        return self.thresholds[-1][1]
    
    def get_color_description(self, height_ft: float) -> str:
        """
        Get human-readable description of color/water level
        
        Args:
            height_ft: Water level in feet relative to MSL
        
        Returns:
            Description string (e.g., "High tide (orange)")
        """
        if height_ft < -2.0:
            return "Very low tide (deep blue)"
        elif height_ft < -1.0:
            return "Low tide (blue)"
        elif height_ft < -0.3:
            return "Below mean (cyan)"
        elif height_ft < 0.3:
            return "At mean level (green)"
        elif height_ft < 1.0:
            return "Slightly above mean (yellow-green)"
        elif height_ft < 2.0:
            return "Above mean (yellow)"
        elif height_ft < 3.0:
            return "High tide (orange)"
        else:
            return "Very high tide / storm surge (red)"


def create_default_color_mapper() -> ColorMapper:
    """
    Create color mapper with default heat-map thresholds
    
    Returns:
        ColorMapper instance with standard thresholds
    """
    thresholds = {
        -999.0: (0, 0, 200),      # Deep blue (very low)
        -2.0: (0, 50, 255),       # Blue (low tide)
        -1.0: (0, 150, 255),      # Cyan (below mean)
        -0.3: (0, 255, 0),        # Green (at mean)
        0.3: (150, 255, 0),       # Yellow-green (slightly above)
        1.0: (255, 200, 0),       # Yellow (above mean)
        2.0: (255, 100, 0),       # Orange (high tide)
        3.0: (255, 0, 0),         # Red (very high)
        999.0: (255, 0, 0)        # Red (extreme)
    }
    return ColorMapper(thresholds)
