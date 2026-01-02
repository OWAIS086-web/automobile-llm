/**
 * Settings Page - Data Collection JavaScript
 * Handles PakWheels scraping and WATI data fetching from the settings page
 */

// Initialize data collection functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDataCollection();
});

function initializeDataCollection() {
    console.log('🔧 Initializing data collection functionality');
    
    // PakWheels scraping button
    const pakWheelsBtn = document.getElementById('startPakWheelsScraping');
    if (pakWheelsBtn) {
        pakWheelsBtn.addEventListener('click', startPakWheelsScraping);
    }
    
    // WATI fetching button
    const watiBtn = document.getElementById('startWatiFetching');
    if (watiBtn) {
        watiBtn.addEventListener('click', startWatiFetching);
    }
    
    // Update status on page load
    updateCollectionStatus();
    
    // Set up periodic status updates
    setInterval(updateCollectionStatus, 30000); // Update every 30 seconds
}

function startPakWheelsScraping() {
    const postsInput = document.getElementById('pakWheelsPosts');
    const posts = parseInt(postsInput.value);
    
    // Validate input
    if (!posts || posts < 10 || posts > 10000) {
        showToast('Please enter a valid number of posts (10-10,000)', 'error');
        return;
    }
    
    console.log('🚀 Starting PakWheels scraping for', posts, 'posts');
    
    // Disable button and show loading state
    const btn = document.getElementById('startPakWheelsScraping');
    btn.disabled = true;
    btn.innerHTML = '🔄 Starting Scraping...';
    
    // Update status
    updateStatusCard('pakwheelsStatus', 'Processing', 'processing');
    
    // Show progress popup
    showScrapingProgress('PakWheels', posts);
    
    // Make API call to start scraping
    fetch('/scrape_pakwheels', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            posts: posts.toString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const count = data.posts_scraped || posts;
            updateScrapingProgress(`Successfully scraped ${count} posts!`, 'success');
            updateStatusCard('pakwheelsStatus', 'Ready', 'ready');
            startEngineMonitoring();
        } else {
            updateScrapingProgress('Error: ' + (data.error || 'Unknown error'), 'error');
            updateStatusCard('pakwheelsStatus', 'Error', 'error');
        }
    })
    .catch(error => {
        console.error('❌ PakWheels scraping error:', error);
        updateScrapingProgress('Error: ' + error.message, 'error');
        updateStatusCard('pakwheelsStatus', 'Error', 'error');
    })
    .finally(() => {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '🔍 Start PakWheels Scraping';
    });
}

function startWatiFetching() {
    const daysSelect = document.getElementById('watiDays');
    const days = daysSelect.value;
    
    console.log('📱 Starting WATI data fetch for', days, 'days');
    
    // Disable button and show loading state
    const btn = document.getElementById('startWatiFetching');
    btn.disabled = true;
    btn.innerHTML = '🔄 Fetching Data...';
    
    // Update status
    updateStatusCard('watiStatus', 'Processing', 'processing');
    
    // Show progress popup
    showScrapingProgress('WATI', `${days} days`);
    
    // Start progress monitoring immediately
    startWatiProgressMonitoring();
    
    // Make API call to fetch WATI data
    fetch('/fetch_wati_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            period: `${days}d`
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const count = data.messages_imported || 0;
            updateScrapingProgress(`Successfully fetched ${count} WhatsApp messages!`, 'success');
            updateStatusCard('watiStatus', 'Ready', 'ready');
            startEngineMonitoring();
        } else {
            updateScrapingProgress('Error: ' + (data.error || 'Unknown error'), 'error');
            updateStatusCard('watiStatus', 'Error', 'error');
        }
    })
    .catch(error => {
        console.error('❌ WATI fetch error:', error);
        updateScrapingProgress('Error: ' + error.message, 'error');
        updateStatusCard('watiStatus', 'Error', 'error');
    })
    .finally(() => {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '📱 Fetch WATI Data';
    });
}

function updateStatusCard(statusId, text, type) {
    const statusEl = document.getElementById(statusId);
    if (statusEl) {
        statusEl.textContent = text;
        statusEl.className = `status-value ${type}`;
    }
}

function updateCollectionStatus() {
    // Check pipeline status
    fetch('/api/pipeline/status')
        .then(response => response.json())
        .then(data => {
            const status = data.status || 'unknown';
            let statusText = 'Unknown';
            let statusType = 'error';
            
            switch (status) {
                case 'ready':
                    statusText = 'Ready';
                    statusType = 'ready';
                    break;
                case 'processing':
                case 'enriching':
                case 'indexing':
                    statusText = 'Processing';
                    statusType = 'processing';
                    break;
                case 'error':
                case 'failed':
                    statusText = 'Error';
                    statusType = 'error';
                    break;
                default:
                    statusText = status.charAt(0).toUpperCase() + status.slice(1);
                    statusType = 'processing';
            }
            
            updateStatusCard('pipelineStatus', statusText, statusType);
        })
        .catch(error => {
            console.error('Error checking pipeline status:', error);
            updateStatusCard('pipelineStatus', 'Error', 'error');
        });
}

// Progress Popup Functions
function showScrapingProgress(source, count) {
    // Remove any existing progress popup
    const existingPopup = document.getElementById('scrapingProgressPopup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Create progress popup
    const progressPopup = document.createElement('div');
    progressPopup.id = 'scrapingProgressPopup';
    progressPopup.className = 'scraping-popup active';
    progressPopup.style.zIndex = '3000';
    
    progressPopup.innerHTML = `
        <div class="popup-content">
            <div class="popup-header">
                <div class="popup-icon ${source.toLowerCase()}">🚀</div>
                <div class="popup-title">Collecting ${source} Data</div>
            </div>
            <div class="popup-body">
                <div class="progress-container">
                    <div class="progress-status" id="progressStatus">
                        Starting data collection for ${count}...
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progressBar">
                            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
                <div class="progress-logs" id="progressLogs">
                    <div class="log-entry">📋 Collecting ${count} from ${source}</div>
                </div>
            </div>
            <div class="popup-actions">
                <button class="popup-btn popup-btn-cancel" onclick="hideScrapingProgress()" disabled>
                    Processing...
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(progressPopup);
}

function updateScrapingProgress(message, type = 'info') {
    const statusEl = document.getElementById('progressStatus');
    const logsEl = document.getElementById('progressLogs');
    
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `progress-status ${type}`;
    }
    
    if (logsEl) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : '📋';
        logEntry.textContent = `${icon} [${timestamp}] ${message}`;
        
        logsEl.appendChild(logEntry);
        logsEl.scrollTop = logsEl.scrollHeight;
    }
    
    if (type === 'success') {
        // Update close button for success states
        const closeBtn = document.querySelector('#scrapingProgressPopup .popup-btn-cancel');
        if (closeBtn) {
            closeBtn.textContent = 'Close';
            closeBtn.disabled = false;
            closeBtn.onclick = () => {
                hideScrapingProgress();
            };
        }
    } else if (type === 'error') {
        // Enable close button for errors
        const closeBtn = document.querySelector('#scrapingProgressPopup .popup-btn-cancel');
        if (closeBtn) {
            closeBtn.textContent = 'Close';
            closeBtn.disabled = false;
            closeBtn.onclick = () => {
                hideScrapingProgress();
            };
        }
    }
}

function hideScrapingProgress() {
    const progressPopup = document.getElementById('scrapingProgressPopup');
    if (progressPopup) {
        progressPopup.remove();
    }
}

function updateProgressBar(percentage) {
    const progressFill = document.getElementById('progressFill');
    if (progressFill) {
        progressFill.style.width = `${Math.min(percentage, 100)}%`;
    }
}

// Monitor WATI progress by checking logs
function startWatiProgressMonitoring() {
    let checkCount = 0;
    const maxChecks = 200; // 10 minutes max (3 second intervals)
    
    const checkProgress = () => {
        checkCount++;
        
        // Try to get progress from a logs endpoint (if available)
        fetch('/api/wati/progress')
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Progress endpoint not available');
                }
            })
            .then(data => {
                if (data.status === 'processing' && data.progress) {
                    const { current, total, contact_name, contact_phone } = data.progress;
                    updateScrapingProgress(
                        `Processing ${current}/${total}: ${contact_name} (${contact_phone})`, 
                        'info'
                    );
                    
                    // Update progress bar
                    if (total > 0) {
                        const percentage = Math.round((current / total) * 90); // Max 90% until complete
                        updateProgressBar(percentage);
                    }
                    
                    // Continue monitoring
                    if (checkCount < maxChecks) {
                        setTimeout(checkProgress, 3000); // Check every 3 seconds
                    }
                } else if (data.status === 'completed') {
                    // Process completed
                    updateScrapingProgress('WATI data fetch completed!', 'success');
                    updateProgressBar(100);
                } else if (data.status === 'error') {
                    updateScrapingProgress('WATI fetch encountered an error', 'error');
                }
            })
            .catch(error => {
                // Progress endpoint not available, continue with basic monitoring
                if (checkCount < maxChecks) {
                    setTimeout(checkProgress, 5000); // Check every 5 seconds
                }
            });
    };
    
    // Start monitoring after a short delay
    setTimeout(checkProgress, 2000);
}

function startEngineMonitoring() {
    updateScrapingProgress('Starting AI pipeline processing...', 'info');
    updateStatusCard('pipelineStatus', 'Processing', 'processing');
    
    let checkCount = 0;
    const maxChecks = 120; // 10 minutes max (5 second intervals)
    
    const checkEngine = () => {
        checkCount++;
        
        fetch('/api/pipeline/status')
            .then(response => response.json())
            .then(data => {
                const status = data.status || 'unknown';
                
                if (status === 'completed' || status === 'ready') {
                    // Pipeline completed successfully
                    updateScrapingProgress('✅ AI Pipeline completed successfully!', 'success');
                    updateStatusCard('pipelineStatus', 'Ready', 'ready');
                    updateProgressBar(100);
                    
                    // Show completion message and auto-close
                    setTimeout(() => {
                        updateScrapingProgress('🎉 Process complete! Data is now available.', 'success');
                        
                        // Close popup after showing completion message
                        setTimeout(() => {
                            hideScrapingProgress();
                            showToast('Data processing completed successfully!');
                        }, 2000);
                    }, 1000);
                    
                } else if (status === 'processing') {
                    // Still processing
                    updateScrapingProgress(`🔄 Processing data... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000); // Check every 5 seconds during processing
                    
                } else if (status === 'enriching') {
                    updateScrapingProgress(`🤖 Enriching data with AI analysis... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000);
                    
                } else if (status === 'indexing') {
                    updateScrapingProgress(`📚 Building vector database... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000);
                    
                } else if (status === 'error' || status === 'failed') {
                    updateScrapingProgress('❌ AI pipeline encountered an error', 'error');
                    updateStatusCard('pipelineStatus', 'Error', 'error');
                    
                } else if (checkCount >= maxChecks) {
                    updateScrapingProgress('⏰ Pipeline taking longer than expected. Check logs for details.', 'error');
                    updateStatusCard('pipelineStatus', 'Error', 'error');
                    
                } else {
                    // Continue monitoring with unknown status
                    updateScrapingProgress(`⏳ AI engine status: ${status}... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000); // Check every 5 seconds for unknown status
                }
            })
            .catch(error => {
                console.error('Error checking pipeline status:', error);
                if (checkCount < maxChecks) {
                    updateScrapingProgress(`🔍 Checking pipeline status... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000);
                } else {
                    updateScrapingProgress('❌ Could not check pipeline status. Please check manually.', 'error');
                    updateStatusCard('pipelineStatus', 'Error', 'error');
                }
            });
    };
    
    // Start monitoring after a short delay
    setTimeout(checkEngine, 2000);
}

// Toast notification function
function showToast(message, type = 'info') {
    // Remove existing toast
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        font-weight: 500;
        max-width: 400px;
        word-wrap: break-word;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Add CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);