let fanSpeed = 100;
let fanRuntime = 0.5;
let leftFanEnabled = false;
let rightFanEnabled = false;
let leftFanHealthy = true;
let rightFanHealthy = true;

// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Get appropriate fan icon based on state
function getFanIcon(enabled, healthy) {
    if (!healthy) {
        return '/icons/fan_red.png';
    } else if (enabled) {
        return '/icons/fan_green.png';
    } else {
        return '/icons/fan_grey.png';
    }
}

// Load current fan settings
function loadFanSettings() {
    fetch('/api/fan/status')
        .then(response => response.json())
        .then(data => {
            // Set fan states
            leftFanEnabled = data.left_fan_on;
            rightFanEnabled = data.right_fan_on;
            leftFanHealthy = data.left_fan_healthy;
            rightFanHealthy = data.right_fan_healthy;

            // Update fan icons
            document.getElementById('left-fan-icon').src = getFanIcon(leftFanEnabled, leftFanHealthy);
            document.getElementById('right-fan-icon').src = getFanIcon(rightFanEnabled, rightFanHealthy);

            // Set fan speed
            fanSpeed = data.fan_speed_pct;
            document.getElementById('fan-speed-slider').value = fanSpeed;
            document.getElementById('fan-speed-value').textContent = `${fanSpeed}%`;

            // Set fan RPM displays
            document.getElementById('left-fan-rpm').textContent = `${data.left_fan_rpm} RPM`;
            document.getElementById('right-fan-rpm').textContent = `${data.right_fan_rpm} RPM`;

            // Set fan runtime
            fanRuntime = data.running_time_after_sauna_off_hrs;
            document.getElementById('fan-runtime-slider').value = fanRuntime;
            document.getElementById('fan-runtime-value').textContent = `${fanRuntime.toFixed(2)} hrs`;

        })
        .catch(error => console.error('Error loading fan settings:', error));
}

// Update fan speed display and context
function updateFanSpeed(value) {
    fanSpeed = parseInt(value);
    document.getElementById('fan-speed-value').textContent = `${fanSpeed}%`;

    // Update context immediately
    fetch('/api/fan/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            fan_speed_pct: fanSpeed
        })
    })
    .catch(error => console.error('Error updating fan speed:', error));
}

// Update fan runtime display
function updateFanRuntime(value) {
    fanRuntime = parseFloat(value);
    document.getElementById('fan-runtime-value').textContent = `${fanRuntime.toFixed(2)} hrs`;
}

// Toggle left fan
function toggleLeftFan() {
    leftFanEnabled = !leftFanEnabled;
    document.getElementById('left-fan-icon').src = getFanIcon(leftFanEnabled, leftFanHealthy);

    // Update on server
    fetch('/api/fan/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            left_fan_on: leftFanEnabled
        })
    })
    .catch(error => console.error('Error updating left fan:', error));
}

// Toggle right fan
function toggleRightFan() {
    rightFanEnabled = !rightFanEnabled;
    document.getElementById('right-fan-icon').src = getFanIcon(rightFanEnabled, rightFanHealthy);

    // Update on server
    fetch('/api/fan/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            right_fan_on: rightFanEnabled
        })
    })
    .catch(error => console.error('Error updating right fan:', error));
}

// Save fan settings and return to main screen
function saveFanSettings() {
    fetch('/api/fan/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            left_fan_on: leftFanEnabled,
            right_fan_on: rightFanEnabled,
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

// Update RPM displays and fan icons periodically
function updateRpmDisplays() {
    fetch('/api/fan/status')
        .then(response => response.json())
        .then(data => {
            // Update RPM values
            document.getElementById('left-fan-rpm').textContent = `${data.left_fan_rpm} RPM`;
            document.getElementById('right-fan-rpm').textContent = `${data.right_fan_rpm} RPM`;

            // Update fan states
            leftFanEnabled = data.left_fan_on;
            rightFanEnabled = data.right_fan_on;
            leftFanHealthy = data.left_fan_healthy;
            rightFanHealthy = data.right_fan_healthy;

            // Update fan icons
            document.getElementById('left-fan-icon').src = getFanIcon(leftFanEnabled, leftFanHealthy);
            document.getElementById('right-fan-icon').src = getFanIcon(rightFanEnabled, rightFanHealthy);
        })
        .catch(error => console.error('Error updating RPM:', error));
}

// Initialize
loadFanSettings();

// Update RPM displays every 2 seconds
setInterval(updateRpmDisplays, 1000);
