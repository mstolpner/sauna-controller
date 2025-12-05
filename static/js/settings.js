// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Switch between tabs
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });

    // Show the selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');

    // Add active class to the clicked button
    event.target.classList.add('active');
}

// Load settings from server
function loadSettings() {
    fetch('/api/settings/get')
        .then(response => response.json())
        .then(data => {
            // Temperature settings
            document.getElementById('max-temp').value = data.max_temp_f;
            document.getElementById('preset-medium').value = data.preset_medium;
            document.getElementById('preset-high').value = data.preset_high;
            document.getElementById('lower-threshold').value = data.lower_threshold_f;
            document.getElementById('upper-threshold').value = data.upper_threshold_f;
            document.getElementById('cooling-grace-period').value = data.cooling_grace_period;

            // Heater health check settings
            document.getElementById('warmup-time').value = data.warmup_time;
            document.getElementById('cooldown-time').value = data.cooldown_time;
            document.getElementById('max-safe-runtime').value = data.max_safe_runtime_min;

            // Heater cycle control settings
            document.getElementById('cycle-on-period').value = data.cycle_on_period_min;
            document.getElementById('cycle-off-period').value = data.cycle_off_period_min;
            document.getElementById('high-temp-mode').checked = data.high_temp_mode;
            document.getElementById('high-temp-threshold').value = data.high_temp_threshold_f;
            document.getElementById('high-temp-cycle-on-period').value = data.high_temp_cycle_on_period_min;
            document.getElementById('high-temp-cycle-off-period').value = data.high_temp_cycle_off_period_min;

            // Modbus settings
            document.getElementById('serial-port').value = data.serial_port;
            document.getElementById('baud-rate').value = data.baud_rate;
            document.getElementById('modbus-timeout').value = data.modbus_timeout;
            document.getElementById('modbus-retries').value = data.modbus_retries;

            // Modbus register addresses
            document.getElementById('temp-sensor-addr').value = data.temp_sensor_addr;
            document.getElementById('humidity-sensor-addr').value = data.humidity_sensor_addr;
            document.getElementById('heater-relay-coil-addr').value = data.heater_relay_coil_addr;
            document.getElementById('hot-room-light-coil-addr').value = data.hot_room_light_coil_addr;
            document.getElementById('right-fan-relay-coil-addr').value = data.right_fan_relay_coil_addr;
            document.getElementById('left-fan-relay-coil-addr').value = data.left_fan_relay_coil_addr;
            document.getElementById('fan-module-room-temp-addr').value = data.fan_module_room_temp_addr;
            document.getElementById('fan-status-addr').value = data.fan_status_addr;
            document.getElementById('fan-speed-addr').value = data.fan_speed_addr;
            document.getElementById('number-of-fans-addr').value = data.number_of_fans_addr;
            document.getElementById('fan-fault-status-addr').value = data.fan_fault_status_addr;
            document.getElementById('fan-module-governor-addr').value = data.fan_module_governor_addr;
            document.getElementById('fan-module-reset-governor-value').value = data.fan_module_reset_governor_value;

            // Light settings
            document.getElementById('light-auto-on-off').checked = data.light_auto_on_off;

            // Display settings
            document.getElementById('display-brightness').value = data.display_brightness;

            // System settings
            document.getElementById('cpu-temp-current').textContent = data.cpu_temp ? data.cpu_temp.toFixed(1) : '--';
            document.getElementById('cpu-temp-warn').value = data.cpu_temp_warn;
            document.getElementById('max-sauna-on-time').value = data.max_sauna_on_time_hrs;
            document.getElementById('log-level').value = data.log_level;
        })
        .catch(error => console.error('Error loading settings:', error));
}

// Save settings to server
function saveSettings() {
    const settings = {
        max_temp_f: parseInt(document.getElementById('max-temp').value),
        preset_medium: parseInt(document.getElementById('preset-medium').value),
        preset_high: parseInt(document.getElementById('preset-high').value),
        lower_threshold_f: parseInt(document.getElementById('lower-threshold').value),
        upper_threshold_f: parseInt(document.getElementById('upper-threshold').value),
        cooling_grace_period: parseInt(document.getElementById('cooling-grace-period').value),
        warmup_time: parseInt(document.getElementById('warmup-time').value),
        cooldown_time: parseInt(document.getElementById('cooldown-time').value),
        max_safe_runtime_min: parseInt(document.getElementById('max-safe-runtime').value),
        cycle_on_period_min: parseInt(document.getElementById('cycle-on-period').value),
        cycle_off_period_min: parseInt(document.getElementById('cycle-off-period').value),
        high_temp_mode: document.getElementById('high-temp-mode').checked,
        high_temp_threshold_f: parseInt(document.getElementById('high-temp-threshold').value),
        high_temp_cycle_on_period_min: parseInt(document.getElementById('high-temp-cycle-on-period').value),
        high_temp_cycle_off_period_min: parseInt(document.getElementById('high-temp-cycle-off-period').value),
        serial_port: document.getElementById('serial-port').value,
        baud_rate: parseInt(document.getElementById('baud-rate').value),
        modbus_timeout: parseFloat(document.getElementById('modbus-timeout').value),
        modbus_retries: parseInt(document.getElementById('modbus-retries').value),
        temp_sensor_addr: parseInt(document.getElementById('temp-sensor-addr').value),
        humidity_sensor_addr: parseInt(document.getElementById('humidity-sensor-addr').value),
        heater_relay_coil_addr: parseInt(document.getElementById('heater-relay-coil-addr').value),
        hot_room_light_coil_addr: parseInt(document.getElementById('hot-room-light-coil-addr').value),
        right_fan_relay_coil_addr: parseInt(document.getElementById('right-fan-relay-coil-addr').value),
        left_fan_relay_coil_addr: parseInt(document.getElementById('left-fan-relay-coil-addr').value),
        fan_module_room_temp_addr: parseInt(document.getElementById('fan-module-room-temp-addr').value),
        fan_status_addr: parseInt(document.getElementById('fan-status-addr').value),
        fan_speed_addr: parseInt(document.getElementById('fan-speed-addr').value),
        number_of_fans_addr: parseInt(document.getElementById('number-of-fans-addr').value),
        fan_fault_status_addr: parseInt(document.getElementById('fan-fault-status-addr').value),
        fan_module_governor_addr: parseInt(document.getElementById('fan-module-governor-addr').value),
        fan_module_reset_governor_value: parseInt(document.getElementById('fan-module-reset-governor-value').value),
        light_auto_on_off: document.getElementById('light-auto-on-off').checked,
        display_brightness: parseInt(document.getElementById('display-brightness').value),
        cpu_temp_warn: parseInt(document.getElementById('cpu-temp-warn').value),
        max_sauna_on_time_hrs: parseInt(document.getElementById('max-sauna-on-time').value),
        log_level: parseInt(document.getElementById('log-level').value)
    };

    fetch('/api/settings/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';
        }
    })
    .catch(error => console.error('Error saving settings:', error));
}

// Initialize
loadSettings();
