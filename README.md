# Mechanical Tide Clock

A real-time tide visualization system using NOAA data and Circuit Playground Classic.

## Features

- **Real-time tide display** - Updates every 6 minutes with NOAA water level data
- **Clock-style visualization** - 10 NeoPixels show current position in 12.4-hour tidal cycle
- **Heat-map colors** - Blue (low) → Green (mean) → Yellow/Red (high)
- **Wave-synchronized breathing** - LED brightness pulses at ocean wave frequency (2-8 seconds)
- **Multi-LED gradient** - Smooth glow effect with interpolation between LEDs
- **Offline resilience** - Caches 48 hours of predictions for operation without internet
- **Standalone operation** - Runs on Raspberry Pi Zero for autonomous deployment

## Hardware Requirements

- **Circuit Playground Classic** (Adafruit #3000)
- **Raspberry Pi Zero W** (or any computer with Python 3.7+)
- **USB cable** (Micro-B)
- **5V power supply** (2A recommended)

## Data Sources

- **Tide data**: NOAA Station 8452944 (Conimicut Light, RI)
- **Wave data**: NDBC Buoy 44028 (Buzzards Bay, 15 miles from station)

## Quick Start

### 1. Arduino Setup

1. Open Arduino IDE
2. Install "Adafruit NeoPixel" library (Tools → Manage Libraries)
3. Open `arduino/tide_clock/tide_clock.ino`
4. Select Board: **Arduino Leonardo** (Circuit Playground uses ATmega32u4)
5. Select Port: Your Circuit Playground port
6. Upload sketch

### 2. Python Setup (Local Testing)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r python/requirements.txt

# Create config file
cp config/config.example.json config/config.json
# Edit config.json if needed (defaults should work)

# Run application
python python/main.py
```

### 3. Raspberry Pi Deployment

See detailed deployment guide below.

## Project Structure

```
mechanical-tide/
├── arduino/
│   └── tide_clock/          # Circuit Playground firmware
│       ├── tide_clock.ino   # Main sketch
│       ├── config.h         # Constants
│       ├── led_renderer.h   # LED display functions
│       └── serial_handler.h # Serial command parsing
├── python/
│   ├── main.py             # Main application
│   ├── data_sources/       # NOAA & NDBC API clients
│   ├── processors/         # Tide calculations & color mapping
│   ├── communication/      # Serial communication
│   ├── storage/            # Cache management
│   └── utils/              # Configuration & logging
├── config/
│   └── config.example.json # Configuration template
├── data/                   # Runtime data cache
├── logs/                   # Application logs
└── deploy/
    └── tide-clock.service  # Systemd service file
```

## LED Display Behavior

### Normal Operation
- **Position**: LEDs around circle indicate current tide position
  - LED 0 (top) = High tide
  - LED 5 (bottom) = Low tide
- **Color**: Heat-map based on water level relative to Mean Sea Level (MSL)
- **Breathing**: Brightness pulses at wave frequency (2-8 seconds)
- **Gradient**: Multi-LED glow effect for smooth visualization

### Status Indicators

| Behavior | Meaning |
|----------|---------|
| Aqua pulsing (all LEDs) | Startup - waiting for data |
| Double-blink green | First data fetch successful |
| Slow red blink (1 Hz) | Cannot fetch data (offline mode) |
| Single LED blinking red (LED 9) | Intermittent errors / stale cache |
| Normal tide display | All systems operational |

## Serial Communication Protocol

The Arduino receives commands via USB serial at 115200 baud:

```
TIDE:<position>,<r>,<g>,<b>  # Set tide position & color
WAVE:<period>                # Set breathing period (seconds)
STATUS:<state>               # Trigger status animation (SUCCESS/FAIL/ERROR)
```

Responses: `OK` or `ERR:<message>`

## Raspberry Pi Deployment

### Initial Setup

1. **Flash Raspberry Pi OS Lite** to SD card (using Raspberry Pi Imager)
2. **Enable SSH and WiFi** before first boot
3. Boot and SSH in: `ssh pi@tide-clock.local`

### Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3 python3-pip python3-venv git

# Clone or copy project
git clone <your-repo> mechanical-tide
# OR: scp -r mechanical-tide pi@tide-clock.local:~/

cd mechanical-tide
```

### Setup Application

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r python/requirements.txt

# Create directories
mkdir -p data logs

# Create config file
cp config/config.example.json config/config.json
# Edit if needed: nano config/config.json
```

### Install as Service

```bash
# Copy service file
sudo cp deploy/tide-clock.service /etc/systemd/system/

# If using different username or path, edit service file:
# sudo nano /etc/systemd/system/tide-clock.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tide-clock.service
sudo systemctl start tide-clock.service

# Check status
sudo systemctl status tide-clock.service

# View logs
tail -f logs/tide_clock.log
```

### Service Management

```bash
# Start/stop/restart
sudo systemctl start tide-clock.service
sudo systemctl stop tide-clock.service
sudo systemctl restart tide-clock.service

# View logs
journalctl -u tide-clock.service -f

# Check if running
sudo systemctl is-active tide-clock.service
```

## Configuration

Edit `config/config.json` to customize:

- **Station IDs**: Change tide station or wave buoy
- **Update intervals**: Adjust fetch frequencies
- **Colors**: Customize heat-map thresholds
- **Breathing**: Adjust min/max wave periods
- **Serial**: Change baud rate or port hints

## Troubleshooting

### Circuit Playground Not Detected

```bash
# Check USB connection
ls /dev/tty*  # Look for ttyACM0 or similar

# Check permissions (Linux)
sudo usermod -a -G dialout $USER
# Log out and back in
```

### NOAA API Not Responding

```bash
# Test API manually
curl "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=8452944&product=water_level&datum=MSL&time_zone=gmt&units=english&format=json&date=latest"

# Check station status
# Visit: https://tidesandcurrents.noaa.gov/stationhome.html?id=8452944
```

### Service Won't Start

```bash
# Check logs
journalctl -u tide-clock.service -n 50

# Common issues:
# 1. Wrong Python path in service file
# 2. Missing serial permissions: sudo usermod -a -G dialout pi
# 3. Missing config file: cp config/config.example.json config/config.json
```

### LEDs Flickering

- Use quality USB cable
- Ensure adequate power supply (5V 2A minimum)
- Check Arduino loop has proper delay (20ms)

## Development

### Running Tests

```bash
# Test individual modules
python -m python.data_sources.noaa_tides
python -m python.processors.color_mapper

# Test with Arduino connected
python python/main.py
```

### Manual Serial Testing

Open Arduino Serial Monitor (115200 baud) and send commands:

```
TIDE:3.5,0,255,0      # Green at position 3.5
WAVE:6.0              # 6-second breathing
STATUS:SUCCESS        # Trigger success animation
```

## License

This project is open source. Use and modify as you wish!

## Acknowledgments

- NOAA CO-OPS for tide and current data
- NDBC for wave data
- Adafruit for Circuit Playground Classic

## Author

Built with care for observing the rhythm of the ocean. 🌊
