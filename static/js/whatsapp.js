// WhatsApp Dashboard JavaScript - Modern Theme

// Theme management
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.getElementById('themeIcon').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    updateLogo(savedTheme);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    document.getElementById('themeIcon').textContent = newTheme === 'dark' ? '☀️' : '🌙';
    updateLogo(newTheme);
}

function updateLogo(theme) {
    const logo = document.getElementById('navLogo');
    if (logo) {
        const logoFile = theme === 'dark' ? 'light-logo.svg' : 'dark-logo.svg';
        logo.src = `/static/images/${logoFile}`;
    }
}

// Sidebar management - REMOVED
function toggleSidebar() {
    // No sidebar anymore
    console.log('Sidebar functionality removed');
}

// Filter management
function applyFilters() {
    try {
        const dateFrom = document.getElementById('dateFrom')?.value || '';
        const dateTo = document.getElementById('dateTo')?.value || '';
        const messageType = document.getElementById('messageType')?.value || 'all';
        const customerSearch = document.getElementById('customerSearch')?.value || '';
        
        if (dateFrom && dateTo && dateFrom > dateTo) {
            showNotification('Start date cannot be after end date', 'error');
            return;
        }
        
        showLoading();
        showNotification('Applying filters...', 'info');
        
        // Filter messages without page refresh
        filterMessages(dateFrom, dateTo, messageType, customerSearch);
    } catch (error) {
        console.warn('Error applying filters:', error);
        hideLoading();
        showNotification('Error applying filters', 'error');
    }
}

function applyDateFilter() {
    applyFilters();
}

function clearAllFilters() {
    try {
        // Clear all filter inputs
        const dateFrom = document.getElementById('dateFrom');
        const dateTo = document.getElementById('dateTo');
        const messageType = document.getElementById('messageType');
        const customerSearch = document.getElementById('customerSearch');
        
        if (dateFrom) dateFrom.value = '';
        if (dateTo) dateTo.value = '';
        if (messageType) messageType.value = 'all';
        if (customerSearch) customerSearch.value = '';
        
        // Apply cleared filters
        filterMessages('', '', 'all', '');
        showNotification('Filters cleared', 'success');
    } catch (error) {
        console.warn('Error clearing filters:', error);
        showNotification('Error clearing filters', 'error');
    }
}

function filterMessages(dateFrom, dateTo, messageType, customerSearch) {
    try {
        const messageCards = document.querySelectorAll('.message-card, .conversation-message');
        let visibleCount = 0;
        
        messageCards.forEach(card => {
            let shouldShow = true;
            
            // Date filtering
            const cardDate = card.getAttribute('data-date');
            if (dateFrom && cardDate && cardDate < dateFrom) shouldShow = false;
            if (dateTo && cardDate && cardDate > dateTo) shouldShow = false;
            
            // Message type filtering
            const cardType = card.getAttribute('data-type');
            if (messageType !== 'all' && cardType !== messageType) shouldShow = false;
            
            // Customer search filtering
            const cardCustomer = card.getAttribute('data-customer') || '';
            if (customerSearch && !cardCustomer.includes(customerSearch.toLowerCase())) shouldShow = false;
            
            // Apply filter with animation
            if (shouldShow) {
                visibleCount++;
                card.style.display = '';
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    card.style.transition = 'all 0.3s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 100);
            } else {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'translateY(-20px)';
                
                setTimeout(() => {
                    card.style.display = 'none';
                }, 300);
            }
        });
        
        // Update empty state
        updateEmptyState(visibleCount);
        hideLoading();
        
        if (visibleCount === 0) {
            showNotification('No messages match the current filters', 'warning');
        } else {
            showNotification(`Showing ${visibleCount} message${visibleCount > 1 ? 's' : ''}`, 'success');
        }
    } catch (error) {
        console.warn('Error filtering messages:', error);
        hideLoading();
        showNotification('Error filtering messages', 'error');
    }
}

function updateEmptyState(visibleCount) {
    try {
        let emptyState = document.querySelector('.empty-state');
        const messagesGrid = document.querySelector('.messages-grid, .conversation-thread');
        
        if (visibleCount === 0 && messagesGrid) {
            if (!emptyState) {
                emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                emptyState.innerHTML = `
                    <div class="empty-icon">🔍</div>
                    <h3 class="empty-title">No Messages Found</h3>
                    <p class="empty-text">No messages match your current filters. Try adjusting the filters or clearing them.</p>
                `;
                messagesGrid.parentNode.appendChild(emptyState);
            }
            emptyState.style.display = 'block';
        } else if (emptyState) {
            emptyState.style.display = 'none';
        }
    } catch (error) {
        console.warn('Error updating empty state:', error);
    }
}

// Loading management
function showLoading() {
    try {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
            loadingIndicator.innerHTML = '🔄 Loading WhatsApp messages...';
        }
    } catch (error) {
        console.warn('Error showing loading indicator:', error);
    }
}

function hideLoading() {
    try {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    } catch (error) {
        console.warn('Error hiding loading indicator:', error);
    }
}

// Navigation functions
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

function goToAnalytics() {
    window.location.href = '/analysis';
}

function goToChatbot() {
    window.location.href = '/chatbot_advanced';
}

// Message card interactions
function highlightMessageCard(card) {
    try {
        card.style.transform = 'translateY(-12px) scale(1.03)';
        card.style.boxShadow = '0 25px 50px rgba(37, 211, 102, 0.4)';
    } catch (error) {
        console.warn('Error highlighting message card:', error);
    }
}

function resetMessageCard(card) {
    try {
        card.style.transform = '';
        card.style.boxShadow = '';
    } catch (error) {
        console.warn('Error resetting message card:', error);
    }
}

// Search functionality
function searchMessages(query) {
    try {
        const messageCards = document.querySelectorAll('.message-card');
        const searchQuery = query.toLowerCase();
        
        messageCards.forEach(card => {
            const customerName = card.querySelector('.customer-name')?.textContent.toLowerCase() || '';
            const messageContent = card.querySelector('.preview-message')?.textContent.toLowerCase() || '';
            
            const matches = customerName.includes(searchQuery) || messageContent.includes(searchQuery);
            
            if (matches || searchQuery === '') {
                card.style.display = 'block';
                card.style.opacity = '1';
            } else {
                card.style.display = 'none';
                card.style.opacity = '0';
            }
        });
        
        // Update results count
        const visibleCards = document.querySelectorAll('.message-card[style*="display: block"], .message-card:not([style*="display: none"])');
        updateSearchResults(visibleCards.length);
    } catch (error) {
        console.warn('Error searching messages:', error);
    }
}

function updateSearchResults(count) {
    try {
        let resultsElement = document.getElementById('searchResults');
        
        if (!resultsElement) {
            resultsElement = document.createElement('div');
            resultsElement.id = 'searchResults';
            resultsElement.style.cssText = `
                text-align: center;
                padding: 16px;
                color: var(--text-secondary);
                font-size: 14px;
                font-weight: 500;
            `;
            
            const messagesGrid = document.querySelector('.messages-grid');
            if (messagesGrid) {
                messagesGrid.parentNode.insertBefore(resultsElement, messagesGrid);
            }
        }
        
        if (count === 0) {
            resultsElement.textContent = '🔍 No messages found matching your search';
            resultsElement.style.display = 'block';
        } else {
            resultsElement.style.display = 'none';
        }
    } catch (error) {
        console.warn('Error updating search results:', error);
    }
}

// Real-time updates
function startRealTimeUpdates() {
    try {
        // Check for new messages every 30 seconds
        setInterval(() => {
            checkForNewMessages();
        }, 30000);
    } catch (error) {
        console.warn('Error starting real-time updates:', error);
    }
}

function checkForNewMessages() {
    try {
        fetch('/api/whatsapp/check-updates')
            .then(response => response.json())
            .then(data => {
                if (data.hasNewMessages) {
                    showNewMessageNotification(data.newCount);
                }
            })
            .catch(error => {
                console.warn('Error checking for new messages:', error);
            });
    } catch (error) {
        console.warn('Error in checkForNewMessages:', error);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    try {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notif => notif.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 90px;
            right: 20px;
            background: ${getNotificationColor(type)};
            color: white;
            padding: 12px 20px;
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            font-weight: 600;
            font-size: 14px;
            max-width: 300px;
            animation: slideInRight 0.3s ease;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);
    } catch (error) {
        console.warn('Error showing notification:', error);
    }
}

function getNotificationColor(type) {
    switch (type) {
        case 'success': return 'linear-gradient(135deg, #10b981, #059669)';
        case 'error': return 'linear-gradient(135deg, #ef4444, #dc2626)';
        case 'warning': return 'linear-gradient(135deg, #f59e0b, #d97706)';
        default: return 'linear-gradient(135deg, #25d366, #128c7e)';
    }
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(100px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideOutRight {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100px); }
    }
`;
document.head.appendChild(notificationStyles);

// Statistics updates
function updateStatistics() {
    try {
        fetch('/api/whatsapp/stats')
            .then(response => response.json())
            .then(stats => {
                // Update stat values
                const statElements = {
                    'total_messages': document.querySelector('.stat-value:not(.complaint):not(.query)'),
                    'total_complaints': document.querySelector('.stat-value.complaint'),
                    'total_queries': document.querySelector('.stat-value.query')
                };
                
                Object.entries(statElements).forEach(([key, element]) => {
                    if (element && stats[key] !== undefined) {
                        element.textContent = stats[key];
                        
                        // Add animation
                        element.style.transform = 'scale(1.1)';
                        setTimeout(() => {
                            element.style.transform = 'scale(1)';
                        }, 200);
                    }
                });
            })
            .catch(error => {
                console.warn('Error updating statistics:', error);
            });
    } catch (error) {
        console.warn('Error in updateStatistics:', error);
    }
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    try {
        document.addEventListener('keydown', (event) => {
            // Ctrl/Cmd + K for search
            if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
                event.preventDefault();
                const searchInput = document.querySelector('input[name="customer"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape to close sidebar on mobile
            if (event.key === 'Escape') {
                const sidebar = document.getElementById('sidebar');
                if (sidebar && !sidebar.classList.contains('collapsed')) {
                    toggleSidebar();
                }
            }
            
            // Ctrl/Cmd + R to refresh
            if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
                event.preventDefault();
                window.location.reload();
            }
        });
    } catch (error) {
        console.warn('Error initializing keyboard shortcuts:', error);
    }
}

// Error handling
function handleError(error, context = 'Unknown') {
    console.warn(`WhatsApp Dashboard Error (${context}):`, error);
    
    // Show user-friendly error message
    const errorElement = document.createElement('div');
    errorElement.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        box-shadow: var(--shadow-lg);
        z-index: 1001;
        font-weight: 600;
        max-width: 300px;
    `;
    
    errorElement.innerHTML = `⚠️ Something went wrong. Please refresh the page.`;
    document.body.appendChild(errorElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorElement.parentNode) {
            errorElement.remove();
        }
    }, 5000);
}

// Suppress external script errors
window.addEventListener('error', function(e) {
    // Suppress errors from external scripts/extensions
    if (e.filename && (
        e.filename.includes('giveFreely') || 
        e.filename.includes('content-script') ||
        e.filename.includes('extension')
    )) {
        e.preventDefault();
        return true;
    }
});

// Initialize responsive behavior - REMOVED (no sidebar)
function initializeResponsive() {
    // No sidebar to manage anymore
    console.log('WhatsApp pages now use full-width layout');
}

// Initialize everything when DOM is ready
function initializeWhatsAppDashboard() {
    try {
        loadTheme();
        hideLoading();
        initializeKeyboardShortcuts();
        initializeResponsive();
        
        // Start real-time updates if not in development
        if (window.location.hostname !== 'localhost') {
            startRealTimeUpdates();
        }
        
        // Update statistics every 5 minutes
        setInterval(updateStatistics, 300000);
        
        // Add event listeners to message cards
        const messageCards = document.querySelectorAll('.message-card');
        messageCards.forEach(card => {
            card.addEventListener('mouseenter', () => highlightMessageCard(card));
            card.addEventListener('mouseleave', () => resetMessageCard(card));
        });
        
        // Add search functionality to customer input
        const customerInput = document.querySelector('input[name="customer"]');
        if (customerInput) {
            customerInput.addEventListener('input', (e) => {
                searchMessages(e.target.value);
            });
        }
        
        console.log('WhatsApp Dashboard initialized successfully');
    } catch (error) {
        handleError(error, 'Initialization');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWhatsAppDashboard);
} else {
    initializeWhatsAppDashboard();
}