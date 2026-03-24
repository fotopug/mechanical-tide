"""
NDBC buoy data client for wave information
Fetches wave period data from NOAA National Data Buoy Center
"""

import requests
from typing import Dict, Optional
from ..utils.logger import get_logger


class NDBCWavesClient:
    """Client for NDBC buoy data"""
    
    BASE_URL = "https://www.ndbc.noaa.gov/data/realtime2"
    
    def __init__(self, buoy_id: str):
        """
        Initialize NDBC waves client
        
        Args:
            buoy_id: NDBC buoy ID (e.g., '44028' for Buzzards Bay)
        """
        self.buoy_id = buoy_id
        self.logger = get_logger()
    
    def fetch_wave_data(self) -> Optional[Dict]:
        """
        Fetch latest wave data from buoy
        
        Returns:
            Dict with 'dominant_period_sec', 'wave_height_ft', 'time', or None if failed
        """
        url = f"{self.BASE_URL}/{self.buoy_id}.txt"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse NDBC text format
            lines = response.text.strip().split('\n')
            
            if len(lines) < 3:
                self.logger.warning(f"Insufficient data from buoy {self.buoy_id}")
                return None
            
            # Line 0: Column headers (units)
            # Line 1: Column names
            # Line 2+: Data rows
            
            header_line = lines[1].split()
            data_line = lines[2].split()
            
            if len(data_line) < len(header_line):
                self.logger.warning(f"Incomplete data row from buoy {self.buoy_id}")
                return None
            
            # Create dict mapping column names to values
            data = dict(zip(header_line, data_line))
            
            # Extract wave data
            # DPD = Dominant Wave Period (seconds)
            # WVHT = Wave Height (meters)
            # APD = Average Wave Period (seconds) - fallback
            
            dpd = data.get('DPD', 'MM')  # MM = Missing
            wvht = data.get('WVHT', 'MM')
            apd = data.get('APD', 'MM')
            
            # Try dominant period first, fall back to average period
            period_sec = None
            if dpd != 'MM':
                try:
                    period_sec = float(dpd)
                except ValueError:
                    pass
            
            if period_sec is None and apd != 'MM':
                try:
                    period_sec = float(apd)
                    self.logger.info("Using average wave period (dominant not available)")
                except ValueError:
                    pass
            
            if period_sec is None:
                self.logger.warning(f"No valid wave period from buoy {self.buoy_id}")
                return None
            
            # Wave height (optional)
            wave_height_ft = None
            if wvht != 'MM':
                try:
                    wave_height_m = float(wvht)
                    wave_height_ft = wave_height_m * 3.28084  # Convert meters to feet
                except ValueError:
                    pass
            
            # Parse timestamp
            year = data.get('#YY')
            month = data.get('MM')
            day = data.get('DD')
            hour = data.get('hh')
            minute = data.get('mm')
            
            time_str = None
            if all([year, month, day, hour, minute]):
                try:
                    time_str = f"{year}-{month}-{day} {hour}:{minute}"
                except Exception:
                    pass
            
            result = {
                'dominant_period_sec': period_sec,
                'wave_height_ft': wave_height_ft,
                'time': time_str,
                'buoy_id': self.buoy_id
            }
            
            self.logger.info(
                f"Fetched wave data from buoy {self.buoy_id}: "
                f"period={period_sec}s, height={wave_height_ft:.1f}ft" if wave_height_ft else
                f"period={period_sec}s"
            )
            
            return result
        
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch wave data from buoy {self.buoy_id}: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse wave data from buoy {self.buoy_id}: {e}")
            return None
    
    def validate_period(self, period_sec: float, min_sec: float = 1.0, 
                       max_sec: float = 30.0) -> bool:
        """
        Validate wave period is within reasonable range
        
        Args:
            period_sec: Wave period in seconds
            min_sec: Minimum valid period
            max_sec: Maximum valid period
        
        Returns:
            True if valid, False otherwise
        """
        return min_sec <= period_sec <= max_sec
