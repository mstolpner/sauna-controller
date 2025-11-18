import logging
import socket
import os
from functools import wraps
from datetime import timedelta

from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from SaunaContext import SaunaContext
from SaunaErrorMgr import SaunaErrorMgr


class SaunaWebUIServer:
    """Web UI server for sauna controller"""

    def __init__(self, ctx: SaunaContext, errorMgr: SaunaErrorMgr):
        self._ctx = ctx
        self._errorMgr = errorMgr
        self._app = Flask(__name__)
        self._app.secret_key = ctx.getSecretKey()

        # Session security configuration
        self._app.config['SESSION_PERMANENT'] = True
        self._app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
        self._app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
        self._app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
        self._app.config['SESSION_COOKIE_SECURE'] = False  # Set to True when using HTTPS

        # CSRF Protection
        self._app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire (session-based)
        self._csrf = CSRFProtect(self._app)

        self._base_dir = os.path.dirname(os.path.abspath(__file__))
        self._setup_routes()

    def _is_wifi_connected(self):
        """Check if WiFi/network is connected"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except OSError:
            return False

    def _login_required(self, f):
        """Decorator to require login for routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def _setup_routes(self):
        """Setup all Flask routes"""
        # Login route
        @self._app.route('/login', methods=['GET', 'POST'])
        def login():
            error = None
            if request.method == 'POST':
                password = request.form.get('password')
                if password == self._ctx.getWebPassword():
                    # Security: Regenerate session ID to prevent session fixation
                    session.clear()
                    session['logged_in'] = True
                    session.permanent = True
                    return redirect(url_for('index'))
                else:
                    error = 'Invalid password'
            return render_template('login.html', error=error)

        # Logout route
        @self._app.route('/logout')
        def logout():
            session.pop('logged_in', None)
            return redirect(url_for('login'))

        # Serve icon files
        @self._app.route('/icons/<path:filename>')
        @self._login_required
        def serve_icon(filename):
            # Security: Prevent path traversal attacks
            # Sanitize filename to remove directory traversal attempts
            filename = secure_filename(filename)

            # Additional check: ensure no path separators remain
            if os.path.sep in filename or (os.path.altsep and os.path.altsep in filename):
                return "Invalid filename", 400

            # Additional check: ensure filename doesn't start with dot (hidden files)
            if filename.startswith('.'):
                return "Invalid filename", 400

            icons_dir = os.path.join(self._base_dir, 'icons')
            return send_from_directory(icons_dir, filename)

        # Main screen
        @self._app.route('/')
        @self._login_required
        def index():
            return render_template('index.html')

        # Fan configuration screen
        @self._app.route('/fan')
        @self._login_required
        def fan():
            return render_template('fan.html')

        # Settings screen
        @self._app.route('/settings')
        @self._login_required
        def settings():
            return render_template('settings.html')

        # WiFi screen
        @self._app.route('/wifi')
        @self._login_required
        def wifi():
            return render_template('wifi.html')

        # Errors screen
        @self._app.route('/errors')
        @self._login_required
        def errors():
            return render_template('errors.html')

        # API Endpoints
        @self._app.route('/api/status')
        @self._login_required
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
                'has_errors': self._errorMgr.hasAnyError() if self._errorMgr else False,
                'heater_error': self._errorMgr._heaterErrorMessage if self._errorMgr else None
            })

        @self._app.route('/api/fan/status')
        @self._login_required
        def api_fan_status():
            """Get fan configuration"""
            return jsonify({
                'left_fan_on': self._ctx.isLeftFanEnabled(),
                'right_fan_on': self._ctx.isRightFanEnabled(),
                'fan_speed_pct': self._ctx.getFanSpeedPct(),
                'left_fan_rpm': self._ctx.getLeftFanRpm(),
                'right_fan_rpm': self._ctx.getRightFanRpm(),
                'running_time_after_sauna_off_hrs': self._ctx.getFanRunningTimeAfterSaunaOffHrs()
            })

        @self._app.route('/api/fan/update', methods=['POST'])
        @self._login_required
        def api_fan_update():
            """Update fan configuration"""
            data = request.json
            if 'left_fan_on' in data:
                self._ctx.setLeftFanEnabled(data['left_fan_on'])
            if 'right_fan_on' in data:
                self._ctx.setRightFanEnabled(data['right_fan_on'])
            if 'fan_speed_pct' in data:
                self._ctx.setFanSpeedPct(int(data['fan_speed_pct']))
            if 'running_time_after_sauna_off_hrs' in data:
                self._ctx.setFanRunningTimeAfterSaunaOffHrs(float(data['running_time_after_sauna_off_hrs']))
            return jsonify({'success': True})

        @self._app.route('/api/sauna/toggle', methods=['POST'])
        @self._login_required
        def api_sauna_toggle():
            """Toggle sauna on/off"""
            self._ctx.turnSaunaOnOff(not self._ctx.isSaunaOn())
            return jsonify({'success': True, 'sauna_on': self._ctx.isSaunaOn()})

        @self._app.route('/api/temperature/set', methods=['POST'])
        @self._login_required
        def api_temperature_set():
            """Set target temperature"""
            data = request.json
            if 'temp_f' in data:
                self._ctx.setHotRoomTargetTempF(int(data['temp_f']))
            return jsonify({'success': True})

        @self._app.route('/api/preset/set', methods=['POST'])
        @self._login_required
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
        @self._login_required
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
                'cycle_on_period_min': self._ctx.getHeaterCycleOnPeriodMin(),
                'cycle_off_period_min': self._ctx.getHeaterCycleOffPeriodMin(),
                'serial_port': self._ctx.getModbusSerialPort(),
                'baud_rate': self._ctx.getModbusSerialBaudRate(),
                'modbus_timeout': self._ctx.getModbusSerialTimeout(),
                'modbus_retries': self._ctx.getModbusSerialRetries(),
                'temp_sensor_addr': self._ctx.getTempSensorAddr(),
                'humidity_sensor_addr': self._ctx.getHumiditySensorAddr(),
                'heater_relay_coil_addr': self._ctx.getHeaterRelayCoilAddr(),
                'hot_room_light_coil_addr': self._ctx.getHotRoomLightCoilAddr(),
                'right_fan_relay_coil_addr': self._ctx.getRightFanRelayCoilAddr(),
                'left_fan_relay_coil_addr': self._ctx.getLeftFanRelayCoilAddr(),
                'fan_module_room_temp_addr': self._ctx.getFanModuleRoomTempAddr(),
                'fan_status_addr': self._ctx.getFanStatusAddr(),
                'fan_speed_addr': self._ctx.getFanSpeedAddr(),
                'number_of_fans_addr': self._ctx.getNumberOfFansAddr(),
                'fan_fault_status_addr': self._ctx.getFanFaultStatusAddr(),
                'fan_module_governor_addr': self._ctx.getFanModuleGovernorAddr(),
                'fan_module_reset_governor_value': self._ctx.getFanModuleResetGovernorValue(),
                'light_off_when_sauna_off': not self._ctx.getHotRoomLightAlwaysOn(),
                'screen_width': self._ctx.getScreenWidth(),
                'screen_height': self._ctx.getScreenHeight(),
                'screen_rotation': self._ctx.getScreenRotation(),
                'cpu_temp_warn': self._ctx.getCpuWarnTempC(),
                'log_level': self._ctx.getLogLevel(),
                'max_sauna_on_time_hrs': self._ctx.getMaxSaunaOnTimeHrs()
            })

        @self._app.route('/api/settings/update', methods=['POST'])
        @self._login_required
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
            if 'cycle_on_period_min' in data:
                self._ctx.setHeaterCycleOnPeriodMin(int(data['cycle_on_period_min']))
            if 'cycle_off_period_min' in data:
                self._ctx.setHeaterCycleOffPeriodMin(int(data['cycle_off_period_min']))
            if 'serial_port' in data:
                self._ctx.setModbusSerialPort(data['serial_port'])
            if 'baud_rate' in data:
                self._ctx.setModbusSerialBaudRate(int(data['baud_rate']))
            if 'modbus_timeout' in data:
                self._ctx.setModbusSerialTimeout(float(data['modbus_timeout']))
            if 'modbus_retries' in data:
                self._ctx.setModbusSerialRetries(int(data['modbus_retries']))
            if 'temp_sensor_addr' in data:
                self._ctx.setTempSensorAddr(int(data['temp_sensor_addr']))
            if 'humidity_sensor_addr' in data:
                self._ctx.setHumiditySensorAddr(int(data['humidity_sensor_addr']))
            if 'heater_relay_coil_addr' in data:
                self._ctx.setHeaterRelayCoilAddr(int(data['heater_relay_coil_addr']))
            if 'hot_room_light_coil_addr' in data:
                self._ctx.setHotRoomLightCoilAddr(int(data['hot_room_light_coil_addr']))
            if 'right_fan_relay_coil_addr' in data:
                self._ctx.setRightFanRelayCoilAddr(int(data['right_fan_relay_coil_addr']))
            if 'left_fan_relay_coil_addr' in data:
                self._ctx.setLeftFanRelayCoilAddr(int(data['left_fan_relay_coil_addr']))
            if 'fan_module_room_temp_addr' in data:
                self._ctx.setFanModuleRoomTempAddr(int(data['fan_module_room_temp_addr']))
            if 'fan_status_addr' in data:
                self._ctx.setFanStatusAddr(int(data['fan_status_addr']))
            if 'fan_speed_addr' in data:
                self._ctx.setFanSpeedAddr(int(data['fan_speed_addr']))
            if 'number_of_fans_addr' in data:
                self._ctx.setNumberOfFansAddr(int(data['number_of_fans_addr']))
            if 'fan_fault_status_addr' in data:
                self._ctx.setFanFaultStatusAddr(int(data['fan_fault_status_addr']))
            if 'fan_module_governor_addr' in data:
                self._ctx.setFanModuleGovernorAddr(int(data['fan_module_governor_addr']))
            if 'fan_module_reset_governor_value' in data:
                self._ctx.setFanModuleResetGovernorValue(int(data['fan_module_reset_governor_value']))
            if 'light_off_when_sauna_off' in data:
                self._ctx.setHotRoomLightAlwaysOn(not data['light_off_when_sauna_off'])
            if 'cpu_temp_warn' in data:
                self._ctx.setCpuWarnTempC(int(data['cpu_temp_warn']))
            if 'log_level' in data:
                self._ctx.setLogLevel(int(data['log_level']))
            if 'max_sauna_on_time_hrs' in data:
                self._ctx.setMaxSaunaOnTimeHrs(int(data['max_sauna_on_time_hrs']))
            return jsonify({'success': True})

        @self._app.route('/api/errors/get')
        @self._login_required
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

            if self._errorMgr._systemHealthErrorMessage:
                errors.append({'type': 'System Health Error', 'message': self._errorMgr._systemHealthErrorMessage})

            return jsonify({'errors': errors})

        @self._app.route('/api/errors/clear', methods=['POST'])
        @self._login_required
        def api_errors_clear():
            """Clear all errors"""
            if self._errorMgr:
                self._errorMgr.clearAllErrors()
            return jsonify({'success': True})

    def run(self):
        host = self._ctx.getHttpHost()
        port = self._ctx.getHttpPort()
        """Run the web server"""
        # Disable werkzeug logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        # Start Flask app
        self._app.run(host=host, port=port, debug=False, use_reloader=False)

