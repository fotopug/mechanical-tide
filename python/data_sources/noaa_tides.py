"""
NOAA CO-OPS API client for tide data
Fetches water levels, predictions, and datums from NOAA Tides & Currents
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..utils.logger import get_logger


class NOAATidesClient:
    """Client for NOAA CO-OPS API"""
    
    BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    METADATA_BASE_URL = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi"
    
    def __init__(self, station_id: str, application_name: str = "MechanicalTideClock"):
        """
        Initialize NOAA tides client
        
        Args:
            station_id: 7-character NOAA station ID (e.g., '8452944')
            application_name: Application identifier for NOAA logs
        """
        self.station_id = station_id
        self.application_name = application_name
        self.logger = get_logger()
    
    def fetch_water_level(self, datum: str = "MSL") -> Optional[Dict]:
        """
        Fetch latest water level observation
        
        Args:
            datum: Datum to use (MSL, MLLW, etc.)
        
        Returns:
            Dict with 'time' (datetime) and 'water_level_ft' (float), or None if failed
        """
        params = {
            'station': self.station_id,
            'product': 'water_level',
            'datum': datum,
            'time_zone': 'gmt',
            'units': 'english',
            'format': 'json',
            'date': 'latest',
            'application': self.application_name
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                obs = data['data'][0]
                
                # Validate water level
                water_level = self._validate_water_level(obs.get('v'))
                if water_level is None:
                    self.logger.warning(f"Invalid water level value: {obs.get('v')}")
                    return None
                
                # Parse time
                time_str = obs.get('t')
                obs_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                
                return {
                    'time': obs_time,
                    'water_level_ft': water_level
                }
            else:
                self.logger.warning("No water level data in NOAA response")
                return None
        
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch water level: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse water level response: {e}")
            return None
    
    def fetch_predictions(self, hours: int = 48, datum: str = "MSL", 
                         interval: int = 6) -> Optional[List[Dict]]:
        """
        Fetch tide predictions
        
        Args:
            hours: Hours of predictions to fetch (default 48)
            datum: Datum to use (MSL, MLLW, etc.)
            interval: Interval in minutes (6, 60, etc.)
        
        Returns:
            List of dicts with 'time' (datetime) and 'water_level_ft' (float), or None if failed
        """
        # Calculate date range
        begin_date = datetime.utcnow()
        end_date = begin_date + timedelta(hours=hours)
        
        params = {
            'station': self.station_id,
            'product': 'predictions',
            'datum': datum,
            'begin_date': begin_date.strftime('%Y%m%d %H:%M'),
            'end_date': end_date.strftime('%Y%m%d %H:%M'),
            'time_zone': 'gmt',
            'units': 'english',
            'interval': str(interval),
            'format': 'json',
            'application': self.application_name
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'predictions' in data:
                predictions = []
                for pred in data['predictions']:
                    water_level = self._validate_water_level(pred.get('v'))
                    if water_level is None:
                        continue
                    
                    time_str = pred.get('t')
                    pred_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                    
                    predictions.append({
                        'time': pred_time,
                        'water_level_ft': water_level
                    })
                
                self.logger.info(f"Fetched {len(predictions)} tide predictions")
                return predictions
            else:
                self.logger.warning("No predictions data in NOAA response")
                return None
        
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch predictions: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse predictions response: {e}")
            return None
    
    def fetch_datums(self) -> Optional[Dict[str, float]]:
        """
        Fetch station datums (MSL, MLLW, etc.)
        
        Returns:
            Dict mapping datum names to values in feet, or None if failed
        """
        url = f"{self.METADATA_BASE_URL}/stations/{self.station_id}/datums.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'datums' in data:
                datums = {}
                for datum in data['datums']:
                    name = datum.get('name')
                    value = datum.get('value')
                    
                    if name and value is not None:
                        try:
                            datums[name] = float(value)
                        except ValueError:
                            continue
                
                self.logger.info(f"Fetched {len(datums)} datums for station {self.station_id}")
                return datums
            else:
                self.logger.warning("No datums data in NOAA response")
                return None
        
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch datums: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to parse datums response: {e}")
            return None
    
    def _validate_water_level(self, value_str: Optional[str]) -> Optional[float]:
        """
        Validate and convert water level value
        
        Args:
            value_str: Water level as string
        
        Returns:
            Float value if valid, None otherwise
        """
        if not value_str:
            return None
        
        try:
            value = float(value_str)
            
            # Sanity check: Conimicut Light range is approximately -4 to +8 ft relative to MSL
            # Allow some buffer for extreme events
            if -10.0 < value < 15.0:
                return value
            else:
                self.logger.warning(f"Water level {value} ft outside expected range")
                return None
        except (ValueError, TypeError):
            return None
