# Sauna Controller Web Server

This is a web-based interface for the Sauna Controller application with similar functionality to the Kivy UI.

## Features

- **Main Screen**: Real-time temperature and humidity display, clock, sauna on/off control, temperature presets, and adjustable target temperature
- **Fan Configuration**: Control left/right fans, adjust fan speed, and set fan running time after sauna shutdown
- **Settings**: Configure maximum temperature and temperature presets
- **WiFi Status**: View WiFi connection status
- **Error Display**: View system errors

## Installation

1. Install Flask if not already installed:
```bash
pip install flask
```

## Running the Server

1. Start the web server:
```bash
python SaunaWebUIServer.py
```

2. Open your web browser and navigate to:
```
http://localhost:8080
```

Or from another device on the same network:
```
http://<raspberry-pi-ip>:8080
```

## API Endpoints

### Status
- `GET /api/status` - Get current sauna status (temperature, humidity, heater state, etc.)

### Fan Control
- `GET /api/fan/status` - Get fan configuration
- `POST /api/fan/update` - Update fan settings
  ```json
  {
    "left_fan_on": true,
    "right_fan_on": true,
    "fan_speed_pct": 100,
    "running_time_after_sauna_off_hrs": 0.5
  }
  ```

### Sauna Control
- `POST /api/sauna/toggle` - Toggle sauna on/off

### Temperature
- `POST /api/temperature/set` - Set target temperature
  ```json
  {"temp_f": 190}
  ```
- `POST /api/preset/set` - Set temperature preset
  ```json
  {"preset": "medium"}  // or "high"
  ```

### Settings
- `GET /api/settings/get` - Get all settings
- `POST /api/settings/update` - Update settings
  ```json
  {
    "max_temp_f": 240,
    "preset_medium": 180,
    "preset_high": 200,
    "lower_threshold_f": 5,
    "upper_threshold_f": 0,
    "cooling_grace_period": 60,
    "warmup_time": 300,
    "cooldown_time": 1200,
    "max_safe_runtime_min": 240,
    "cycle_on_period_min": 30,
    "cycle_off_period_min": 15,
    "serial_port": "/dev/ttyAMA0",
    "baud_rate": 9600,
    "modbus_timeout": 0.3,
    "modbus_retries": 3,
    "light_off_when_sauna_off": true
  }
  ```

### Errors
- `GET /api/errors/get` - Get current errors

## UI Features

### Main Screen
- Click on temperature to toggle between Fahrenheit and Celsius
- Use slider to adjust target temperature
- Click preset buttons (High/Medium) to set temperature presets
- Click sauna button to toggle sauna on/off
- Real-time updates every 2 seconds

### Fan Screen
- Check/uncheck boxes to enable/disable left and right fans
- Adjust fan speed (0-100%, increments of 5)
- Set fan running time after sauna off (0-12 hours, increments of 0.5)
- Click "Ok" to save settings and return to main screen

### Settings Screen
- **Temperature Settings**: Max temperature, presets, heater thresholds, cooling grace period
- **Heater Health Check Settings**: Warmup and cooldown times
- **Modbus Communication Settings**: Serial port, baud rate, timeout, retries
- **Hot Room Light Settings**: Control light behavior when sauna is off
- Click "Save" to apply changes or "Cancel" to return without saving

## Styling

The web interface uses a dark theme matching the original Kivy UI:
- Deep dark grey background (#1a1a1a)
- Orange temperature display (#ff8000)
- Blue humidity display (#80ccff)
- Green-yellow target temperature (#d9ff66)

## Notes

- The server runs on port 8080 by default
- The SaunaController runs in a background thread
- Status updates occur automatically every 2 seconds on the main screen
- All settings are persisted to sauna.ini via SaunaContext
