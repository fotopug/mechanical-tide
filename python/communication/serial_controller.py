"""
Serial communication controller
Manages USB serial communication with Circuit Playground Classic
"""

import serial
import serial.tools.list_ports
import time
from typing import Optional, Tuple
from ..utils.logger import get_logger


class SerialController:
    """Handle serial communication with Arduino"""
    
    def __init__(self, baud_rate: int = 115200, timeout: float = 2.0,
                 port_hints: list = None):
        """
        Initialize serial controller
        
        Args:
            baud_rate: Serial baud rate
            timeout: Read timeout in seconds
            port_hints: List of port name patterns to search for
        """
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.port_hints = port_hints or ["/dev/ttyACM", "COM", "/dev/cu.usbmodem"]
        self.serial_port = None
        self.logger = get_logger()
    
    def auto_detect_port(self) -> Optional[str]:
        """
        Auto-detect Circuit Playground serial port
        
        Returns:
            Port name if found, None otherwise
        """
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            port_name = port.device
            
            # Check if port name matches any hints
            for hint in self.port_hints:
                if hint in port_name:
                    self.logger.info(f"Found potential Circuit Playground port: {port_name}")
                    return port_name
        
        self.logger.warning("No Circuit Playground port found via auto-detection")
        return None
    
    def connect(self, port: Optional[str] = None) -> bool:
        """
        Connect to Circuit Playground
        
        Args:
            port: Serial port name (auto-detects if None)
        
        Returns:
            True if connected successfully
        """
        if port is None:
            port = self.auto_detect_port()
            if port is None:
                return False
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            
            # Wait for Arduino to reset after serial connection
            time.sleep(2.0)
            
            # Clear any startup messages
            self.serial_port.reset_input_buffer()
            
            self.logger.info(f"Connected to Circuit Playground on {port}")
            return True
        
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to {port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Circuit Playground"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("Disconnected from Circuit Playground")
    
    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self.serial_port is not None and self.serial_port.is_open
    
    def send_tide_command(self, position: float, r: int, g: int, b: int) -> bool:
        """
        Send TIDE command to Arduino
        
        Args:
            position: Tide position (0.0 - 9.999)
            r, g, b: RGB color values (0-255)
        
        Returns:
            True if command acknowledged
        """
        if not self.is_connected():
            self.logger.error("Not connected to Circuit Playground")
            return False
        
        # Validate inputs
        position = max(0.0, min(9.999, position))
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        
        command = f"TIDE:{position:.3f},{r},{g},{b}\n"
        
        try:
            self.serial_port.write(command.encode())
            response = self._read_response()
            
            if response == "OK":
                self.logger.debug(f"TIDE command sent: pos={position:.3f}, rgb=({r},{g},{b})")
                return True
            else:
                self.logger.warning(f"TIDE command failed: {response}")
                return False
        
        except serial.SerialException as e:
            self.logger.error(f"Serial error sending TIDE command: {e}")
            return False
    
    def send_wave_command(self, period: float) -> bool:
        """
        Send WAVE command to Arduino
        
        Args:
            period: Wave period in seconds (2.0 - 8.0)
        
        Returns:
            True if command acknowledged
        """
        if not self.is_connected():
            self.logger.error("Not connected to Circuit Playground")
            return False
        
        # Validate period
        period = max(2.0, min(8.0, period))
        
        command = f"WAVE:{period:.1f}\n"
        
        try:
            self.serial_port.write(command.encode())
            response = self._read_response()
            
            if response == "OK":
                self.logger.debug(f"WAVE command sent: period={period:.1f}s")
                return True
            else:
                self.logger.warning(f"WAVE command failed: {response}")
                return False
        
        except serial.SerialException as e:
            self.logger.error(f"Serial error sending WAVE command: {e}")
            return False
    
    def send_status_command(self, status: str) -> bool:
        """
        Send STATUS command to Arduino
        
        Args:
            status: Status type ('SUCCESS', 'FAIL', 'ERROR')
        
        Returns:
            True if command acknowledged
        """
        if not self.is_connected():
            self.logger.error("Not connected to Circuit Playground")
            return False
        
        if status not in ['SUCCESS', 'FAIL', 'ERROR']:
            self.logger.error(f"Invalid status: {status}")
            return False
        
        command = f"STATUS:{status}\n"
        
        try:
            self.serial_port.write(command.encode())
            response = self._read_response()
            
            if response == "OK":
                self.logger.debug(f"STATUS command sent: {status}")
                return True
            else:
                self.logger.warning(f"STATUS command failed: {response}")
                return False
        
        except serial.SerialException as e:
            self.logger.error(f"Serial error sending STATUS command: {e}")
            return False
    
    def _read_response(self) -> str:
        """
        Read response from Arduino
        
        Returns:
            Response string (e.g., 'OK', 'ERR:message')
        """
        try:
            # Read until newline or timeout
            response = self.serial_port.readline().decode().strip()
            
            # Filter out comment lines (start with #)
            while response.startswith('#'):
                response = self.serial_port.readline().decode().strip()
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error reading response: {e}")
            return "ERR:Read failed"
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Circuit Playground
        
        Returns:
            True if reconnected successfully
        """
        self.disconnect()
        time.sleep(1.0)
        return self.connect()
