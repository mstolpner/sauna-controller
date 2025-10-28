import logging
import socket
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
from SaunaContext import SaunaContext
from ErrorManager import ErrorManager


class WebServer:
    """Web UI server for sauna controller"""

    def __init__(self, ctx: SaunaContext, errorMgr: ErrorManager):
        self.ctx = ctx
        self.errorMgr = errorMgr
        self.app = Flask(__name__)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self._setup_routes()

    def _is_wifi_connected(self):
        """Check if WiFi/network is connected"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except OSError:
            return False

    def _setup_routes(self):
        """Setup all Flask routes"""
        # Serve icon files
        @self.app.route('/icons/<path:filename>')
        def serve_icon(filename):
            icons_dir = os.path.join(self.base_dir, 'icons')
            return send_from_directory(icons_dir, filename)

        # Main screen
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # Fan configuration screen
        @self.app.route('/fan')
        def fan():
            return render_template('fan.html')

        # Settings screen
        @self.app.route('/settings')
        def settings():
            return render_template('settings.html')

        # WiFi screen
        @self.app.route('/wifi')
        def wifi():
            return render_template('wifi.html')

        # Errors screen
        @self.app.route('/errors')
        def errors():
            return render_template('errors.html')

        # API Endpoints
        @self.app.route('/api/status')
        def api_status():
            """Get current sauna status"""
            return jsonify({
                'sauna_on': self.ctx.isSaunaOn(),
                'heater_on': self.ctx.isHeaterOn(),
                'hot_room_temp_f': self.ctx.getHotRoomTempF(),
                'hot_room_humidity': self.ctx.getHotRoomHumidity(),
                'target_temp_f': self.ctx.getHotRoomTargetTempF(),
                'wifi_connected': self._is_wifi_connected(),
                'has_errors': self.errorMgr.hasAnyError() if self.errorMgr else False
            })

        @self.app.route('/api/fan/status')
        def api_fan_status():
            """Get fan configuration"""
            return jsonify({
                'left_fan_on': self.ctx.getLeftFanOnStatus(),
                'right_fan_on': self.ctx.getRightFanOnStatus(),
                'fan_speed_pct': self.ctx.getFanSpeedPct(),
                'running_time_after_sauna_off_hrs': self.ctx.getFanRunningTimeAfterSaunaOffHrs()
            })

        @self.app.route('/api/fan/update', methods=['POST'])
        def api_fan_update():
            """Update fan configuration"""
            data = request.json
            if 'left_fan_on' in data:
                self.ctx.setLeftFanOnStatus(data['left_fan_on'])
            if 'right_fan_on' in data:
                self.ctx.setRightFanOnStatus(data['right_fan_on'])
            if 'fan_speed_pct' in data:
                self.ctx.setFanSpeedPct(int(data['fan_speed_pct']))
            if 'running_time_after_sauna_off_hrs' in data:
                self.ctx.setFanRunningTimeAfterSaunaOffHrs(float(data['running_time_after_sauna_off_hrs']))
            return jsonify({'success': True})

        @self.app.route('/api/sauna/toggle', methods=['POST'])
        def api_sauna_toggle():
            """Toggle sauna on/off"""
            self.ctx.turnSaunaOnOff(not self.ctx.isSaunaOn())
            return jsonify({'success': True, 'sauna_on': self.ctx.isSaunaOn()})

        @self.app.route('/api/temperature/set', methods=['POST'])
        def api_temperature_set():
            """Set target temperature"""
            data = request.json
            if 'temp_f' in data:
                self.ctx.setHotRoomTargetTempF(int(data['temp_f']))
            return jsonify({'success': True})

        @self.app.route('/api/preset/set', methods=['POST'])
        def api_preset_set():
            """Set temperature preset"""
            data = request.json
            preset = data.get('preset')
            if preset == 'medium':
                self.ctx.setHotRoomTargetTempF(self.ctx.getTargetTempPresetMedium())
            elif preset == 'high':
                self.ctx.setHotRoomTargetTempF(self.ctx.getTargetTempPresetHigh())
            return jsonify({'success': True, 'target_temp_f': self.ctx.getHotRoomTargetTempF()})

        @self.app.route('/api/settings/get')
        def api_settings_get():
            """Get all settings"""
            return jsonify({
                'max_temp_f': self.ctx.getHotRoomMaxTempF(),
                'preset_medium': self.ctx.getTargetTempPresetMedium(),
                'preset_high': self.ctx.getTargetTempPresetHigh(),
                'lower_threshold_f': self.ctx.getLowerHotRoomTempThresholdF(),
                'upper_threshold_f': self.ctx.getUpperHotRoomTempThresholdF(),
                'cooling_grace_period': self.ctx.getCoolingGracePeriod(),
                'warmup_time': self.ctx.getHeaterHealthWarmUpTime(),
                'cooldown_time': self.ctx.getHeaterHealthCooldownTime(),
                'serial_port': self.ctx.getRs485SerialPort(),
                'baud_rate': self.ctx.getRs485SerialBaudRate(),
                'rs485_timeout': self.ctx.getRs485SerialTimeout(),
                'rs485_retries': self.ctx.getRs485SerialRetries(),
                'light_off_when_sauna_off': not self.ctx.getHotRoomLightAlwaysOn(),
                'screen_width': self.ctx.getScreenWidth(),
                'screen_height': self.ctx.getScreenHeight(),
                'screen_rotation': self.ctx.getScreenRotation()
            })

        @self.app.route('/api/settings/update', methods=['POST'])
        def api_settings_update():
            """Update settings"""
            data = request.json
            if 'max_temp_f' in data:
                self.ctx.setHotRoomMaxTempF(int(data['max_temp_f']))
            if 'preset_medium' in data:
                self.ctx.setTargetTempPresetMedium(int(data['preset_medium']))
            if 'preset_high' in data:
                self.ctx.setTargetTempPresetHigh(int(data['preset_high']))
            if 'lower_threshold_f' in data:
                self.ctx.setLowerHotRoomTempThresholdF(int(data['lower_threshold_f']))
            if 'upper_threshold_f' in data:
                self.ctx.setUpperHotRoomTempThresholdF(int(data['upper_threshold_f']))
            if 'cooling_grace_period' in data:
                self.ctx.setCoolingGracePeriod(int(data['cooling_grace_period']))
            if 'warmup_time' in data:
                self.ctx.setLHeaterHealthWarmupTime(int(data['warmup_time']))
            if 'cooldown_time' in data:
                self.ctx.setHeaterHealthCooldownTime(int(data['cooldown_time']))
            if 'serial_port' in data:
                self.ctx.setRs485SerialPort(data['serial_port'])
            if 'baud_rate' in data:
                self.ctx.setRs485SerialBaudRate(int(data['baud_rate']))
            if 'rs485_timeout' in data:
                self.ctx.setRs485SerialTimeout(float(data['rs485_timeout']))
            if 'rs485_retries' in data:
                self.ctx.setRs485SerialRetries(int(data['rs485_retries']))
            if 'light_off_when_sauna_off' in data:
                self.ctx.setHotRoomLightAlwaysOn(not data['light_off_when_sauna_off'])
            return jsonify({'success': True})

        @self.app.route('/api/errors/get')
        def api_errors_get():
            """Get current errors"""
            if not self.errorMgr:
                return jsonify({'errors': []})

            errors = []

            # Collect all error messages
            if self.errorMgr._criticalErrorMessage:
                errors.append({'type': 'Critical Error', 'message': self.errorMgr._criticalErrorMessage})

            if self.errorMgr._relayModuleErrorMessage:
                errors.append({'type': 'Relay Module Error', 'message': self.errorMgr._relayModuleErrorMessage})

            if self.errorMgr._fanModuleErrorMessage:
                errors.append({'type': 'Fan Module Error', 'message': self.errorMgr._fanModuleErrorMessage})

            if self.errorMgr._sensorModuleErrorMessage:
                errors.append({'type': 'Sensor Module Error', 'message': self.errorMgr._sensorModuleErrorMessage})

            if self.errorMgr._modbusException:
                errors.append({'type': 'Modbus Error', 'message': str(self.errorMgr._modbusException)})

            if self.errorMgr._heaterErrorMessage:
                errors.append({'type': 'Heater Error', 'message': self.errorMgr._heaterErrorMessage})

            if self.errorMgr._fanErrorMessage:
                errors.append({'type': 'Fan Error', 'message': self.errorMgr._fanErrorMessage})

            return jsonify({'errors': errors})

    def run(self, host='0.0.0.0', port=8080):
        """Run the web server"""
        # Disable werkzeug logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        # Start Flask app
        self.app.run(host=host, port=port, debug=False, use_reloader=False)


# Legacy function for backward compatibility
def start_web_ui(ctx: SaunaContext, errorMgr: ErrorManager):
    """Start web UI (legacy function for backward compatibility)"""
    server = WebServer(ctx, errorMgr)
    server.run()
