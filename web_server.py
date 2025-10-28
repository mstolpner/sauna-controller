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
ctx = None
errorMgr = None
sc = None


def init_sauna():
    """Initialize sauna controller components"""
    global ctx, errorMgr, sc
    ctx = SaunaContext()
    errorMgr = ErrorManager()
    sc = SaunaController(ctx, errorMgr)
    # Run sauna controller in background thread
    threading.Thread(target=sc.run, daemon=True).start()


def is_wifi_connected():
    """Check if WiFi/network is connected"""
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
        'sauna_on': ctx.isSaunaOn(),
        'heater_on': ctx.isHeaterOn(),
        'hot_room_temp_f': ctx.getHotRoomTempF(),
        'hot_room_humidity': ctx.getHotRoomHumidity(),
        'target_temp_f': ctx.getHotRoomTargetTempF(),
        'wifi_connected': is_wifi_connected(),
        'has_errors': errorMgr.hasAnyError() if errorMgr else False
    })


@app.route('/api/fan/status')
def api_fan_status():
    """Get fan configuration"""
    return jsonify({
        'left_fan_on': ctx.getLeftFanOnStatus(),
        'right_fan_on': ctx.getRightFanOnStatus(),
        'fan_speed_pct': ctx.getFanSpeedPct(),
        'running_time_after_sauna_off_hrs': ctx.getFanRunningTimeAfterSaunaOffHrs()
    })


@app.route('/api/fan/update', methods=['POST'])
def api_fan_update():
    """Update fan configuration"""
    data = request.json
    if 'left_fan_on' in data:
        ctx.setLeftFanOnStatus(data['left_fan_on'])
    if 'right_fan_on' in data:
        ctx.setRightFanOnStatus(data['right_fan_on'])
    if 'fan_speed_pct' in data:
        ctx.setFanSpeedPct(int(data['fan_speed_pct']))
    if 'running_time_after_sauna_off_hrs' in data:
        ctx.setFanRunningTimeAfterSaunaOffHrs(float(data['running_time_after_sauna_off_hrs']))
    return jsonify({'success': True})


@app.route('/api/sauna/toggle', methods=['POST'])
def api_sauna_toggle():
    """Toggle sauna on/off"""
    ctx.turnSaunaOnOff(not ctx.isSaunaOn())
    return jsonify({'success': True, 'sauna_on': ctx.isSaunaOn()})


@app.route('/api/temperature/set', methods=['POST'])
def api_temperature_set():
    """Set target temperature"""
    data = request.json
    if 'temp_f' in data:
        ctx.setHotRoomTargetTempF(int(data['temp_f']))
    return jsonify({'success': True})


@app.route('/api/preset/set', methods=['POST'])
def api_preset_set():
    """Set temperature preset"""
    data = request.json
    preset = data.get('preset')
    if preset == 'medium':
        ctx.setHotRoomTargetTempF(ctx.getTargetTempPresetMedium())
    elif preset == 'high':
        ctx.setHotRoomTargetTempF(ctx.getTargetTempPresetHigh())
    return jsonify({'success': True, 'target_temp_f': ctx.getHotRoomTargetTempF()})


@app.route('/api/settings/get')
def api_settings_get():
    """Get all settings"""
    return jsonify({
        'max_temp_f': ctx.getHotRoomMaxTempF(),
        'preset_medium': ctx.getTargetTempPresetMedium(),
        'preset_high': ctx.getTargetTempPresetHigh(),
        'screen_width': ctx.getScreenWidth(),
        'screen_height': ctx.getScreenHeight(),
        'screen_rotation': ctx.getScreenRotation()
    })


@app.route('/api/errors/get')
def api_errors_get():
    """Get current errors"""
    if not errorMgr:
        return jsonify({'errors': []})

    errors = []

    # Collect all error messages
    if errorMgr._criticalErrorMessage:
        errors.append({'type': 'Critical Error', 'message': errorMgr._criticalErrorMessage})

    if errorMgr._relayModuleErrorMessage:
        errors.append({'type': 'Relay Module Error', 'message': errorMgr._relayModuleErrorMessage})

    if errorMgr._fanModuleErrorMessage:
        errors.append({'type': 'Fan Module Error', 'message': errorMgr._fanModuleErrorMessage})

    if errorMgr._sensorModuleErrorMessage:
        errors.append({'type': 'Sensor Module Error', 'message': errorMgr._sensorModuleErrorMessage})

    if errorMgr._modbusException:
        errors.append({'type': 'Modbus Error', 'message': str(errorMgr._modbusException)})

    if errorMgr._heaterErrorMessage:
        errors.append({'type': 'Heater Error', 'message': errorMgr._heaterErrorMessage})

    if errorMgr._fanErrorMessage:
        errors.append({'type': 'Fan Error', 'message': errorMgr._fanErrorMessage})

    return jsonify({'errors': errors})


if __name__ == '__main__':
    init_sauna()
    # Run on all interfaces, port 8080
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
