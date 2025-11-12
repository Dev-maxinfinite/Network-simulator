// Common JavaScript functions

// Theme toggle
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
}

// Load devices
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const devices = await response.json();
        return devices;
    } catch (error) {
        console.error('Error loading devices:', error);
        return [];
    }
}

// Start simulation
async function startSimulation(type = 'basic') {
    try {
        const response = await fetch('/api/start-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: type })
        });
        const result = await response.json();
        showNotification(result.message, 'success');
        return result;
    } catch (error) {
        console.error('Error starting simulation:', error);
        showNotification('Failed to start simulation', 'error');
    }
}

// Validate configuration
async function validateConfig(deviceName, configText) {
    try {
        const response = await fetch('/api/validate-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                device_name: deviceName,
                config: configText
            })
        });
        return await response.json();
    } catch (error) {
        console.error('Error validating config:', error);
        return { valid: false, errors: ['Validation failed'] };
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = '#27ae60';
    } else if (type === 'error') {
        notification.style.background = '#e74c3c';
    } else {
        notification.style.background = '#3498db';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Format bytes
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}