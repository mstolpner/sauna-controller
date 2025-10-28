// Load settings from server
function loadSettings() {
    fetch('/api/settings/get')
        .then(response => response.json())
        .then(data => {
            document.getElementById('max-temp').value = data.max_temp_f;
            document.getElementById('preset-medium').value = data.preset_medium;
            document.getElementById('preset-high').value = data.preset_high;
        })
        .catch(error => console.error('Error loading settings:', error));
}

// Initialize
loadSettings();
