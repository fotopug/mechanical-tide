"""
Multi-LED gradient builder
Calculates LED intensities for smooth gradient effect
"""

from typing import List


class GradientBuilder:
    """Build multi-LED gradient distributions"""
    
    def __init__(self, num_leds: int = 10, neighbor_intensity: float = 0.15, 
                 far_intensity: float = 0.10):
        """
        Initialize gradient builder
        
        Args:
            num_leds: Number of LEDs in ring
            neighbor_intensity: Intensity for adjacent neighbor
            far_intensity: Intensity for far neighbor
        """
        self.num_leds = num_leds
        self.neighbor_intensity = neighbor_intensity
        self.far_intensity = far_intensity
    
    def calculate_intensities(self, position: float) -> List[float]:
        """
        Calculate LED intensities for gradient effect
        
        Args:
            position: Floating-point LED position (e.g., 3.7)
        
        Returns:
            List of intensities (0.0-1.0) for each LED
        """
        primary_led = int(position) % self.num_leds
        secondary_led = (primary_led + 1) % self.num_leds
        fraction = position - int(position)
        
        # Initialize all to zero
        intensities = [0.0] * self.num_leds
        
        # Primary LED (closest to position)
        intensities[primary_led] = 1.0
        
        # Secondary LED (interpolation)
        intensities[secondary_led] = fraction
        
        # Neighbors for glow effect
        neighbor_before = (primary_led - 1) % self.num_leds
        neighbor_after = (secondary_led + 1) % self.num_leds
        
        intensities[neighbor_before] = self.neighbor_intensity
        intensities[neighbor_after] = self.far_intensity
        
        return intensities
