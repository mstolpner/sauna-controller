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

            // Modbus settings
            document.getElementById('serial-port').value = data.serial_port;
            document.getElementById('baud-rate').value = data.baud_rate;
            document.getElementById('modbus-timeout').value = data.modbus_timeout;
            document.getElementById('modbus-retries').value = data.modbus_retries;

            // Light settings
            document.getElementById('light-off-when-sauna-off').checked = data.light_off_when_sauna_off;

            // System settings
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
        serial_port: document.getElementById('serial-port').value,
        baud_rate: parseInt(document.getElementById('baud-rate').value),
        modbus_timeout: parseFloat(document.getElementById('modbus-timeout').value),
        modbus_retries: parseInt(document.getElementById('modbus-retries').value),
        light_off_when_sauna_off: document.getElementById('light-off-when-sauna-off').checked,
        cpu_temp_warn: parseInt(document.getElementById('cpu-temp-warn').value),
        max_sauna_on_time_hrs: parseInt(document.getElementById('max-sauna-on-time').value),
        log_level: parseInt(document.getElementById('log-level').value)
    };

    fetch('/api/settings/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
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
