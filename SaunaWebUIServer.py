import logging
import socket
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
from SaunaContext import SaunaContext
from ErrorManager import ErrorManager


class SaunaWebUIServer:
    """Web UI server for sauna controller"""

    def __init__(self, ctx: SaunaContext, errorMgr: ErrorManager):
        self._ctx = ctx
        self._errorMgr = errorMgr
        self._app = Flask(__name__)
        self._base_dir = os.path.dirname(os.path.abspath(__file__))
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
        @self._app.route('/icons/<path:filename>')
        def serve_icon(filename):
            icons_dir = os.path.join(self._base_dir, 'icons')
            return send_from_directory(icons_dir, filename)

        # Main screen
        @self._app.route('/')
        def index():
            return render_template('index.html')

        # Fan configuration screen
        @self._app.route('/fan')
        def fan():
            return render_template('fan.html')

        # Settings screen
        @self._app.route('/settings')
        def settings():
            return render_template('settings.html')

        # WiFi screen
        @self._app.route('/wifi')
        def wifi():
            return render_template('wifi.html')

        # Errors screen
        @self._app.route('/errors')
        def errors():
            return render_template('errors.html')

        # API Endpoints
        @self._app.route('/api/status')
        def api_status():
            """Get current sauna status"""
            return jsonify({
                'sauna_on': self._ctx.isSaunaOn(),
                'heater_on': self._ctx.isHeaterOn(),
                'light_on': self._ctx.isHotRoomLightOn(),
                'hot_room_temp_f': self._ctx.getHotRoomTempF(),
                'hot_room_humidity': self._ctx.getHotRoomHumidity(),
                'target_temp_f': self._ctx.getHotRoomTargetTempF(),
                'wifi_connected': self._is_wifi_connected(),
                'has_errors': self._errorMgr.hasAnyError() if self._errorMgr else False
            })

        @self._app.route('/api/fan/status')
        def api_fan_status():
            """Get fan configuration"""
            return jsonify({
                'left_fan_on': self._ctx.getLeftFanOnStatus(),
                'right_fan_on': self._ctx.getRightFanOnStatus(),
                'fan_speed_pct': self._ctx.getFanSpeedPct(),
                'left_fan_rpm': self._ctx.getLeftFanRpm(),
                'right_fan_rpm': self._ctx.getRightFanRpm(),
                'running_time_after_sauna_off_hrs': self._ctx.getFanRunningTimeAfterSaunaOffHrs()
            })

        @self._app.route('/api/fan/update', methods=['POST'])
        def api_fan_update():
            """Update fan configuration"""
            data = request.json
            if 'left_fan_on' in data:
                self._ctx.setLeftFanOnStatus(data['left_fan_on'])
            if 'right_fan_on' in data:
                self._ctx.setRightFanOnStatus(data['right_fan_on'])
            if 'fan_speed_pct' in data:
                self._ctx.setFanSpeedPct(int(data['fan_speed_pct']))
            if 'running_time_after_sauna_off_hrs' in data:
                self._ctx.setFanRunningTimeAfterSaunaOffHrs(float(data['running_time_after_sauna_off_hrs']))
            return jsonify({'success': True})

        @self._app.route('/api/sauna/toggle', methods=['POST'])
        def api_sauna_toggle():
            """Toggle sauna on/off"""
            self._ctx.turnSaunaOnOff(not self._ctx.isSaunaOn())
            return jsonify({'success': True, 'sauna_on': self._ctx.isSaunaOn()})

        @self._app.route('/api/temperature/set', methods=['POST'])
        def api_temperature_set():
            """Set target temperature"""
            data = request.json
            if 'temp_f' in data:
                self._ctx.setHotRoomTargetTempF(int(data['temp_f']))
            return jsonify({'success': True})

        @self._app.route('/api/preset/set', methods=['POST'])
        def api_preset_set():
            """Set temperature preset"""
            data = request.json
            preset = data.get('preset')
            if preset == 'medium':
                self._ctx.setHotRoomTargetTempF(self._ctx.getTargetTempPresetMedium())
            elif preset == 'high':
                self._ctx.setHotRoomTargetTempF(self._ctx.getTargetTempPresetHigh())
            return jsonify({'success': True, 'target_temp_f': self._ctx.getHotRoomTargetTempF()})

        @self._app.route('/api/settings/get')
        def api_settings_get():
            """Get all settings"""
            return jsonify({
                'max_temp_f': self._ctx.getHotRoomMaxTempF(),
                'preset_medium': self._ctx.getTargetTempPresetMedium(),
                'preset_high': self._ctx.getTargetTempPresetHigh(),
                'lower_threshold_f': self._ctx.getLowerHotRoomTempThresholdF(),
                'upper_threshold_f': self._ctx.getUpperHotRoomTempThresholdF(),
                'cooling_grace_period': self._ctx.getCoolingGracePeriodMin(),
                'warmup_time': self._ctx.getHeaterHealthWarmUpTimeMin(),
                'cooldown_time': self._ctx.getHeaterHealthCooldownTimeMin(),
                'max_safe_runtime_min': self._ctx.getHeaterMaxSafeRuntimeMin(),
                'serial_port': self._ctx.getRs485SerialPort(),
                'baud_rate': self._ctx.getRs485SerialBaudRate(),
                'rs485_timeout': self._ctx.getRs485SerialTimeout(),
                'rs485_retries': self._ctx.getRs485SerialRetries(),
                'light_off_when_sauna_off': not self._ctx.getHotRoomLightAlwaysOn(),
                'screen_width': self._ctx.getScreenWidth(),
                'screen_height': self._ctx.getScreenHeight(),
                'screen_rotation': self._ctx.getScreenRotation()
            })

        @self._app.route('/api/settings/update', methods=['POST'])
        def api_settings_update():
            """Update settings"""
            data = request.json
            if 'max_temp_f' in data:
                self._ctx.setHotRoomMaxTempF(int(data['max_temp_f']))
            if 'preset_medium' in data:
                self._ctx.setTargetTempPresetMedium(int(data['preset_medium']))
            if 'preset_high' in data:
                self._ctx.setTargetTempPresetHigh(int(data['preset_high']))
            if 'lower_threshold_f' in data:
                self._ctx.setLowerHotRoomTempThresholdF(int(data['lower_threshold_f']))
            if 'upper_threshold_f' in data:
                self._ctx.setUpperHotRoomTempThresholdF(int(data['upper_threshold_f']))
            if 'cooling_grace_period' in data:
                self._ctx.setCoolingGracePeriodMin(int(data['cooling_grace_period']))
            if 'warmup_time' in data:
                self._ctx.setHeaterHealthWarmupTimeMin(int(data['warmup_time']))
            if 'cooldown_time' in data:
                self._ctx.setHeaterHealthCooldownTimeMin(int(data['cooldown_time']))
            if 'max_safe_runtime_min' in data:
                self._ctx.setHeaterMaxSafeRuntimeMin(int(data['max_safe_runtime_min']))
            if 'serial_port' in data:
                self._ctx.setRs485SerialPort(data['serial_port'])
            if 'baud_rate' in data:
                self._ctx.setRs485SerialBaudRate(int(data['baud_rate']))
            if 'rs485_timeout' in data:
                self._ctx.setRs485SerialTimeout(float(data['rs485_timeout']))
            if 'rs485_retries' in data:
                self._ctx.setRs485SerialRetries(int(data['rs485_retries']))
            if 'light_off_when_sauna_off' in data:
                self._ctx.setHotRoomLightAlwaysOn(not data['light_off_when_sauna_off'])
            return jsonify({'success': True})

        @self._app.route('/api/errors/get')
        def api_errors_get():
            """Get current errors"""
            if not self._errorMgr:
                return jsonify({'errors': []})

            errors = []

            # Collect all error messages
            if self._errorMgr._criticalErrorMessage:
                errors.append({'type': 'Critical Error', 'message': self._errorMgr._criticalErrorMessage})

            if self._errorMgr._relayModuleErrorMessage:
                errors.append({'type': 'Relay Module Error', 'message': self._errorMgr._relayModuleErrorMessage})

            if self._errorMgr._fanModuleErrorMessage:
                errors.append({'type': 'Fan Module Error', 'message': self._errorMgr._fanModuleErrorMessage})

            if self._errorMgr._sensorModuleErrorMessage:
                errors.append({'type': 'Sensor Module Error', 'message': self._errorMgr._sensorModuleErrorMessage})

            if self._errorMgr._modbusException:
                errors.append({'type': 'Modbus Error', 'message': str(self._errorMgr._modbusException)})

            if self._errorMgr._heaterErrorMessage:
                errors.append({'type': 'Heater Error', 'message': self._errorMgr._heaterErrorMessage})

            if self._errorMgr._fanErrorMessage:
                errors.append({'type': 'Fan Error', 'message': self._errorMgr._fanErrorMessage})

            return jsonify({'errors': errors})

    def run(self):
        host = self._ctx.getHttpHost()
        port = self._ctx.getHttpPort()
        """Run the web server"""
        # Disable werkzeug logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        # Start Flask app
        self._app.run(host=host, port=port, debug=False, use_reloader=False)

