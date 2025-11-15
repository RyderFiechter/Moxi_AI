// Storage Node Dashboard JavaScript
const API_BASE = window.location.origin;

// Load status on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadConfig();
    loadRegistryStatus();
    setInterval(loadStatus, 5000); // Refresh every 5 seconds
});

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();
        
        document.getElementById('status').innerHTML = `
            <div class="status-grid">
                <div class="status-item">
                    <label>Wallet Address</label>
                    <value>${data.wallet_address.substring(0, 10)}...</value>
                </div>
                <div class="status-item">
                    <label>Payment Wallet</label>
                    <value>${data.payment_wallet.substring(0, 10)}...</value>
                </div>
                <div class="status-item">
                    <label>Available Storage</label>
                    <value>${data.available_storage_gb.toFixed(2)} GB</value>
                </div>
                <div class="status-item">
                    <label>Total Storage</label>
                    <value>${data.total_storage_gb.toFixed(2)} GB</value>
                </div>
                <div class="status-item">
                    <label>Uptime</label>
                    <value>${data.uptime_formatted}</value>
                </div>
                <div class="status-item">
                    <label>Status</label>
                    <value class="${data.is_online ? 'success' : 'error'}">${data.is_online ? 'Online' : 'Offline'}</value>
                </div>
            </div>
        `;
        
        // Update storage info
        document.getElementById('storageInfo').innerHTML = `
            <div class="status-grid">
                <div class="status-item">
                    <label>Total Storage</label>
                    <value>${data.total_storage_gb.toFixed(2)} GB</value>
                </div>
                <div class="status-item">
                    <label>Used Storage</label>
                    <value>${data.used_storage_gb.toFixed(2)} GB</value>
                </div>
                <div class="status-item">
                    <label>Available Storage</label>
                    <value>${data.available_storage_gb.toFixed(2)} GB</value>
                </div>
            </div>
        `;
    } catch (error) {
        document.getElementById('status').innerHTML = `<div class="error">Error loading status: ${error.message}</div>`;
    }
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();
        
        document.getElementById('paymentWallet').value = data.payment_wallet || '';
        
        // Update lending status
        const statusEl = document.getElementById('lendingStatus');
        const toggleBtn = document.getElementById('lendingToggle');
        
        if (data.storage_lending_enabled) {
            statusEl.textContent = 'Enabled';
            statusEl.className = 'success';
            toggleBtn.textContent = 'Disable';
            toggleBtn.className = 'btn-disable';
        } else {
            statusEl.textContent = 'Disabled';
            statusEl.className = 'error';
            toggleBtn.textContent = 'Enable';
            toggleBtn.className = 'btn-enable';
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

async function loadRegistryStatus() {
    try {
        const response = await fetch(`${API_BASE}/registry/status`);
        const data = await response.json();
        
        const statusEl = document.getElementById('registryStatus');
        
        if (data.registered) {
            statusEl.innerHTML = `
                <div class="info-box success">
                    <strong>✅ Registered</strong>
                    <p>Storage: ${data.provider_info.storageGB} GB</p>
                    <p>Price: ${(parseInt(data.provider_info.pricePerGB) / 1e18).toFixed(6)} ETH/GB</p>
                    <p>Status: ${data.provider_info.isActive ? 'Active' : 'Inactive'}</p>
                </div>
            `;
            document.getElementById('registerForm').style.display = 'none';
            document.getElementById('updateBtn').style.display = 'inline-block';
            if (data.provider_info.isActive) {
                document.getElementById('deactivateBtn').style.display = 'inline-block';
                document.getElementById('activateBtn').style.display = 'none';
            } else {
                document.getElementById('activateBtn').style.display = 'inline-block';
                document.getElementById('deactivateBtn').style.display = 'none';
            }
        } else {
            statusEl.innerHTML = `
                <div class="info-box warning">
                    <strong>⚠️ Not Registered</strong>
                    <p>${data.message || 'Configure registry settings in config.json to register'}</p>
                </div>
            `;
            document.getElementById('registerForm').style.display = 'block';
            document.getElementById('updateBtn').style.display = 'none';
            document.getElementById('activateBtn').style.display = 'none';
            document.getElementById('deactivateBtn').style.display = 'none';
        }
    } catch (error) {
        document.getElementById('registryStatus').innerHTML = `
            <div class="info-box error">
                <strong>❌ Error</strong>
                <p>${error.message}</p>
            </div>
        `;
    }
}

async function updatePaymentWallet() {
    const wallet = document.getElementById('paymentWallet').value.trim();
    if (!wallet || !wallet.startsWith('0x')) {
        alert('Please enter a valid wallet address');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/payment-wallet`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ payment_wallet: wallet })
        });
        
        const data = await response.json();
        if (response.ok) {
            alert('✅ Payment wallet updated!');
            loadConfig();
            loadRegistryStatus();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function toggleStorageLending() {
    const currentStatus = document.getElementById('lendingStatus').textContent === 'Enabled';
    const endpoint = currentStatus ? 'disable' : 'enable';
    
    try {
        const response = await fetch(`${API_BASE}/storage-lending/${endpoint}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Storage lending ${endpoint}d!`);
            loadConfig();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function registerWithRegistry() {
    const storageGB = parseInt(document.getElementById('storageGB').value);
    const pricePerGB = parseFloat(document.getElementById('pricePerGB').value);
    
    if (!storageGB || storageGB <= 0) {
        alert('Please enter valid storage amount');
        return;
    }
    
    if (!pricePerGB || pricePerGB <= 0) {
        alert('Please enter valid price');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/registry/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ storage_gb: storageGB, price_per_gb_eth: pricePerGB })
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Registered! TX: ${data.transaction_hash}`);
            loadRegistryStatus();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function updateRegistryStorage() {
    try {
        const response = await fetch(`${API_BASE}/registry/update`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Storage updated! TX: ${data.transaction_hash}`);
            loadRegistryStatus();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function activateInRegistry() {
    try {
        const response = await fetch(`${API_BASE}/registry/activate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Activated! TX: ${data.transaction_hash}`);
            loadRegistryStatus();
            loadConfig();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deactivateInRegistry() {
    try {
        const response = await fetch(`${API_BASE}/registry/deactivate`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (response.ok) {
            alert(`✅ Deactivated! TX: ${data.transaction_hash}`);
            loadRegistryStatus();
            loadConfig();
        } else {
            alert(`Error: ${data.detail}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

