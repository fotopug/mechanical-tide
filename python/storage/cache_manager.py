"""
Cache manager for Mechanical Tide Clock
Handles persistent storage of predictions, wave data, and datums
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class CacheManager:
    """Manage cached data for offline operation"""
    
    def __init__(self, data_dir=None):
        """
        Initialize cache manager
        
        Args:
            data_dir: Directory for cache files (defaults to data/)
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.predictions_file = self.data_dir / "predictions_cache.json"
        self.wave_file = self.data_dir / "wave_cache.json"
        self.datums_file = self.data_dir / "datums.json"
    
    def save_predictions(self, station_id: str, datum: str, predictions: List[Dict], 
                        duration_hours: int = 48):
        """
        Save tide predictions to cache
        
        Args:
            station_id: NOAA station ID
            datum: Datum used (e.g., 'MSL')
            predictions: List of prediction dicts with 'time' and 'water_level_ft'
            duration_hours: Cache duration in hours
        """
        cache_data = {
            'station_id': station_id,
            'datum': datum,
            'fetch_time': datetime.utcnow().isoformat() + 'Z',
            'expiry_time': (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat() + 'Z',
            'predictions': predictions
        }
        
        with open(self.predictions_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def load_predictions(self, check_expiry: bool = True) -> Optional[Dict]:
        """
        Load tide predictions from cache
        
        Args:
            check_expiry: Whether to check if cache is expired
        
        Returns:
            Cache data dict or None if not available/expired
        """
        if not self.predictions_file.exists():
            return None
        
        try:
            with open(self.predictions_file, 'r') as f:
                cache_data = json.load(f)
            
            if check_expiry:
                expiry_time = datetime.fromisoformat(cache_data['expiry_time'].replace('Z', '+00:00'))
                if datetime.utcnow() > expiry_time.replace(tzinfo=None):
                    return None
            
            return cache_data
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def save_wave_data(self, buoy_id: str, dominant_period: float, 
                       wave_height: Optional[float] = None, clamped_period: Optional[float] = None):
        """
        Save wave data to cache
        
        Args:
            buoy_id: NDBC buoy ID
            dominant_period: Dominant wave period in seconds
            wave_height: Wave height in feet (optional)
            clamped_period: Period after clamping to 2-8 seconds (optional)
        """
        cache_data = {
            'buoy_id': buoy_id,
            'fetch_time': datetime.utcnow().isoformat() + 'Z',
            'dominant_period_sec': dominant_period,
            'wave_height_ft': wave_height,
            'clamped_period_sec': clamped_period if clamped_period else dominant_period
        }
        
        with open(self.wave_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def load_wave_data(self) -> Optional[Dict]:
        """
        Load wave data from cache
        
        Returns:
            Wave data dict or None if not available
        """
        if not self.wave_file.exists():
            return None
        
        try:
            with open(self.wave_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def save_datums(self, station_id: str, datums: Dict[str, float]):
        """
        Save station datums to cache
        
        Args:
            station_id: NOAA station ID
            datums: Dict of datum names to values (e.g., {'MSL': 0.00, 'MLLW': -2.89})
        """
        cache_data = {
            'station_id': station_id,
            'fetch_time': datetime.utcnow().isoformat() + 'Z',
            'datums': datums
        }
        
        with open(self.datums_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def load_datums(self) -> Optional[Dict]:
        """
        Load station datums from cache
        
        Returns:
            Datums dict or None if not available
        """
        if not self.datums_file.exists():
            return None
        
        try:
            with open(self.datums_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def get_cached_datum(self, datum_name: str) -> Optional[float]:
        """
        Get specific datum value from cache
        
        Args:
            datum_name: Name of datum (e.g., 'MSL', 'MLLW')
        
        Returns:
            Datum value or None if not available
        """
        datums_cache = self.load_datums()
        if datums_cache and 'datums' in datums_cache:
            return datums_cache['datums'].get(datum_name)
        return None
    
    def is_predictions_expired(self) -> bool:
        """
        Check if predictions cache is expired
        
        Returns:
            True if expired or not available
        """
        cache_data = self.load_predictions(check_expiry=False)
        if not cache_data:
            return True
        
        try:
            expiry_time = datetime.fromisoformat(cache_data['expiry_time'].replace('Z', '+00:00'))
            return datetime.utcnow() > expiry_time.replace(tzinfo=None)
        except (KeyError, ValueError):
            return True
    
    def get_cache_age_hours(self) -> Optional[float]:
        """
        Get age of predictions cache in hours
        
        Returns:
            Hours since cache was created, or None if no cache
        """
        cache_data = self.load_predictions(check_expiry=False)
        if not cache_data:
            return None
        
        try:
            fetch_time = datetime.fromisoformat(cache_data['fetch_time'].replace('Z', '+00:00'))
            age = datetime.utcnow() - fetch_time.replace(tzinfo=None)
            return age.total_seconds() / 3600
        except (KeyError, ValueError):
            return None
