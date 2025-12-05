let tempUnit = 'F';
let currentTempF = 75;
let currentTargetTempF = 190;

// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Update clock every second
function updateClock() {
    const now = new Date();
    const hours = now.getHours() % 12 || 12;
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    document.getElementById('clock').textContent = `${hours}:${minutes}:${seconds}`;
}

// Toggle temperature unit between F and C
function toggleTempUnit() {
    tempUnit = tempUnit === 'F' ? 'C' : 'F';
    updateTemperatureDisplay();
    updateTargetTempDisplay();
}

// Update temperature display based on current unit
function updateTemperatureDisplay() {
    const tempElement = document.getElementById('temperature');
    if (tempUnit === 'F') {
        tempElement.textContent = `${Math.round(currentTempF)}°F`;
    } else {
        const tempC = (currentTempF - 32) * 5 / 9;
        tempElement.textContent = `${Math.round(tempC)}°C`;
    }
}

// Update target temperature display
function updateTargetTempDisplay() {
    const targetElement = document.getElementById('target-temp');
    if (tempUnit === 'F') {
        targetElement.textContent = `${Math.round(currentTargetTempF)}°F`;
    } else {
        const tempC = (currentTargetTempF - 32) * 5 / 9;
        targetElement.textContent = `${Math.round(tempC)}°C`;
    }
}

// Update target temperature from slider
function updateTargetTemp(value) {
    currentTargetTempF = parseInt(value);
    updateTargetTempDisplay();

    // Send to server
    fetch('/api/temperature/set', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({temp_f: currentTargetTempF})
    });
}

// Toggle sauna on/off
function toggleSauna() {
    fetch('/api/sauna/toggle', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            updateSaunaButton(data.sauna_on);
        });
}

// Toggle light on/off
function toggleLight() {
    fetch('/api/light/toggle', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log('Light toggled:', data.light_on);
        });
}

// Update sauna button image
function updateSaunaButton(isOn) {
    const saunaImg = document.getElementById('sauna-img');
    if (isOn) {
        saunaImg.src = '/icons/sauna_on.png';
    } else {
        saunaImg.src = '/icons/sauna_off.png';
    }
}

// Set temperature preset
function setPreset(preset) {
    fetch('/api/preset/set', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({preset: preset})
    })
    .then(response => response.json())
    .then(data => {
        currentTargetTempF = data.target_temp_f;
        document.getElementById('temp-slider').value = currentTargetTempF;
        updateTargetTempDisplay();
    });
}

// Fetch and update status from server
function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // Update temperature
            currentTempF = data.hot_room_temp_f;
            updateTemperatureDisplay();

            // Update humidity
            document.getElementById('humidity').textContent = `${Math.round(data.hot_room_humidity)}%`;

            // Update target temperature
            currentTargetTempF = data.target_temp_f;
            document.getElementById('temp-slider').value = currentTargetTempF;
            updateTargetTempDisplay();

            // Update sauna button
            updateSaunaButton(data.sauna_on);

            // Update light icon
            const lightIcon = document.getElementById('light-icon');
            if (data.light_on) {
                lightIcon.src = '/icons/light_on.png';
            } else {
                lightIcon.src = '/icons/light_off.png';
            }

            // Update heater icon - check for error first, then switch between on/off
            const heaterIcon = document.getElementById('heater-icon');
            if (data.heater_error) {
                heaterIcon.src = '/icons/heater_error.png';
            } else if (data.heater_on) {
                heaterIcon.src = '/icons/heater_on.png';
            } else {
                heaterIcon.src = '/icons/heater_off.png';
            }

            // Update WiFi icon
            const wifiIcon = document.getElementById('wifi-icon').querySelector('img');
            if (data.wifi_connected) {
                wifiIcon.src = '/icons/wifi.png';
            } else {
                wifiIcon.src = '/icons/wifi_nc.png';
            }

            // Update errors icon visibility
            const errorsIcon = document.getElementById('errors-icon');
            if (data.has_errors) {
                errorsIcon.style.display = 'block';
            } else {
                errorsIcon.style.display = 'none';
            }
        })
        .catch(error => console.error('Error fetching status:', error));
}

// Initialize
updateClock();
setInterval(updateClock, 1000);
updateStatus();
setInterval(updateStatus, 2000);
