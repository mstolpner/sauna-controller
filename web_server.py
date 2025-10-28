import logging

from flask import Flask, render_template, jsonify, request, send_from_directory
from SaunaContext import SaunaContext
from ErrorManager import ErrorManager
from SaunaController import SaunaController
import threading
import socket
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global instances
_ctx: SaunaContext = None
_errorMgr: ErrorManager = None


def start_web_ui(ctx: SaunaContext, errorMgr: ErrorManager):
    global _ctx, _errorMgr
    _ctx = ctx
    _errorMgr = errorMgr
    log = logging.getLogger('werkzeug')
    log.disabled = True
    # Run web server
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)


def is_wifi_connected():
    # Check if WiFi/network is connected
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return True
    except OSError:
        return False


# Serve icon files
@app.route('/icons/<path:filename>')
def serve_icon(filename):
    icons_dir = os.path.join(BASE_DIR, 'icons')
    return send_from_directory(icons_dir, filename)


# Main screen
@app.route('/')
def index():
    return render_template('index.html')


# Fan configuration screen
@app.route('/fan')
def fan():
    return render_template('fan.html')


# Settings screen
@app.route('/settings')
def settings():
    return render_template('settings.html')


# WiFi screen
@app.route('/wifi')
def wifi():
    return render_template('wifi.html')


# Errors screen
@app.route('/errors')
def errors():
    return render_template('errors.html')


# API Endpoints
@app.route('/api/status')
def api_status():
    """Get current sauna status"""
    return jsonify({
        'sauna_on': _ctx.isSaunaOn(),
        'heater_on': _ctx.isHeaterOn(),
        'hot_room_temp_f': _ctx.getHotRoomTempF(),
        'hot_room_humidity': _ctx.getHotRoomHumidity(),
        'target_temp_f': _ctx.getHotRoomTargetTempF(),
        'wifi_connected': is_wifi_connected(),
        'has_errors': _errorMgr.hasAnyError() if _errorMgr else False
    })


@app.route('/api/fan/status')
def api_fan_status():
    """Get fan configuration"""
    return jsonify({
        'left_fan_on': _ctx.getLeftFanOnStatus(),
        'right_fan_on': _ctx.getRightFanOnStatus(),
        'fan_speed_pct': _ctx.getFanSpeedPct(),
        'running_time_after_sauna_off_hrs': _ctx.getFanRunningTimeAfterSaunaOffHrs()
    })


@app.route('/api/fan/update', methods=['POST'])
def api_fan_update():
    """Update fan configuration"""
    data = request.json
    if 'left_fan_on' in data:
        _ctx.setLeftFanOnStatus(data['left_fan_on'])
    if 'right_fan_on' in data:
        _ctx.setRightFanOnStatus(data['right_fan_on'])
    if 'fan_speed_pct' in data:
        _ctx.setFanSpeedPct(int(data['fan_speed_pct']))
    if 'running_time_after_sauna_off_hrs' in data:
        _ctx.setFanRunningTimeAfterSaunaOffHrs(float(data['running_time_after_sauna_off_hrs']))
    return jsonify({'success': True})


@app.route('/api/sauna/toggle', methods=['POST'])
def api_sauna_toggle():
    """Toggle sauna on/off"""
    _ctx.turnSaunaOnOff(not _ctx.isSaunaOn())
    return jsonify({'success': True, 'sauna_on': _ctx.isSaunaOn()})


@app.route('/api/temperature/set', methods=['POST'])
def api_temperature_set():
    """Set target temperature"""
    data = request.json
    if 'temp_f' in data:
        _ctx.setHotRoomTargetTempF(int(data['temp_f']))
    return jsonify({'success': True})


@app.route('/api/preset/set', methods=['POST'])
def api_preset_set():
    """Set temperature preset"""
    data = request.json
    preset = data.get('preset')
    if preset == 'medium':
        _ctx.setHotRoomTargetTempF(_ctx.getTargetTempPresetMedium())
    elif preset == 'high':
        _ctx.setHotRoomTargetTempF(_ctx.getTargetTempPresetHigh())
    return jsonify({'success': True, 'target_temp_f': _ctx.getHotRoomTargetTempF()})


@app.route('/api/settings/get')
def api_settings_get():
    """Get all settings"""
    return jsonify({
        'max_temp_f': _ctx.getHotRoomMaxTempF(),
        'preset_medium': _ctx.getTargetTempPresetMedium(),
        'preset_high': _ctx.getTargetTempPresetHigh(),
        'lower_threshold_f': _ctx.getLowerHotRoomTempThresholdF(),
        'upper_threshold_f': _ctx.getUpperHotRoomTempThresholdF(),
        'cooling_grace_period': _ctx.getCoolingGracePeriod(),
        'warmup_time': _ctx.getHeaterHealthWarmUpTime(),
        'cooldown_time': _ctx.getHeaterHealthCooldownTime(),
        'serial_port': _ctx.getRs485SerialPort(),
        'baud_rate': _ctx.getRs485SerialBaudRate(),
        'rs485_timeout': _ctx.getRs485SerialTimeout(),
        'rs485_retries': _ctx.getRs485SerialRetries(),
        'light_off_when_sauna_off': not _ctx.getHotRoomLightAlwaysOn(),
        'screen_width': _ctx.getScreenWidth(),
        'screen_height': _ctx.getScreenHeight(),
        'screen_rotation': _ctx.getScreenRotation()
    })


@app.route('/api/settings/update', methods=['POST'])
def api_settings_update():
    """Update settings"""
    data = request.json
    if 'max_temp_f' in data:
        _ctx.setHotRoomMaxTempF(int(data['max_temp_f']))
    if 'preset_medium' in data:
        _ctx.setTargetTempPresetMedium(int(data['preset_medium']))
    if 'preset_high' in data:
        _ctx.setTargetTempPresetHigh(int(data['preset_high']))
    if 'lower_threshold_f' in data:
        _ctx.setLowerHotRoomTempThresholdF(int(data['lower_threshold_f']))
    if 'upper_threshold_f' in data:
        _ctx.setUpperHotRoomTempThresholdF(int(data['upper_threshold_f']))
    if 'cooling_grace_period' in data:
        _ctx.setCoolingGracePeriod(int(data['cooling_grace_period']))
    if 'warmup_time' in data:
        _ctx.setLHeaterHealthWarmupTime(int(data['warmup_time']))
    if 'cooldown_time' in data:
        _ctx.setHeaterHealthCooldownTime(int(data['cooldown_time']))
    if 'serial_port' in data:
        _ctx.setRs485SerialPort(data['serial_port'])
    if 'baud_rate' in data:
        _ctx.setRs485SerialBaudRate(int(data['baud_rate']))
    if 'rs485_timeout' in data:
        _ctx.setRs485SerialTimeout(float(data['rs485_timeout']))
    if 'rs485_retries' in data:
        _ctx.setRs485SerialRetries(int(data['rs485_retries']))
    if 'light_off_when_sauna_off' in data:
        _ctx.setHotRoomLightAlwaysOn(not data['light_off_when_sauna_off'])
    return jsonify({'success': True})


@app.route('/api/errors/get')
def api_errors_get():
    """Get current errors"""
    if not _errorMgr:
        return jsonify({'errors': []})

    errors = []

    # Collect all error messages
    if _errorMgr._criticalErrorMessage:
        errors.append({'type': 'Critical Error', 'message': _errorMgr._criticalErrorMessage})

    if _errorMgr._relayModuleErrorMessage:
        errors.append({'type': 'Relay Module Error', 'message': _errorMgr._relayModuleErrorMessage})

    if _errorMgr._fanModuleErrorMessage:
        errors.append({'type': 'Fan Module Error', 'message': _errorMgr._fanModuleErrorMessage})

    if _errorMgr._sensorModuleErrorMessage:
        errors.append({'type': 'Sensor Module Error', 'message': _errorMgr._sensorModuleErrorMessage})

    if _errorMgr._modbusException:
        errors.append({'type': 'Modbus Error', 'message': str(_errorMgr._modbusException)})

    if _errorMgr._heaterErrorMessage:
        errors.append({'type': 'Heater Error', 'message': _errorMgr._heaterErrorMessage})

    if _errorMgr._fanErrorMessage:
        errors.append({'type': 'Fan Error', 'message': _errorMgr._fanErrorMessage})

    return jsonify({'errors': errors})
