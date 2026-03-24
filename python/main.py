#!/usr/bin/env python3
"""
Mechanical Tide Clock - Main Application
Real-time tide visualization using NOAA data and Circuit Playground Classic
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_loader import get_config
from utils.logger import setup_logger
from storage.cache_manager import CacheManager
from data_sources.noaa_tides import NOAATidesClient
from data_sources.ndbc_waves import NDBCWavesClient
from processors.tide_calculator import TideCalculator
from processors.color_mapper import create_default_color_mapper
from processors.wave_processor import WaveProcessor
from processors.gradient_builder import GradientBuilder
from communication.serial_controller import SerialController


class TideClockApp:
    """Main tide clock application"""
    
    def __init__(self):
        """Initialize application"""
        # Load configuration
        self.config = get_config()
        
        # Setup logger
        log_config = self.config.get('logging', default={})
        self.logger = setup_logger('tide_clock', log_config)
        
        self.logger.info("=" * 60)
        self.logger.info("Mechanical Tide Clock Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.cache_manager = CacheManager()
        
        station_id = self.config.get('station', 'tide_station_id')
        self.noaa_client = NOAATidesClient(station_id)
        
        buoy_id = self.config.get('station', 'wave_buoy_id')
        self.ndbc_client = NDBCWavesClient(buoy_id)
        
        num_leds = self.config.get('display', 'num_leds', default=10)
        self.tide_calculator = TideCalculator(num_leds)
        
        self.color_mapper = create_default_color_mapper()
        
        wave_config = self.config.get('breathing', default={})
        self.wave_processor = WaveProcessor(
            min_period=wave_config.get('period_min_seconds', 2.0),
            max_period=wave_config.get('period_max_seconds', 8.0),
            default_period=wave_config.get('default_period_seconds', 7.0)
        )
        
        self.gradient_builder = GradientBuilder(num_leds)
        
        serial_config = self.config.get('serial', default={})
        self.serial = SerialController(
            baud_rate=serial_config.get('baud_rate', 115200),
            timeout=serial_config.get('timeout_seconds', 2.0),
            port_hints=serial_config.get('port_hints', [])
        )
        
        # State tracking
        self.last_tide_update = None
        self.last_wave_update = None
        self.last_predictions_refresh = None
        self.first_success = False
        self.error_count = 0
        self.consecutive_errors = 0
        
        # Get MSL datum
        self.msl_datum = self._get_msl_datum()
    
    def _get_msl_datum(self) -> float:
        """Get MSL datum value"""
        # Try cache first
        cached_msl = self.cache_manager.get_cached_datum('MSL')
        if cached_msl is not None:
            self.logger.info(f"Using cached MSL datum: {cached_msl} ft")
            return cached_msl
        
        # Fetch from NOAA
        self.logger.info("Fetching MSL datum from NOAA...")
        datums = self.noaa_client.fetch_datums()
        
        if datums and 'MSL' in datums:
            msl = datums['MSL']
            self.cache_manager.save_datums(
                self.config.get('station', 'tide_station_id'),
                datums
            )
            self.logger.info(f"MSL datum: {msl} ft")
            return msl
        
        # Fallback to config or 0.0
        fallback = self.config.get('station', 'msl_datum_ft', default=0.0)
        self.logger.warning(f"Could not fetch MSL datum, using fallback: {fallback} ft")
        return fallback
    
    def connect_to_arduino(self) -> bool:
        """Connect to Circuit Playground"""
        self.logger.info("Connecting to Circuit Playground...")
        
        if self.serial.connect():
            self.logger.info("Successfully connected to Circuit Playground")
            return True
        else:
            self.logger.error("Failed to connect to Circuit Playground")
            return False
    
    def update_tide_display(self) -> bool:
        """Update tide data and send to Arduino"""
        try:
            # Fetch current water level
            self.logger.info("Fetching current water level...")
            water_level_data = self.noaa_client.fetch_water_level(datum='MSL')
            
            using_cache = False
            current_water_level = None
            
            if water_level_data:
                current_water_level = water_level_data['water_level_ft']
                self.logger.info(f"Current water level: {current_water_level:.2f} ft MSL")
                self.consecutive_errors = 0
            else:
                # Fall back to cached predictions
                self.logger.warning("Failed to fetch water level, using cached predictions")
                using_cache = True
                predictions_cache = self.cache_manager.load_predictions()
                
                if predictions_cache and 'predictions' in predictions_cache:
                    predictions = predictions_cache['predictions']
                    # Convert time strings back to datetime
                    for pred in predictions:
                        if isinstance(pred['time'], str):
                            pred['time'] = datetime.fromisoformat(pred['time'].replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    current_water_level = self.tide_calculator.interpolate_water_level(
                        datetime.utcnow(), predictions
                    )
                    
                    if current_water_level:
                        self.logger.info(f"Interpolated water level: {current_water_level:.2f} ft MSL (from cache)")
                    else:
                        self.logger.error("Could not interpolate water level from cache")
                        self.consecutive_errors += 1
                        return False
                else:
                    self.logger.error("No cached predictions available")
                    self.consecutive_errors += 1
                    return False
            
            # Get predictions for position calculation
            predictions_cache = self.cache_manager.load_predictions()
            if not predictions_cache or 'predictions' not in predictions_cache:
                self.logger.warning("No predictions in cache, fetching...")
                self.refresh_predictions()
                predictions_cache = self.cache_manager.load_predictions()
            
            if predictions_cache and 'predictions' in predictions_cache:
                predictions = predictions_cache['predictions']
                
                # Convert time strings to datetime if needed
                for pred in predictions:
                    if isinstance(pred['time'], str):
                        pred['time'] = datetime.fromisoformat(pred['time'].replace('Z', '+00:00')).replace(tzinfo=None)
                
                # Calculate tide position
                position = self.tide_calculator.calculate_position(
                    datetime.utcnow(), predictions
                )
                
                if position is not None:
                    # Calculate color based on water level relative to MSL
                    height_relative_to_msl = current_water_level
                    r, g, b = self.color_mapper.height_to_rgb(height_relative_to_msl)
                    
                    self.logger.info(
                        f"Tide position: {position:.2f}, "
                        f"Height: {height_relative_to_msl:+.2f} ft MSL, "
                        f"Color: RGB({r},{g},{b}) - {self.color_mapper.get_color_description(height_relative_to_msl)}"
                    )
                    
                    # Send to Arduino
                    if self.serial.send_tide_command(position, r, g, b):
                        self.last_tide_update = datetime.now()
                        
                        # Send status indicator if using cache
                        if using_cache:
                            cache_age = self.cache_manager.get_cache_age_hours()
                            stale_threshold = self.config.get('update_intervals', 'stale_data_threshold_hours', default=4)
                            
                            if cache_age and cache_age > stale_threshold:
                                self.serial.send_status_command('ERROR')
                                self.logger.warning(f"Cache is {cache_age:.1f} hours old (stale)")
                        
                        return True
                    else:
                        self.logger.error("Failed to send TIDE command")
                        return False
                else:
                    self.logger.error("Could not calculate tide position")
                    return False
            else:
                self.logger.error("No predictions available")
                return False
        
        except Exception as e:
            self.logger.error(f"Error updating tide display: {e}", exc_info=True)
            self.consecutive_errors += 1
            return False
    
    def update_wave_breathing(self) -> bool:
        """Update wave data and send to Arduino"""
        try:
            self.logger.info("Fetching wave data...")
            wave_data = self.ndbc_client.fetch_wave_data()
            
            if wave_data and 'dominant_period_sec' in wave_data:
                period = wave_data['dominant_period_sec']
                clamped_period = self.wave_processor.clamp_period(period)
                
                # Cache the wave data
                self.cache_manager.save_wave_data(
                    self.config.get('station', 'wave_buoy_id'),
                    period,
                    wave_data.get('wave_height_ft'),
                    clamped_period
                )
                
                # Send to Arduino
                if self.serial.send_wave_command(clamped_period):
                    self.last_wave_update = datetime.now()
                    self.logger.info(f"Wave breathing updated: period={clamped_period:.1f}s")
                    return True
                else:
                    self.logger.error("Failed to send WAVE command")
                    return False
            else:
                # Use cached wave data
                self.logger.warning("Failed to fetch wave data, using cached value")
                cached_wave = self.cache_manager.load_wave_data()
                
                if cached_wave and 'clamped_period_sec' in cached_wave:
                    period = cached_wave['clamped_period_sec']
                    
                    if self.serial.send_wave_command(period):
                        self.last_wave_update = datetime.now()
                        self.logger.info(f"Wave breathing updated (cached): period={period:.1f}s")
                        return True
                else:
                    self.logger.warning("No cached wave data, using default")
                    default_period = self.config.get('breathing', 'default_period_seconds', default=7.0)
                    
                    if self.serial.send_wave_command(default_period):
                        self.last_wave_update = datetime.now()
                        return True
                    return False
        
        except Exception as e:
            self.logger.error(f"Error updating wave breathing: {e}", exc_info=True)
            return False
    
    def refresh_predictions(self) -> bool:
        """Refresh tide predictions cache"""
        try:
            self.logger.info("Refreshing tide predictions...")
            hours = self.config.get('fallback', 'cache_duration_hours', default=48)
            
            predictions = self.noaa_client.fetch_predictions(hours=hours, datum='MSL')
            
            if predictions:
                # Convert datetime to ISO string for JSON serialization
                for pred in predictions:
                    if isinstance(pred['time'], datetime):
                        pred['time'] = pred['time'].isoformat() + 'Z'
                
                self.cache_manager.save_predictions(
                    self.config.get('station', 'tide_station_id'),
                    'MSL',
                    predictions,
                    hours
                )
                
                self.last_predictions_refresh = datetime.now()
                self.logger.info(f"Predictions refreshed: {len(predictions)} data points")
                
                # Signal success on first refresh
                if not self.first_success:
                    self.serial.send_status_command('SUCCESS')
                    self.first_success = True
                
                return True
            else:
                self.logger.error("Failed to fetch predictions")
                return False
        
        except Exception as e:
            self.logger.error(f"Error refreshing predictions: {e}", exc_info=True)
            return False
    
    def should_update_tide(self) -> bool:
        """Check if tide data should be updated"""
        if self.last_tide_update is None:
            return True
        
        interval_minutes = self.config.get('update_intervals', 'tide_observation_minutes', default=6)
        elapsed = (datetime.now() - self.last_tide_update).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def should_update_wave(self) -> bool:
        """Check if wave data should be updated"""
        if self.last_wave_update is None:
            return True
        
        interval_minutes = self.config.get('update_intervals', 'wave_data_minutes', default=60)
        elapsed = (datetime.now() - self.last_wave_update).total_seconds() / 60
        return elapsed >= interval_minutes
    
    def should_refresh_predictions(self) -> bool:
        """Check if predictions should be refreshed"""
        if self.last_predictions_refresh is None:
            return True
        
        interval_hours = self.config.get('update_intervals', 'predictions_refresh_hours', default=24)
        elapsed = (datetime.now() - self.last_predictions_refresh).total_seconds() / 3600
        return elapsed >= interval_hours
    
    def run(self):
        """Main application loop"""
        # Connect to Arduino
        if not self.connect_to_arduino():
            self.logger.error("Cannot start without Arduino connection")
            self.serial.send_status_command('FAIL')
            return 1
        
        # Initial data fetch
        self.logger.info("Performing initial data fetch...")
        
        # Refresh predictions first (needed for tide calculation)
        if not self.refresh_predictions():
            self.logger.warning("Initial predictions fetch failed, checking cache...")
            if not self.cache_manager.load_predictions():
                self.logger.error("No predictions available (fresh or cached)")
                self.serial.send_status_command('FAIL')
                return 1
        
        # Initial tide update
        if not self.update_tide_display():
            self.logger.warning("Initial tide update failed")
        
        # Initial wave update
        if not self.update_wave_breathing():
            self.logger.warning("Initial wave update failed")
        
        self.logger.info("Entering main loop...")
        
        # Main loop
        try:
            while True:
                # Check if we should update tide
                if self.should_update_tide():
                    success = self.update_tide_display()
                    if not success and self.consecutive_errors >= 3:
                        self.logger.error("Multiple consecutive errors, attempting Arduino reconnect...")
                        if not self.serial.reconnect():
                            self.logger.error("Failed to reconnect to Arduino")
                            break
                        self.consecutive_errors = 0
                
                # Check if we should update wave
                if self.should_update_wave():
                    self.update_wave_breathing()
                
                # Check if we should refresh predictions
                if self.should_refresh_predictions():
                    self.refresh_predictions()
                
                # Sleep for a bit
                time.sleep(10)
        
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            self.logger.info("Shutting down...")
            self.serial.disconnect()
            self.logger.info("Mechanical Tide Clock stopped")
        
        return 0


def main():
    """Entry point"""
    app = TideClockApp()
    return app.run()


if __name__ == '__main__':
    sys.exit(main())
