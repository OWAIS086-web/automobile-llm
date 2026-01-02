// Analysis Dashboard JavaScript - Working Version

console.log('=== ANALYSIS.JS LOADED ===');

// Theme management
function loadTheme() {
    console.log('Loading theme...');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    }
    
    updateLogo(savedTheme);
    
    // Update charts theme if charts exist
    if (Object.keys(charts).length > 0) {
        console.log('Updating charts theme on load for:', savedTheme);
        updateChartsTheme(savedTheme);
    }
    
    console.log('Theme loaded:', savedTheme);
}

function toggleTheme() {
    console.log('Toggling theme...');
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
    }
    
    updateLogo(newTheme);
    updateChartsTheme(newTheme);
    console.log('Theme toggled to:', newTheme);
}

function updateLogo(theme) {
    const logo = document.getElementById('navLogo');
    if (logo) {
        const logoFile = theme === 'dark' ? 'light-logo.svg' : 'dark-logo.svg';
        logo.src = `/static/images/${logoFile}`;
        console.log('Logo updated for theme:', theme);
    }
}

function updateChartsTheme(theme) {
    const isDark = theme === 'dark';
    const colors = getChartColors(isDark);
    
    console.log('=== UPDATING CHARTS THEME WITH PURPLE COLORS ===');
    console.log('Theme:', theme, 'isDark:', isDark);
    console.log('Purple text color:', colors.text);
    console.log('Available charts:', Object.keys(charts));
    
    if (Object.keys(charts).length === 0) {
        console.log('No charts available to update');
        return;
    }
    
    Object.entries(charts).forEach(([chartName, chart]) => {
        if (!chart || !chart.options) {
            console.log(`Skipping ${chartName} - invalid chart object`);
            return;
        }
        
        console.log(`Updating ${chartName} chart with purple theme...`);
        
        try {
            // Update scales colors with purple theme
            if (chart.options.scales) {
                console.log(`Updating scales for ${chartName} with purple text`);
                if (chart.options.scales.x) {
                    chart.options.scales.x.ticks = chart.options.scales.x.ticks || {};
                    chart.options.scales.x.ticks.color = colors.text; // Purple text
                    chart.options.scales.x.ticks.font = chart.options.scales.x.ticks.font || {};
                    chart.options.scales.x.ticks.font.weight = '600';
                    chart.options.scales.x.grid = chart.options.scales.x.grid || {};
                    chart.options.scales.x.grid.color = colors.grid;
                    console.log(`X-axis updated: purple text=${colors.text}, grid=${colors.grid}`);
                }
                if (chart.options.scales.y) {
                    chart.options.scales.y.ticks = chart.options.scales.y.ticks || {};
                    chart.options.scales.y.ticks.color = colors.text; // Purple text
                    chart.options.scales.y.ticks.font = chart.options.scales.y.ticks.font || {};
                    chart.options.scales.y.ticks.font.weight = '600';
                    chart.options.scales.y.grid = chart.options.scales.y.grid || {};
                    chart.options.scales.y.grid.color = colors.grid;
                    console.log(`Y-axis updated: purple text=${colors.text}, grid=${colors.grid}`);
                }
            }
            
            // Update legend colors with purple theme
            if (chart.options.plugins && chart.options.plugins.legend) {
                console.log(`Updating legend for ${chartName} with purple text`);
                chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
                chart.options.plugins.legend.labels.color = colors.text; // Purple text
                chart.options.plugins.legend.labels.font = chart.options.plugins.legend.labels.font || {};
                chart.options.plugins.legend.labels.font.weight = '600';
                console.log(`Legend updated: purple color=${colors.text}`);
            }
            
            // Update tooltip colors with purple theme
            if (chart.options.plugins) {
                console.log(`Updating tooltip for ${chartName} with purple colors`);
                chart.options.plugins.tooltip = chart.options.plugins.tooltip || {};
                chart.options.plugins.tooltip.backgroundColor = colors.background;
                chart.options.plugins.tooltip.titleColor = colors.text; // Purple title
                chart.options.plugins.tooltip.bodyColor = colors.text; // Purple body text
                chart.options.plugins.tooltip.borderColor = colors.textSecondary || colors.text; // Purple border
                chart.options.plugins.tooltip.borderWidth = 2;
                console.log(`Tooltip updated: bg=${colors.background}, purple text=${colors.text}`);
            }
            
            // Force chart update with animation
            console.log(`Forcing update for ${chartName} with purple theme`);
            chart.update('active'); // Use 'active' for smooth animation
            console.log(`✅ ${chartName} chart updated with purple colors successfully`);
            
        } catch (error) {
            console.error(`❌ Error updating ${chartName} chart theme:`, error);
        }
    });
    
    console.log('=== ALL CHARTS UPDATED WITH PURPLE THEME ===');
}

// Chart colors with purple theme
function getChartColors(isDark) {
    return {
        primary: isDark ? '#6366f1' : '#4f46e5',
        secondary: isDark ? '#8b5cf6' : '#7c3aed',
        success: isDark ? '#10b981' : '#059669',
        warning: isDark ? '#f59e0b' : '#d97706',
        danger: isDark ? '#ef4444' : '#dc2626',
        info: isDark ? '#3b82f6' : '#2563eb',
        text: '#7c3aed', // Strong purple text that works on both light and dark backgrounds
        textSecondary: '#8b5cf6', // Lighter purple for secondary text
        grid: isDark ? '#4c1d95' : '#ddd6fe', // Purple-tinted grid
        background: isDark ? '#1a1a1a' : '#ffffff'
    };
}

let charts = {};

// Chart initialization
function initCharts() {
    console.log('=== INITIALIZING CHARTS ===');
    
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded!');
        showNotification('Chart.js library failed to load', 'error');
        return;
    }
    
    console.log('Chart.js available, version:', Chart.version || 'unknown');
    
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const colors = getChartColors(isDark);

    // Check data availability
    console.log('Data check:');
    console.log('- sentimentData:', typeof sentimentData !== 'undefined' ? sentimentData : 'undefined');
    console.log('- chatbotData:', typeof chatbotData !== 'undefined' ? chatbotData : 'undefined');
    console.log('- whatsappData:', typeof whatsappData !== 'undefined' ? whatsappData : 'undefined');
    console.log('- queriesData:', typeof queriesData !== 'undefined' ? queriesData : 'undefined');

    // Create charts with fallbacks
    createSentimentChart(colors);
    createChatbotChart(colors);
    createWhatsAppChart(colors);
    createQueriesChart(colors);
    
    console.log('Chart initialization complete. Created charts:', Object.keys(charts));
    showNotification('Charts loaded successfully!', 'success');
}

function createSentimentChart(colors) {
    const canvas = document.getElementById('sentimentChart');
    if (!canvas) return;
    
    let data, labels;
    if (typeof sentimentData !== 'undefined' && sentimentData && Object.keys(sentimentData).length > 0) {
        labels = Object.keys(sentimentData);
        data = Object.values(sentimentData);
        console.log('Creating sentiment chart with real data:', sentimentData);
    } else {
        labels = ['No Data Available'];
        data = [1];
        console.log('Creating sentiment chart with placeholder data');
    }
    
    try {
        charts.sentiment = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [colors.success, colors.warning, colors.danger, colors.info],
                    borderWidth: 2,
                    borderColor: colors.background
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: colors.text, // Purple text
                            padding: 15, 
                            font: { size: 12, weight: '600' } 
                        }
                    },
                    tooltip: {
                        backgroundColor: colors.background,
                        titleColor: colors.text, // Purple title
                        bodyColor: colors.text, // Purple body text
                        borderColor: colors.textSecondary, // Purple border
                        borderWidth: 2,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        console.log('✅ Sentiment chart created with purple theme');
    } catch (error) {
        console.error('❌ Error creating sentiment chart:', error);
    }
}

function createChatbotChart(colors) {
    const canvas = document.getElementById('chatbotChart');
    if (!canvas) return;
    
    let data, labels;
    if (typeof chatbotData !== 'undefined' && chatbotData && Object.keys(chatbotData).length > 0) {
        labels = Object.keys(chatbotData);
        data = Object.values(chatbotData);
        console.log('Creating chatbot chart with real data:', chatbotData);
    } else {
        labels = ['No Data'];
        data = [0];
        console.log('Creating chatbot chart with placeholder data');
    }
    
    try {
        charts.chatbot = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Queries',
                    data: data,
                    backgroundColor: colors.primary,
                    borderColor: colors.primary,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { 
                        ticks: { 
                            color: colors.text, // Purple text
                            font: { weight: '600' }
                        }, 
                        grid: { color: colors.grid } 
                    },
                    y: { 
                        ticks: { 
                            color: colors.text, // Purple text
                            font: { weight: '600' }
                        }, 
                        grid: { color: colors.grid } 
                    }
                },
                plugins: {
                    legend: { 
                        display: false 
                    },
                    tooltip: {
                        backgroundColor: colors.background,
                        titleColor: colors.text, // Purple title
                        bodyColor: colors.text, // Purple body text
                        borderColor: colors.textSecondary, // Purple border
                        borderWidth: 2
                    }
                }
            }
        });
        console.log('✅ Chatbot chart created with purple theme');
    } catch (error) {
        console.error('❌ Error creating chatbot chart:', error);
    }
}
function createWhatsAppChart(colors) {
    const canvas = document.getElementById('whatsappChart');
    if (!canvas) return;
    
    let data, labels;
    if (typeof whatsappData !== 'undefined' && whatsappData && Object.keys(whatsappData).length > 0) {
        labels = Object.keys(whatsappData);
        data = Object.values(whatsappData);
        console.log('Creating WhatsApp chart with real data:', whatsappData);
    } else {
        console.log('WhatsApp chart canvas found but no data available');
        return; // Skip if no data
    }
    
    try {
        charts.whatsapp = new Chart(canvas, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [colors.success, colors.danger, colors.info],
                    borderWidth: 2,
                    borderColor: colors.background
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: colors.text, // Purple text
                            padding: 15, 
                            font: { size: 12, weight: '600' } 
                        }
                    },
                    tooltip: {
                        backgroundColor: colors.background,
                        titleColor: colors.text, // Purple title
                        bodyColor: colors.text, // Purple body text
                        borderColor: colors.textSecondary, // Purple border
                        borderWidth: 2,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        console.log('✅ WhatsApp chart created with purple theme');
    } catch (error) {
        console.error('❌ Error creating WhatsApp chart:', error);
    }
}

function createQueriesChart(colors) {
    const canvas = document.getElementById('queriesChart');
    if (!canvas) return;
    
    let data, labels;
    if (typeof queriesData !== 'undefined' && queriesData && Array.isArray(queriesData) && queriesData.length > 0) {
        labels = queriesData.map(q => q.query.substring(0, 30) + '...');
        data = queriesData.map(q => q.count);
        console.log('Creating queries chart with real data:', queriesData);
    } else {
        labels = ['No Data'];
        data = [0];
        console.log('Creating queries chart with placeholder data');
    }
    
    try {
        charts.queries = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Frequency',
                    data: data,
                    backgroundColor: colors.secondary,
                    borderColor: colors.secondary,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: { 
                        ticks: { 
                            color: colors.text, // Purple text
                            font: { weight: '600' }
                        }, 
                        grid: { color: colors.grid } 
                    },
                    y: { 
                        ticks: { 
                            color: colors.text, // Purple text
                            font: { size: 10, weight: '600' } 
                        }, 
                        grid: { display: false } 
                    }
                },
                plugins: {
                    legend: { 
                        display: false 
                    },
                    tooltip: {
                        backgroundColor: colors.background,
                        titleColor: colors.text, // Purple title
                        bodyColor: colors.text, // Purple body text
                        borderColor: colors.textSecondary, // Purple border
                        borderWidth: 2,
                        callbacks: {
                            title: function(context) {
                                if (typeof queriesData !== 'undefined' && queriesData && queriesData[context[0].dataIndex]) {
                                    return queriesData[context[0].dataIndex].query;
                                }
                                return context[0].label;
                            }
                        }
                    }
                }
            }
        });
        console.log('✅ Queries chart created with purple theme');
    } catch (error) {
        console.error('❌ Error creating queries chart:', error);
    }
}
// Date filtering functions
function applyDateFilter() {
    const dateFrom = document.getElementById('dateFrom')?.value;
    const dateTo = document.getElementById('dateTo')?.value;
    
    console.log('Applying date filter:', { dateFrom, dateTo });
    
    // Validate date inputs
    if (!dateFrom && !dateTo) {
        showNotification('Please select at least one date (From or To)', 'warning');
        return;
    }
    
    if (dateFrom && dateTo && dateFrom > dateTo) {
        showNotification('Start date cannot be after end date', 'error');
        return;
    }
    
    // Show loading notification
    showNotification('Applying date filter...', 'info');
    
    // Apply filter to both complaints and charts
    filterDataByDate(dateFrom, dateTo);
    
    // Fetch updated data from server
    fetchFilteredDataFromServer(dateFrom, dateTo);
}

function clearDateFilter() {
    console.log('Clearing date filter...');
    const dateFromInput = document.getElementById('dateFrom');
    const dateToInput = document.getElementById('dateTo');
    
    if (dateFromInput) dateFromInput.value = '';
    if (dateToInput) dateToInput.value = '';
    
    // Clear filter from both complaints and charts
    filterDataByDate('', '');
    
    // Fetch all data from server (no date filter)
    fetchFilteredDataFromServer('', '');
    
    showNotification('Date filter cleared', 'success');
}

// Fetch filtered data from server
function fetchFilteredDataFromServer(dateFrom, dateTo) {
    console.log('Fetching filtered data from server...');
    
    // Build URL with date parameters
    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    const url = `/analysis?${params.toString()}`;
    
    // Show loading state
    showNotification('Loading filtered analytics data...', 'info');
    
    // Try AJAX first, fallback to page reload
    fetch(url, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            // If HTML response, reload the page with new parameters
            console.log('Received HTML response, reloading page with parameters');
            window.location.href = url;
            return null;
        }
    })
    .then(data => {
        if (data) {
            console.log('Received filtered data:', data);
            
            if (data.success) {
                updateChartsWithServerData(data);
                showNotification('Analytics data updated successfully!', 'success');
            } else {
                throw new Error(data.message || 'Server returned error');
            }
        }
    })
    .catch(error => {
        console.error('Error fetching filtered data:', error);
        
        // Fallback: reload page with date parameters
        console.log('Falling back to page reload with parameters');
        showNotification('Reloading page with filtered data...', 'info');
        
        setTimeout(() => {
            window.location.href = url;
        }, 1000);
    });
}

// Update charts with server data
function updateChartsWithServerData(data) {
    console.log('=== UPDATING CHARTS WITH SERVER DATA ===');
    
    try {
        // Update sentiment chart if data available
        if (data.sentiment_analysis && charts.sentiment) {
            const sentimentData = data.sentiment_analysis;
            console.log('Updating sentiment chart with:', sentimentData);
            
            if (Object.keys(sentimentData).length > 0) {
                charts.sentiment.data.labels = Object.keys(sentimentData);
                charts.sentiment.data.datasets[0].data = Object.values(sentimentData);
            } else {
                charts.sentiment.data.labels = ['No Data for Selected Period'];
                charts.sentiment.data.datasets[0].data = [1];
            }
            charts.sentiment.update('active');
        }
        
        // Update chatbot chart if data available
        if (data.chatbot_usage && charts.chatbot) {
            const chatbotData = data.chatbot_usage;
            console.log('Updating chatbot chart with:', chatbotData);
            
            if (Object.keys(chatbotData).length > 0) {
                charts.chatbot.data.labels = Object.keys(chatbotData);
                charts.chatbot.data.datasets[0].data = Object.values(chatbotData);
            } else {
                charts.chatbot.data.labels = ['No Data'];
                charts.chatbot.data.datasets[0].data = [0];
            }
            charts.chatbot.update('active');
        }
        
        // Update WhatsApp chart if data available
        if (data.whatsapp_stats && data.whatsapp_stats.message_types && charts.whatsapp) {
            const whatsappData = data.whatsapp_stats.message_types;
            console.log('Updating WhatsApp chart with:', whatsappData);
            
            charts.whatsapp.data.labels = Object.keys(whatsappData);
            charts.whatsapp.data.datasets[0].data = Object.values(whatsappData);
            charts.whatsapp.update('active');
        }
        
        // Update queries chart if data available
        if (data.popular_queries && charts.queries) {
            const queriesData = data.popular_queries;
            console.log('Updating queries chart with:', queriesData);
            
            if (Array.isArray(queriesData) && queriesData.length > 0) {
                charts.queries.data.labels = queriesData.map(q => q.query.substring(0, 30) + '...');
                charts.queries.data.datasets[0].data = queriesData.map(q => q.count);
            } else {
                charts.queries.data.labels = ['No Data'];
                charts.queries.data.datasets[0].data = [0];
            }
            charts.queries.update('active');
        }
        
        // Update stats cards
        updateStatsCardsWithServerData(data);
        
        console.log('✅ All charts updated with server data');
        
    } catch (error) {
        console.error('Error updating charts with server data:', error);
        showNotification('Error updating charts with filtered data', 'error');
    }
}

// Update stats cards with server data
function updateStatsCardsWithServerData(data) {
    try {
        // Update total posts
        if (data.total_posts !== undefined) {
            const totalPostsCard = document.querySelector('.stat-card:nth-child(1) .stat-value');
            if (totalPostsCard) {
                totalPostsCard.textContent = data.total_posts;
            }
        }
        
        // Update WhatsApp messages
        if (data.whatsapp_stats && data.whatsapp_stats.total_messages !== undefined) {
            const whatsappCard = document.querySelector('.stat-card:nth-child(2) .stat-value');
            if (whatsappCard) {
                whatsappCard.textContent = data.whatsapp_stats.total_messages;
            }
        }
        
        // Update chatbot interactions
        if (data.chatbot_usage) {
            const chatbotTotal = Object.values(data.chatbot_usage).reduce((sum, val) => sum + val, 0);
            const chatbotCard = document.querySelector('.stat-card:nth-child(3) .stat-value');
            if (chatbotCard) {
                chatbotCard.textContent = chatbotTotal;
            }
        }
        
        // Update total complaints
        const pakwheelsCount = data.pakwheels_complaints ? data.pakwheels_complaints.length : 0;
        const whatsappCount = data.whatsapp_complaints ? data.whatsapp_complaints.length : 0;
        const totalComplaints = pakwheelsCount + whatsappCount;
        
        const complaintsCard = document.querySelector('.stat-card:nth-child(4) .stat-value');
        if (complaintsCard) {
            complaintsCard.textContent = totalComplaints;
        }
        
        // Update sentiment stats
        if (data.sentiment_analysis) {
            const positiveCard = document.querySelector('.stat-card:nth-child(5) .stat-value');
            const negativeCard = document.querySelector('.stat-card:nth-child(6) .stat-value');
            
            if (positiveCard) {
                positiveCard.textContent = data.sentiment_analysis.positive || 0;
            }
            if (negativeCard) {
                negativeCard.textContent = data.sentiment_analysis.negative || 0;
            }
        }
        
        console.log('✅ Stats cards updated with server data');
        
    } catch (error) {
        console.error('Error updating stats cards:', error);
    }
}

function filterDataByDate(dateFrom, dateTo) {
    try {
        const complaintItems = document.querySelectorAll('.complaint-item');
        let visibleCount = 0;
        
        console.log('Filtering', complaintItems.length, 'complaint items');
        
        const fromDate = dateFrom ? new Date(dateFrom) : null;
        const toDate = dateTo ? new Date(dateTo) : null;
        
        complaintItems.forEach((item, index) => {
            let shouldShow = true;
            const dateAttr = item.getAttribute('data-date');
            
            if (dateAttr && (fromDate || toDate)) {
                const itemDate = parseItemDate(dateAttr);
                
                if (itemDate) {
                    if (fromDate && itemDate < fromDate) {
                        shouldShow = false;
                    }
                    if (toDate && itemDate > toDate) {
                        shouldShow = false;
                    }
                }
            }
            
            if (shouldShow) {
                visibleCount++;
                item.style.display = '';
                item.style.opacity = '1';
            } else {
                item.style.display = 'none';
            }
        });
        
        const message = dateFrom || dateTo ? 
            `Date filter applied - showing ${visibleCount} items` : 
            `Showing all ${visibleCount} items`;
        showNotification(message, 'success');
        
    } catch (error) {
        console.error('Error filtering data:', error);
        showNotification('Error applying date filter', 'error');
    }
}

function parseItemDate(dateStr) {
    try {
        if (!dateStr) return null;
        
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) {
            return null;
        }
        
        date.setHours(0, 0, 0, 0);
        return date;
    } catch (error) {
        return null;
    }
}

// Update charts with date-filtered data
function updateChartsWithDateFilter(dateFrom, dateTo) {
    console.log('=== UPDATING CHARTS WITH DATE FILTER ===');
    console.log('Date range:', { dateFrom, dateTo });
    
    const fromDate = dateFrom ? new Date(dateFrom) : null;
    const toDate = dateTo ? new Date(dateTo) : null;
    
    // Filter complaint data for charts
    const filteredComplaints = getFilteredComplaints(fromDate, toDate);
    console.log('Filtered complaints:', filteredComplaints);
    
    // Update sentiment analysis based on filtered data
    updateSentimentChart(filteredComplaints);
    
    // Update stats cards with filtered data
    updateStatsCards(filteredComplaints);
    
    console.log('=== CHARTS UPDATED WITH FILTERED DATA ===');
}

function getFilteredComplaints(fromDate, toDate) {
    const complaintItems = document.querySelectorAll('.complaint-item');
    const filteredComplaints = [];
    
    complaintItems.forEach(item => {
        const dateAttr = item.getAttribute('data-date');
        const complaintText = item.querySelector('.complaint-text')?.textContent || '';
        const complaintAuthor = item.querySelector('.complaint-author')?.textContent || '';
        
        let shouldInclude = true;
        
        if (dateAttr && (fromDate || toDate)) {
            const itemDate = parseItemDate(dateAttr);
            
            if (itemDate) {
                if (fromDate && itemDate < fromDate) {
                    shouldInclude = false;
                }
                if (toDate && itemDate > toDate) {
                    shouldInclude = false;
                }
            }
        }
        
        if (shouldInclude) {
            filteredComplaints.push({
                date: dateAttr,
                text: complaintText,
                author: complaintAuthor,
                sentiment: analyzeSentiment(complaintText)
            });
        }
    });
    
    return filteredComplaints;
}

function analyzeSentiment(text) {
    // Simple sentiment analysis based on keywords
    const positiveWords = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'wonderful', 'fantastic', 'awesome', 'satisfied', 'happy', 'pleased'];
    const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'worst', 'disappointed', 'angry', 'frustrated', 'problem', 'issue', 'broken', 'defect', 'fault'];
    
    const lowerText = text.toLowerCase();
    let positiveCount = 0;
    let negativeCount = 0;
    
    positiveWords.forEach(word => {
        if (lowerText.includes(word)) positiveCount++;
    });
    
    negativeWords.forEach(word => {
        if (lowerText.includes(word)) negativeCount++;
    });
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
}

function updateSentimentChart(filteredComplaints) {
    const sentimentChart = charts.sentiment;
    if (!sentimentChart) return;
    
    // Calculate sentiment distribution from filtered complaints
    const sentimentCounts = {
        positive: 0,
        negative: 0,
        neutral: 0
    };
    
    filteredComplaints.forEach(complaint => {
        sentimentCounts[complaint.sentiment]++;
    });
    
    console.log('Updated sentiment counts:', sentimentCounts);
    
    // Update chart data
    if (Object.values(sentimentCounts).some(count => count > 0)) {
        sentimentChart.data.labels = Object.keys(sentimentCounts).map(key => 
            key.charAt(0).toUpperCase() + key.slice(1)
        );
        sentimentChart.data.datasets[0].data = Object.values(sentimentCounts);
    } else {
        // No data for this date range
        sentimentChart.data.labels = ['No Data for Selected Period'];
        sentimentChart.data.datasets[0].data = [1];
    }
    
    sentimentChart.update('active');
    console.log('✅ Sentiment chart updated with filtered data');
}

function updateStatsCards(filteredComplaints) {
    // Update complaint count in stats
    const totalComplaintsCard = document.querySelector('.stat-card:nth-child(4) .stat-value');
    if (totalComplaintsCard) {
        totalComplaintsCard.textContent = filteredComplaints.length;
    }
    
    // Update sentiment-based stats
    const sentimentCounts = {
        positive: 0,
        negative: 0,
        neutral: 0
    };
    
    filteredComplaints.forEach(complaint => {
        sentimentCounts[complaint.sentiment]++;
    });
    
    // Update positive posts count
    const positiveCard = document.querySelector('.stat-card:nth-child(5) .stat-value');
    if (positiveCard) {
        positiveCard.textContent = sentimentCounts.positive;
    }
    
    // Update negative posts count
    const negativeCard = document.querySelector('.stat-card:nth-child(6) .stat-value');
    if (negativeCard) {
        negativeCard.textContent = sentimentCounts.negative;
    }
    
    console.log('✅ Stats cards updated with filtered data');
}
// Utility functions
function downloadChart(chartId) {
    const canvas = document.getElementById(chartId);
    if (canvas) {
        const a = document.createElement('a');
        a.href = canvas.toDataURL('image/png');
        a.download = `${chartId}-${Date.now()}.png`;
        a.click();
        showNotification('Chart downloaded!', 'success');
    }
}

function generateReport() {
    showNotification('Generating comprehensive PDF report with charts...', 'info');
    
    // Get current date filter values
    const dateFrom = document.getElementById('dateFrom')?.value;
    const dateTo = document.getElementById('dateTo')?.value;
    
    // Build request data for PDF generation
    const requestData = {
        date_from: dateFrom,
        date_to: dateTo,
        include_charts: true,
        format: 'pdf'
    };
    
    console.log('Requesting PDF report with data:', requestData);
    
    fetch('/generate_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('Report response status:', response.status);
        console.log('Report response content-type:', response.headers.get('content-type'));
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/pdf')) {
            // Handle PDF response
            console.log('Received PDF response, downloading...');
            return response.blob().then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Generate filename with company and date
                const companyName = (window.companyName || 'Company').replace(/\s+/g, '_');
                const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
                const dateRange = dateFrom && dateTo ? `_${dateFrom}_to_${dateTo}` : '';
                
                a.download = `${companyName}_Analytics_Report${dateRange}_${timestamp}.pdf`;
                a.click();
                URL.revokeObjectURL(url);
                
                showNotification('PDF report with charts generated and downloaded successfully!', 'success');
            });
        } else {
            // Handle JSON response (fallback)
            console.log('Received JSON response, falling back to text report');
            return response.json().then(data => {
                if (data.success) {
                    generateClientSideReport(data);
                    showNotification('Report generated (text format - PDF generation failed)', 'warning');
                } else {
                    throw new Error(data.message || 'Report generation failed');
                }
            });
        }
    })
    .catch(error => {
        console.error('Error generating PDF report:', error);
        
        // Fallback to client-side report generation
        console.log('Falling back to client-side text report generation');
        generateClientSideReport();
        showNotification('Report generated in text format (PDF generation unavailable)', 'warning');
    });
}

function generateClientSideReport(serverData = null) {
    console.log('Generating client-side report...');
    
    const dateFrom = document.getElementById('dateFrom')?.value;
    const dateTo = document.getElementById('dateTo')?.value;
    const companyName = typeof window.companyName !== 'undefined' ? window.companyName : 'Unknown Company';
    const selectedCompany = typeof window.selectedCompany !== 'undefined' ? window.selectedCompany : 'haval';
    
    // Get current stats from the page
    const totalPosts = document.querySelector('.stat-card:nth-child(1) .stat-value')?.textContent || '0';
    const whatsappMessages = document.querySelector('.stat-card:nth-child(2) .stat-value')?.textContent || '0';
    const chatbotInteractions = document.querySelector('.stat-card:nth-child(3) .stat-value')?.textContent || '0';
    const totalComplaints = document.querySelector('.stat-card:nth-child(4) .stat-value')?.textContent || '0';
    const positivePosts = document.querySelector('.stat-card:nth-child(5) .stat-value')?.textContent || '0';
    const negativePosts = document.querySelector('.stat-card:nth-child(6) .stat-value')?.textContent || '0';
    
    // Build report content based on company
    let reportContent = `INSIGHTS AI ANALYTICS REPORT
========================================

Company: ${companyName}
Generated: ${new Date().toLocaleString()}
Report Period: ${dateFrom || 'All Time'} to ${dateTo || 'Present'}
Report Type: ${selectedCompany === 'haval' ? 'Comprehensive (Posts + WhatsApp)' : 'Posts Analysis'}

========================================
EXECUTIVE SUMMARY
========================================

Total Forum Posts Analyzed: ${totalPosts}`;

    if (selectedCompany === 'haval') {
        reportContent += `
Total WhatsApp Messages: ${whatsappMessages}`;
    }

    reportContent += `
Total Chatbot Interactions: ${chatbotInteractions}
Total Complaints Identified: ${totalComplaints}

Sentiment Analysis:
- Positive Posts: ${positivePosts}
- Negative Posts: ${negativePosts}
- Sentiment Ratio: ${calculateSentimentRatio(positivePosts, negativePosts)}

========================================
DETAILED ANALYTICS
========================================

1. FORUM ANALYSIS
   - Total posts processed: ${totalPosts}
   - Chatbot interactions: ${chatbotInteractions}
   - Complaint detection rate: ${calculateComplaintRate(totalComplaints, totalPosts)}%`;

    if (selectedCompany === 'haval') {
        reportContent += `

2. WHATSAPP ANALYSIS
   - Total messages processed: ${whatsappMessages}
   - Message types analyzed: Complaints, Queries, General Chat
   - Integration status: Active`;
    }

    reportContent += `

3. SENTIMENT INSIGHTS
   - Positive sentiment: ${positivePosts} posts (${calculatePercentage(positivePosts, totalPosts)}%)
   - Negative sentiment: ${negativePosts} posts (${calculatePercentage(negativePosts, totalPosts)}%)
   - Overall sentiment trend: ${getSentimentTrend(positivePosts, negativePosts)}

4. COMPLAINT ANALYSIS
   - Total complaints identified: ${totalComplaints}
   - Sources: ${selectedCompany === 'haval' ? 'PakWheels Forums + WhatsApp' : 'PakWheels Forums'}
   - Resolution tracking: Available in dashboard

========================================
RECOMMENDATIONS
========================================

Based on the analysis period ${dateFrom || 'all time'} to ${dateTo || 'present'}:

1. Customer Satisfaction:
   ${getCustomerSatisfactionRecommendation(positivePosts, negativePosts)}

2. Complaint Management:
   ${getComplaintRecommendation(totalComplaints, totalPosts)}`;

    if (selectedCompany === 'haval') {
        reportContent += `

3. WhatsApp Integration:
   ${getWhatsAppRecommendation(whatsappMessages)}`;
    }

    reportContent += `

4. Chatbot Performance:
   ${getChatbotRecommendation(chatbotInteractions)}

========================================
TECHNICAL DETAILS
========================================

Data Sources:
- PakWheels Forum Posts: ${totalPosts} entries`;

    if (selectedCompany === 'haval') {
        reportContent += `
- WhatsApp Messages: ${whatsappMessages} entries`;
    }

    reportContent += `
- AI Processing: Sentiment Analysis, Topic Extraction, Complaint Detection
- Date Range: ${dateFrom || 'Inception'} - ${dateTo || 'Current'}
- Generated By: Insights AI Analytics Platform
- Report Format: Comprehensive Analytics Summary

========================================
CHART DATA SUMMARY
========================================

Note: Visual charts are available in the dashboard at:
${window.location.origin}/analysis

For detailed visual analysis, please refer to the interactive dashboard.

========================================
END OF REPORT
========================================

Generated by Insights AI Analytics Platform
© ${new Date().getFullYear()} - Advanced Analytics & Business Intelligence`;

    // Create and download the report
    const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyName.replace(/\s+/g, '_')}_Analytics_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// Helper functions for report generation
function calculateSentimentRatio(positive, negative) {
    const pos = parseInt(positive) || 0;
    const neg = parseInt(negative) || 0;
    
    if (pos + neg === 0) return 'No data available';
    
    const ratio = pos / (pos + neg);
    if (ratio > 0.7) return 'Highly Positive';
    if (ratio > 0.5) return 'Positive';
    if (ratio > 0.3) return 'Mixed';
    return 'Negative';
}

function calculateComplaintRate(complaints, total) {
    const comp = parseInt(complaints) || 0;
    const tot = parseInt(total) || 0;
    
    if (tot === 0) return 0;
    return ((comp / tot) * 100).toFixed(1);
}

function calculatePercentage(value, total) {
    const val = parseInt(value) || 0;
    const tot = parseInt(total) || 0;
    
    if (tot === 0) return 0;
    return ((val / tot) * 100).toFixed(1);
}

function getSentimentTrend(positive, negative) {
    const pos = parseInt(positive) || 0;
    const neg = parseInt(negative) || 0;
    
    if (pos > neg * 2) return 'Strongly Positive';
    if (pos > neg) return 'Positive';
    if (neg > pos * 2) return 'Concerning - High Negativity';
    return 'Neutral/Mixed';
}

function getCustomerSatisfactionRecommendation(positive, negative) {
    const pos = parseInt(positive) || 0;
    const neg = parseInt(negative) || 0;
    
    if (pos > neg * 2) {
        return 'Excellent customer satisfaction levels. Continue current strategies and consider expanding successful initiatives.';
    } else if (pos > neg) {
        return 'Good customer satisfaction with room for improvement. Focus on addressing negative feedback patterns.';
    } else {
        return 'Customer satisfaction needs attention. Implement immediate action plan to address negative sentiment drivers.';
    }
}

function getComplaintRecommendation(complaints, total) {
    const rate = parseFloat(calculateComplaintRate(complaints, total));
    
    if (rate < 5) {
        return 'Low complaint rate indicates good product/service quality. Maintain current standards.';
    } else if (rate < 15) {
        return 'Moderate complaint rate. Monitor trends and implement proactive customer service improvements.';
    } else {
        return 'High complaint rate requires immediate attention. Conduct root cause analysis and implement corrective measures.';
    }
}

function getWhatsAppRecommendation(messages) {
    const msg = parseInt(messages) || 0;
    
    if (msg > 1000) {
        return 'High WhatsApp engagement. Consider expanding support team and implementing automated responses for common queries.';
    } else if (msg > 100) {
        return 'Good WhatsApp adoption. Optimize response times and consider adding more self-service options.';
    } else {
        return 'Low WhatsApp usage. Promote the channel and ensure customers are aware of this support option.';
    }
}

function getChatbotRecommendation(interactions) {
    const inter = parseInt(interactions) || 0;
    
    if (inter > 500) {
        return 'High chatbot usage indicates good adoption. Analyze conversation patterns to improve responses and add new capabilities.';
    } else if (inter > 100) {
        return 'Moderate chatbot engagement. Consider improving discoverability and expanding the knowledge base.';
    } else {
        return 'Low chatbot usage. Review placement, improve initial prompts, and ensure the bot provides valuable responses.';
    }
}

function refreshData() {
    showNotification('Refreshing data...', 'info');
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// Notification system
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
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
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        z-index: 1001;
        font-weight: 600;
        font-size: 14px;
        max-width: 350px;
        font-family: 'Inter', sans-serif;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

function getNotificationColor(type) {
    switch (type) {
        case 'success': return 'linear-gradient(135deg, #10b981, #059669)';
        case 'error': return 'linear-gradient(135deg, #ef4444, #dc2626)';
        case 'warning': return 'linear-gradient(135deg, #f59e0b, #d97706)';
        case 'info': return 'linear-gradient(135deg, #6366f1, #4f46e5)';
        default: return 'linear-gradient(135deg, #6366f1, #4f46e5)';
    }
}
// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('=== ANALYSIS DASHBOARD INITIALIZATION ===');
    
    loadTheme();
    
    // Initialize date filter from URL parameters
    initializeDateFilterFromURL();
    
    // Wait for Chart.js to be available
    if (typeof Chart !== 'undefined') {
        initCharts();
        console.log('Charts initialized immediately');
        
        // Apply theme to charts after a short delay to ensure they're fully created
        setTimeout(() => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
            updateChartsTheme(currentTheme);
        }, 500);
    } else {
        let attempts = 0;
        const checkChart = setInterval(() => {
            attempts++;
            if (typeof Chart !== 'undefined') {
                clearInterval(checkChart);
                initCharts();
                console.log('Charts initialized after waiting');
                
                // Apply theme to charts after initialization
                setTimeout(() => {
                    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
                    updateChartsTheme(currentTheme);
                }, 500);
            } else if (attempts > 50) {
                clearInterval(checkChart);
                console.error('Chart.js failed to load');
                showNotification('Charts failed to load. Please refresh.', 'error');
            }
        }, 100);
    }
    
    setTimeout(() => {
        showNotification('Dashboard loaded successfully!', 'success');
    }, 1000);
    
    console.log('Initialization complete');
});

// Manual function to refresh chart themes (can be called from console for debugging)
function refreshChartThemes() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    console.log('Manually refreshing chart themes for:', currentTheme);
    updateChartsTheme(currentTheme);
    showNotification(`Chart themes refreshed for ${currentTheme} mode`, 'info');
}

// Debug function to check chart status
function debugCharts() {
    console.log('=== CHART DEBUG INFO ===');
    console.log('Available charts:', Object.keys(charts));
    console.log('Current theme:', document.documentElement.getAttribute('data-theme'));
    
    Object.entries(charts).forEach(([name, chart]) => {
        console.log(`Chart ${name}:`, {
            exists: !!chart,
            hasOptions: !!(chart && chart.options),
            hasScales: !!(chart && chart.options && chart.options.scales),
            hasPlugins: !!(chart && chart.options && chart.options.plugins)
        });
        
        if (chart && chart.options) {
            console.log(`${name} scales:`, chart.options.scales);
            console.log(`${name} plugins:`, chart.options.plugins);
        }
    });
    
    console.log('=== END CHART DEBUG ===');
}

// Add debug buttons (only in development)
function addDebugButtons() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const debugContainer = document.createElement('div');
        debugContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            z-index: 9999;
            display: flex;
            gap: 10px;
        `;
        
        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh Chart Themes';
        refreshBtn.style.cssText = `
            padding: 8px 12px;
            background: #6366f1;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        refreshBtn.onclick = refreshChartThemes;
        
        const debugBtn = document.createElement('button');
        debugBtn.textContent = 'Debug Charts';
        debugBtn.style.cssText = `
            padding: 8px 12px;
            background: #8b5cf6;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        `;
        debugBtn.onclick = debugCharts;
        
        debugContainer.appendChild(refreshBtn);
        debugContainer.appendChild(debugBtn);
        document.body.appendChild(debugContainer);
        
        console.log('Debug buttons added to page');
    }
}

// Initialize date filter from URL parameters
function initializeDateFilterFromURL() {
    const params = new URLSearchParams(window.location.search);
    const dateFrom = params.get('date_from');
    const dateTo = params.get('date_to');
    
    console.log('Initializing date filter from URL:', { dateFrom, dateTo });
    
    if (dateFrom) {
        const dateFromInput = document.getElementById('dateFrom');
        if (dateFromInput) {
            dateFromInput.value = dateFrom;
        }
    }
    
    if (dateTo) {
        const dateToInput = document.getElementById('dateTo');
        if (dateToInput) {
            dateToInput.value = dateTo;
        }
    }
    
    // Show notification if date filter is active
    if (dateFrom || dateTo) {
        setTimeout(() => {
            const dateRange = `${dateFrom || 'start'} to ${dateTo || 'end'}`;
            showNotification(`Date filter active: ${dateRange}`, 'info');
        }, 2000);
    }
}

console.log('=== ANALYSIS.JS SCRIPT END ===');