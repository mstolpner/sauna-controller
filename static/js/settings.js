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

            // RS485 settings
            document.getElementById('serial-port').value = data.serial_port;
            document.getElementById('baud-rate').value = data.baud_rate;
            document.getElementById('rs485-timeout').value = data.rs485_timeout;
            document.getElementById('rs485-retries').value = data.rs485_retries;

            // Light settings
            document.getElementById('light-off-when-sauna-off').checked = data.light_off_when_sauna_off;
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
        serial_port: document.getElementById('serial-port').value,
        baud_rate: parseInt(document.getElementById('baud-rate').value),
        rs485_timeout: parseFloat(document.getElementById('rs485-timeout').value),
        rs485_retries: parseInt(document.getElementById('rs485-retries').value),
        light_off_when_sauna_off: document.getElementById('light-off-when-sauna-off').checked
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
