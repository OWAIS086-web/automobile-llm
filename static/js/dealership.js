/* ============================================
   DEALERSHIP MANAGEMENT JAVASCRIPT
   ============================================ */

// Disable console logging in production
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    console.log = console.warn = console.error = function() {};
}

// Global variables
let dealershipData = {};
let currentFilters = {};
let charts = {};

// Initialize dashboard
function initializeDashboard() {
    console.log('🏢 Initializing Dealership Management System...');
    
    try {
        // Hide loading screen
        setTimeout(() => {
            const loadingScreen = document.getElementById('loadingScreen');
            const mainContainer = document.getElementById('mainContainer');
            
            if (loadingScreen && mainContainer) {
                loadingScreen.style.opacity = '0';
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                    mainContainer.style.opacity = '1';
                }, 300);
            }
        }, 1500);
        
        // Initialize components
        initializeEventListeners();
        loadDashboardData();
        
        // Initialize table features with better error handling
        setTimeout(() => {
            try {
                makeTableSortable();
                addTableSearch();
                initializeTablePagination();
            } catch (error) {
                console.error('❌ Error initializing table features:', error);
            }
        }, 100);
        
        console.log('✅ Dealership Management System initialized');
        
    } catch (error) {
        console.error('❌ Error initializing dealership system:', error);
        
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="position: fixed; top: 20px; right: 20px; background: #ef4444; 
                        color: white; padding: 16px; border-radius: 8px; z-index: 10000;">
                ❌ Error loading dealership system. Please refresh the page.
            </div>
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize table pagination
function initializeTablePagination() {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('.no-data'));
    
    if (rows.length <= 50) return; // No pagination needed for small datasets
    
    const rowsPerPage = 50;
    let currentPage = 1;
    const totalPages = Math.ceil(rows.length / rowsPerPage);
    
    // Create pagination controls
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-container';
    paginationContainer.innerHTML = `
        <div class="pagination-info">
            Showing <span id="pageStart">1</span>-<span id="pageEnd">${Math.min(rowsPerPage, rows.length)}</span> of <span id="totalRows">${rows.length}</span> records
        </div>
        <div class="pagination-controls">
            <button class="pagination-btn" id="prevPage" disabled>← Previous</button>
            <div class="pagination-numbers" id="pageNumbers"></div>
            <button class="pagination-btn" id="nextPage" ${totalPages <= 1 ? 'disabled' : ''}>Next →</button>
        </div>
    `;
    
    // Insert pagination after table
    const tableContainer = document.querySelector('.table-container');
    if (tableContainer) {
        tableContainer.parentNode.insertBefore(paginationContainer, tableContainer.nextSibling);
    }
    
    // Pagination functions
    function showPage(page) {
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        
        rows.forEach((row, index) => {
            row.style.display = (index >= start && index < end) ? '' : 'none';
        });
        
        // Update pagination info
        const pageStartEl = document.getElementById('pageStart');
        const pageEndEl = document.getElementById('pageEnd');
        if (pageStartEl) pageStartEl.textContent = start + 1;
        if (pageEndEl) pageEndEl.textContent = Math.min(end, rows.length);
        
        // Update buttons
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        if (prevBtn) prevBtn.disabled = page === 1;
        if (nextBtn) nextBtn.disabled = page === totalPages;
        
        // Update page numbers
        updatePageNumbers(page, totalPages);
        
        currentPage = page;
    }
    
    function updatePageNumbers(current, total) {
        const container = document.getElementById('pageNumbers');
        if (!container) return;
        
        container.innerHTML = '';
        
        const maxVisible = 5;
        let start = Math.max(1, current - Math.floor(maxVisible / 2));
        let end = Math.min(total, start + maxVisible - 1);
        
        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            const btn = document.createElement('button');
            btn.className = `pagination-number ${i === current ? 'active' : ''}`;
            btn.textContent = i;
            btn.addEventListener('click', () => showPage(i));
            container.appendChild(btn);
        }
    }
    
    // Event listeners - use setTimeout to ensure DOM is ready
    setTimeout(() => {
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (currentPage > 1) showPage(currentPage - 1);
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (currentPage < totalPages) showPage(currentPage + 1);
            });
        }
        
        // Show first page
        showPage(1);
    }, 0);
}

// Event listeners
function initializeEventListeners() {
    // Navigation active state
    updateActiveNavigation();
    
    // Navigation dropdown functionality
    initializeNavigationDropdown();
    
    // Ensure proper scrolling
    ensureProperScrolling();
    
    // Modal event listeners
    setupModalEventListeners();
    
    // Search functionality
    setupSearchFunctionality();
    
    // Filter functionality
    setupFilterFunctionality();
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        const navDropdown = document.getElementById('navDropdownMenu');
        const navToggle = document.getElementById('navDropdownToggle');
        
        if (navDropdown && navToggle && !navDropdown.contains(event.target) && !navToggle.contains(event.target)) {
            closeNavigationDropdown();
        }
    });
}

// Update active navigation based on current page
function updateActiveNavigation() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
}

// Modal event listeners
function setupModalEventListeners() {
    // Close modal on outside click
    document.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const activeModal = document.querySelector('.modal.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });
}

// Search functionality
function setupSearchFunctionality() {
    // VIN search input
    const vinInput = document.getElementById('vinInput');
    if (vinInput) {
        vinInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                searchVin();
            }
        });
        
        // Format VIN input (uppercase, alphanumeric only)
        vinInput.addEventListener('input', function(event) {
            let value = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length > 17) {
                value = value.substring(0, 17);
            }
            event.target.value = value;
        });
    }
}

// Filter functionality
function setupFilterFunctionality() {
    // Date range filters
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            applyFilters();
        });
    });
    
    // Dropdown filters
    const selectInputs = document.querySelectorAll('select');
    selectInputs.forEach(select => {
        select.addEventListener('change', function() {
            applyFilters();
        });
    });
}

// Load dashboard data
function loadDashboardData() {
    // Load summary statistics
    loadSummaryStats();
    
    // Load recent activity
    loadRecentActivity();
    
    // Load charts if on dashboard
    if (window.location.pathname === '/dealership') {
        loadDashboardCharts();
    }
}

// Load summary statistics
function loadSummaryStats() {
    // This would typically fetch from API
    console.log('📊 Loading summary statistics...');
    
    // Animate stat numbers
    animateStatNumbers();
}

// Animate stat numbers
function animateStatNumbers() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(element => {
        const finalValue = parseInt(element.textContent) || 0;
        let currentValue = 0;
        const increment = Math.ceil(finalValue / 50);
        
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            element.textContent = currentValue.toLocaleString();
        }, 30);
    });
}

// Load recent activity
function loadRecentActivity() {
    console.log('📋 Loading recent activity...');
    // This would typically fetch from API
}

// Load dashboard charts
function loadDashboardCharts() {
    console.log('📈 Loading dashboard charts...');
    // This would create charts using Chart.js
}

// Apply filters
function applyFilters() {
    console.log('🔍 Applying filters...');
    
    // Collect filter values
    const filters = {};
    
    // Date filters
    const dateFrom = document.getElementById('dateFrom');
    const dateTo = document.getElementById('dateTo');
    if (dateFrom && dateFrom.value) filters.date_from = dateFrom.value;
    if (dateTo && dateTo.value) filters.date_to = dateTo.value;
    
    // Dealership filter
    const dealership = document.getElementById('dealershipFilter');
    if (dealership && dealership.value) filters.dealership = dealership.value;
    
    // VIN filter
    const vin = document.getElementById('vinFilter');
    if (vin && vin.value) filters.vin = vin.value;
    
    // Claim type filter
    const claimType = document.getElementById('claimTypeFilter');
    if (claimType && claimType.value) filters.claim_type = claimType.value;
    
    // Campaign filter
    const campaign = document.getElementById('campaignFilter');
    if (campaign && campaign.value) filters.campaign = campaign.value;
    
    // RO Number filter
    const roNumber = document.getElementById('roNumberFilter');
    if (roNumber && roNumber.value) filters.ro_number = roNumber.value;
    
    // Store current filters
    currentFilters = filters;
    
    // Build query string
    const queryParams = new URLSearchParams();
    Object.keys(filters).forEach(key => {
        if (filters[key]) {
            queryParams.append(key, filters[key]);
        }
    });
    
    // Reload page with filters
    const currentUrl = window.location.pathname;
    const newUrl = queryParams.toString() ? `${currentUrl}?${queryParams.toString()}` : currentUrl;
    
    // Show loading state
    showNotification('Applying filters...', 'info');
    
    // Navigate to filtered URL
    window.location.href = newUrl;
}

// Clear all filters
function clearFilters() {
    console.log('🗑️ Clearing filters...');
    
    // Clear all filter inputs
    const filterInputs = document.querySelectorAll('#dateFrom, #dateTo, #dealershipFilter, #vinFilter, #claimTypeFilter, #campaignFilter, #roNumberFilter');
    filterInputs.forEach(input => {
        if (input.type === 'select-one') {
            input.selectedIndex = 0;
        } else {
            input.value = '';
        }
    });
    
    // Clear current filters
    currentFilters = {};
    
    // Reload page without filters
    window.location.href = window.location.pathname;
}

// Real-time table filtering (client-side)
function filterTableRows() {
    const table = document.querySelector('.data-table tbody');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const searchTerm = document.getElementById('tableSearch')?.value.toLowerCase() || '';
    
    rows.forEach(row => {
        if (row.querySelector('.no-data')) return; // Skip no-data row
        
        const text = row.textContent.toLowerCase();
        const shouldShow = text.includes(searchTerm);
        
        row.style.display = shouldShow ? '' : 'none';
    });
    
    // Update visible count
    const visibleRows = Array.from(rows).filter(row => 
        row.style.display !== 'none' && !row.querySelector('.no-data')
    ).length;
    
    const countElement = document.querySelector('.table-title p');
    if (countElement && searchTerm) {
        countElement.textContent = `${visibleRows} records found (filtered)`;
    }
}

// Add table search functionality
function addTableSearch() {
    const tableHeader = document.querySelector('.table-header');
    if (!tableHeader || document.getElementById('tableSearch')) return;
    
    const searchContainer = document.createElement('div');
    searchContainer.className = 'table-search';
    searchContainer.innerHTML = `
        <input type="text" id="tableSearch" placeholder="Search in table..." class="search-input">
    `;
    
    // Insert search before table actions
    const tableActions = tableHeader.querySelector('.table-actions');
    if (tableActions) {
        tableHeader.insertBefore(searchContainer, tableActions);
    } else {
        tableHeader.appendChild(searchContainer);
    }
    
    // Add event listener with null check
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('input', filterTableRows);
    }
}

// Sort table columns
function sortTable(columnIndex, dataType = 'text') {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('.no-data'));
    
    // Toggle sort direction
    const currentSort = table.dataset.sortColumn;
    const currentDirection = table.dataset.sortDirection || 'asc';
    const newDirection = (currentSort == columnIndex && currentDirection === 'asc') ? 'desc' : 'asc';
    
    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex]?.textContent.trim() || '';
        const bVal = b.cells[columnIndex]?.textContent.trim() || '';
        
        let comparison = 0;
        
        if (dataType === 'number') {
            const aNum = parseFloat(aVal.replace(/[^\d.-]/g, '')) || 0;
            const bNum = parseFloat(bVal.replace(/[^\d.-]/g, '')) || 0;
            comparison = aNum - bNum;
        } else if (dataType === 'date') {
            const aDate = new Date(aVal) || new Date(0);
            const bDate = new Date(bVal) || new Date(0);
            comparison = aDate - bDate;
        } else {
            comparison = aVal.localeCompare(bVal);
        }
        
        return newDirection === 'asc' ? comparison : -comparison;
    });
    
    // Update table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicators
    table.dataset.sortColumn = columnIndex;
    table.dataset.sortDirection = newDirection;
    
    // Update header indicators
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.classList.remove('sort-asc', 'sort-desc');
        if (index === columnIndex) {
            header.classList.add(`sort-${newDirection}`);
        }
    });
}

// Make table headers clickable for sorting
function makeTableSortable() {
    const table = document.querySelector('.data-table');
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        if (header.textContent.trim() === 'Actions') return; // Skip actions column
        
        header.style.cursor = 'pointer';
        header.style.userSelect = 'none';
        header.title = 'Click to sort';
        
        // Determine data type based on header text
        let dataType = 'text';
        const headerText = header.textContent.toLowerCase();
        if (headerText.includes('date') || headerText.includes('time')) {
            dataType = 'date';
        } else if (headerText.includes('cost') || headerText.includes('amount') || headerText.includes('count')) {
            dataType = 'number';
        }
        
        header.addEventListener('click', () => sortTable(index, dataType));
    });
}

// Get current page type
function getCurrentPageType() {
    const path = window.location.pathname;
    if (path.includes('warranty-claims')) return 'warranty-claims';
    if (path.includes('campaign-reports')) return 'campaign-reports';
    if (path.includes('pdi-inspections')) return 'pdi-inspections';
    if (path.includes('repair-orders')) return 'repair-orders';
    return 'dashboard';
}

// Filter functions for different pages
function filterWarrantyClaims(filters) {
    console.log('🔍 Filtering warranty claims:', filters);
    // Implementation would filter the displayed claims
}

function filterCampaignReports(filters) {
    console.log('🔍 Filtering campaign reports:', filters);
    // Implementation would filter the displayed campaigns
}

function filterPDIInspections(filters) {
    console.log('🔍 Filtering PDI inspections:', filters);
    // Implementation would filter the displayed PDI reports
}

function filterRepairOrders(filters) {
    console.log('🔍 Filtering repair orders:', filters);
    // Implementation would filter the displayed repair orders
}

// VIN search functionality
function searchVin() {
    const vinInput = document.getElementById('vinInput');
    if (!vinInput) return;
    
    const vin = vinInput.value.trim().toUpperCase();
    
    if (vin.length !== 17) {
        showNotification('Please enter a valid 17-character VIN number', 'error');
        return;
    }
    
    // Validate VIN format (basic validation)
    if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) {
        showNotification('Invalid VIN format. Please check and try again.', 'error');
        return;
    }
    
    console.log('🔍 Searching VIN:', vin);
    
    // Close modal
    closeVinSearch();
    
    // Redirect to VIN history page
    window.location.href = `/dealership/vin-history?vin=${vin}`;
}

// Close VIN search modal
function closeVinSearch() {
    const modal = document.getElementById('vinSearchModal');
    if (modal) {
        modal.classList.remove('active');
        const input = document.getElementById('vinInput');
        if (input) input.value = '';
    }
}

// Export functionality
function exportData(type, format = 'csv') {
    console.log(`📤 Exporting ${type} data as ${format}...`);
    
    showNotification('Preparing export...', 'info');
    
    // Make API call to export data
    fetch(`/api/dealership/export?type=${type}&format=${format}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Create download link
                const blob = new Blob([data.csv_data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${type}_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showNotification('Export completed successfully!', 'success');
            } else {
                showNotification('Export failed: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Export error:', error);
            showNotification('Export failed. Please try again.', 'error');
        });
}

// Notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getNotificationIcon(type)}</span>
            <span class="notification-message">${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Get notification icon
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return '✅';
        case 'error': return '❌';
        case 'warning': return '⚠️';
        default: return 'ℹ️';
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'PKR'
    }).format(amount);
}

function formatVIN(vin) {
    if (!vin) return 'N/A';
    return vin.toUpperCase();
}

// Chart creation utilities
function createChart(canvasId, type, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    // Default options
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim()
                }
            }
        },
        scales: {
            y: {
                ticks: {
                    color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim()
                },
                grid: {
                    color: getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim()
                }
            },
            x: {
                ticks: {
                    color: getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim()
                },
                grid: {
                    color: getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim()
                }
            }
        }
    };
    
    // Merge options
    const finalOptions = { ...defaultOptions, ...options };
    
    // Create chart
    const chart = new Chart(ctx, {
        type: type,
        data: data,
        options: finalOptions
    });
    
    // Store chart reference
    charts[canvasId] = chart;
    
    return chart;
}

// Update charts on theme change
function updateChartsTheme() {
    Object.values(charts).forEach(chart => {
        if (chart && chart.options) {
            // Update colors based on current theme
            const textPrimary = getComputedStyle(document.documentElement).getPropertyValue('--text-primary').trim();
            const textSecondary = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim();
            const borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim();
            
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = textPrimary;
            }
            
            if (chart.options.scales) {
                if (chart.options.scales.y) {
                    chart.options.scales.y.ticks.color = textSecondary;
                    chart.options.scales.y.grid.color = borderColor;
                }
                if (chart.options.scales.x) {
                    chart.options.scales.x.ticks.color = textSecondary;
                    chart.options.scales.x.grid.color = borderColor;
                }
            }
            
            chart.update();
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a dealership page
    if (window.location.pathname.startsWith('/dealership')) {
        initializeDashboard();
    }
});

// Ensure proper scrolling for all dealership pages
function ensureProperScrolling() {
    // Set proper scrolling for main container
    const dealershipContainer = document.querySelector('.dealership-container');
    if (dealershipContainer) {
        dealershipContainer.style.overflowY = 'auto';
        dealershipContainer.style.overflowX = 'hidden';
        dealershipContainer.style.height = '100vh';
    }
    
    // Set proper scrolling for main content
    const dealershipMain = document.querySelector('.dealership-main');
    if (dealershipMain) {
        dealershipMain.style.overflowY = 'auto';
        dealershipMain.style.overflowX = 'hidden';
        dealershipMain.style.maxHeight = 'calc(100vh - 120px)';
        dealershipMain.style.paddingBottom = '2rem';
    }
    
    // Set proper scrolling for content areas
    const contentAreas = document.querySelectorAll('.content-area, .main-content, .page-content');
    contentAreas.forEach(area => {
        area.style.overflowY = 'auto';
        area.style.overflowX = 'hidden';
        area.style.maxHeight = 'calc(100vh - 200px)';
    });
    
    // Set proper scrolling for tables
    const tableContainers = document.querySelectorAll('.table-container');
    tableContainers.forEach(container => {
        container.style.overflowX = 'auto';
        container.style.overflowY = 'auto';
        container.style.maxHeight = 'calc(100vh - 300px)';
    });
    
    console.log('✅ Proper scrolling ensured for dealership pages');
}

// Initialize navigation dropdown
function initializeNavigationDropdown() {
    const navDropdownToggle = document.getElementById('navDropdownToggle');
    const navDropdownMenu = document.getElementById('navDropdownMenu');
    
    if (navDropdownToggle && navDropdownMenu) {
        navDropdownToggle.addEventListener('click', function(event) {
            event.stopPropagation();
            toggleNavigationDropdown();
        });
        
        // Handle dropdown item clicks
        const dropdownItems = navDropdownMenu.querySelectorAll('.nav-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function() {
                // Update current page display
                const icon = this.querySelector('.nav-icon').textContent;
                const text = this.querySelector('.nav-text').textContent;
                
                const currentPageIcon = document.querySelector('.current-page-icon');
                const currentPageText = document.querySelector('.current-page-text');
                
                if (currentPageIcon) currentPageIcon.textContent = icon;
                if (currentPageText) currentPageText.textContent = text;
                
                // Close dropdown
                closeNavigationDropdown();
            });
        });
    }
}

// Toggle navigation dropdown
function toggleNavigationDropdown() {
    const navDropdownToggle = document.getElementById('navDropdownToggle');
    const navDropdownMenu = document.getElementById('navDropdownMenu');
    
    if (navDropdownToggle && navDropdownMenu) {
        const isActive = navDropdownMenu.classList.contains('active');
        
        if (isActive) {
            closeNavigationDropdown();
        } else {
            navDropdownMenu.classList.add('active');
            navDropdownToggle.classList.add('active');
        }
    }
}

// Close navigation dropdown
function closeNavigationDropdown() {
    const navDropdownToggle = document.getElementById('navDropdownToggle');
    const navDropdownMenu = document.getElementById('navDropdownMenu');
    
    if (navDropdownToggle && navDropdownMenu) {
        navDropdownMenu.classList.remove('active');
        navDropdownToggle.classList.remove('active');
    }
}

// Theme change observer
const themeObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
            updateChartsTheme();
        }
    });
});

// Start observing theme changes
themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
});

// Export functions for global access
window.dealershipManager = {
    searchVin,
    closeVinSearch,
    exportData,
    showNotification,
    applyFilters,
    createChart,
    formatDate,
    formatCurrency,
    formatVIN
};