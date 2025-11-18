// Get CSRF token from meta tag
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Load errors from server
function loadErrors() {
    fetch('/api/errors/get')
        .then(response => response.json())
        .then(data => {
            const errorsList = document.getElementById('errors-list');
            if (data.errors.length === 0) {
                errorsList.innerHTML = '<p>No errors</p>';
            } else {
                errorsList.innerHTML = '';
                data.errors.forEach(error => {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-item';

                    const typeSpan = document.createElement('div');
                    typeSpan.className = 'error-type';
                    typeSpan.textContent = error.type;

                    const messageSpan = document.createElement('div');
                    messageSpan.className = 'error-message';
                    messageSpan.textContent = error.message;

                    errorDiv.appendChild(typeSpan);
                    errorDiv.appendChild(messageSpan);
                    errorsList.appendChild(errorDiv);
                });
            }
        })
        .catch(error => console.error('Error loading errors:', error));
}

// Clear all errors
function clearErrors() {
    fetch('/api/errors/clear', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadErrors();
        }
    })
    .catch(error => console.error('Error clearing errors:', error));
}

// Initialize
loadErrors();
setInterval(loadErrors, 5000);
