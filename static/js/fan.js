let fanSpeed = 100;
let fanRuntime = 0.5;

// Load current fan settings
function loadFanSettings() {
    fetch('/api/fan/status')
        .then(response => response.json())
        .then(data => {
            // Set checkboxes
            document.getElementById('left-fan').checked = data.left_fan_on;
            document.getElementById('right-fan').checked = data.right_fan_on;

            // Set fan speed
            fanSpeed = data.fan_speed_pct;
            document.getElementById('fan-speed-slider').value = fanSpeed;
            document.getElementById('fan-speed-value').textContent = `${fanSpeed}%`;

            // Set fan runtime
            fanRuntime = data.running_time_after_sauna_off_hrs;
            document.getElementById('fan-runtime-slider').value = fanRuntime;
            document.getElementById('fan-runtime-value').textContent = `${fanRuntime.toFixed(2)} hrs`;
        })
        .catch(error => console.error('Error loading fan settings:', error));
}

// Update fan speed display
function updateFanSpeed(value) {
    fanSpeed = parseInt(value);
    document.getElementById('fan-speed-value').textContent = `${fanSpeed}%`;
}

// Update fan runtime display
function updateFanRuntime(value) {
    fanRuntime = parseFloat(value);
    document.getElementById('fan-runtime-value').textContent = `${fanRuntime.toFixed(2)} hrs`;
}

// Update fan status when checkboxes change
function updateFanStatus() {
    // This is called on checkbox change, but we'll save on OK button
}

// Save fan settings and return to main screen
function saveFanSettings() {
    const leftFan = document.getElementById('left-fan').checked;
    const rightFan = document.getElementById('right-fan').checked;

    fetch('/api/fan/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            left_fan_on: leftFan,
            right_fan_on: rightFan,
            fan_speed_pct: fanSpeed,
            running_time_after_sauna_off_hrs: fanRuntime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/';
        }
    })
    .catch(error => console.error('Error saving fan settings:', error));
}

// Initialize
loadFanSettings();
