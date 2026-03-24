"""
Configuration loader for Mechanical Tide Clock
Loads and validates configuration from JSON file
"""

import json
import os
from pathlib import Path


class ConfigLoader:
    """Load and access configuration settings"""
    
    def __init__(self, config_path=None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to config.json file (defaults to config/config.json)
        """
        if config_path is None:
            # Default to config/config.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            # Try to use example config
            example_path = self.config_path.parent / "config.example.json"
            if example_path.exists():
                print(f"Warning: {self.config_path} not found, using {example_path}")
                self.config_path = example_path
            else:
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}\n"
                    f"Please create config.json from config.example.json"
                )
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get(self, *keys, default=None):
        """
        Get configuration value by nested keys
        
        Args:
            *keys: Nested keys to traverse (e.g., 'station', 'tide_station_id')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Example:
            config.get('station', 'tide_station_id')  # Returns '8452944'
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def __getitem__(self, key):
        """Allow dict-style access: config['station']"""
        return self.config[key]
    
    def __contains__(self, key):
        """Allow 'in' operator: 'station' in config"""
        return key in self.config


# Singleton instance
_config_instance = None

def get_config(config_path=None):
    """
    Get singleton configuration instance
    
    Args:
        config_path: Path to config file (only used on first call)
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance
