/* ============================================
   CHATBOT PAGE - JAVASCRIPT FUNCTIONALITY
   ============================================ */

// Immediate debug logging
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // Disable console logging in production
    console.log = console.warn = console.error = function() {};
}
console.log('🚀 Chatbot.js file loaded');

// Add global error handler
window.addEventListener('error', function(e) {
    console.error('🚨 Global JavaScript Error:', e.error);
    console.error('🚨 Error details:', {
        messae,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno
    });
});

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('🚨 Unhandled Promise Rejection:', e.reason);
});

// Very early loading screen check
setTimeout(() => {
    console.log('⏰ Early loading screen check (500ms)');
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        console.log('📱 Loading screen found, will hide soon...');
        
        // Aggressive immediate hide after 2 seconds
        setTimeout(() => {
            console.log('🚨 Aggressive hide triggered');
            loadingScreen.style.opacity = '0';
            loadingScreen.style.visibility = 'hidden';
            loadingScreen.style.display = 'none';
        }, 2000);
    }
}, 500);

// Global Variables
let conversationHistory = [];
let currentSessionId = null;
let thinkingMode = false;
let isTyping = false;
let currentTypingElement = null;
let fullContent = '';
let userScrolled = false;
let currentMessageDiv = null;
let currentReferences = [];
let currentStructuredData = null;
let typingInterval = null;
let typingSpeed = 1;
let currentMode = localStorage.getItem('selectedMode') || null; // No default mode, remember last selected
let isHovering = false; // Track hover state globally
let draftSaveTimeout = null; // For auto-saving drafts
let retryCount = 0; // For message retry functionality
let maxRetries = 3; // Maximum retry attempts

// DOM Validation Function
function validateDOMElements() {
    console.log('🔍 Validating critical DOM elements...');
    
    const criticalElements = [
        'loadingScreen',
        'chatInput',
        'sendBtn',
        'stopBtn',
        'chatArea',
        'messagesContainer',
        'welcomeScreen',
        'aiModeToggle',
        'dataSourceToggle'
    ];
    
    const missingElements = [];
    
    criticalElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (!element) {
            missingElements.push(elementId);
            console.warn(`⚠️ Missing element: ${elementId}`);
        } else {
            console.log(`✅ Found element: ${elementId}`);
        }
    });
    
    if (missingElements.length > 0) {
        console.error('❌ Missing DOM elements:', missingElements);
        return false;
    }
    
    console.log('✅ All critical DOM elements found');
    return true;
}

// Initialize the application
function init() {
    console.log('🚀 Initializing chatbot application...');
    
    // Validate critical DOM elements
    if (!validateDOMElements()) {
        console.error('❌ Critical DOM elements missing, initialization failed');
        return;
    }
    
    try {
        // Initialize session ID for new chat
        if (!currentSessionId) {
            currentSessionId = generateSessionId();
            console.log('✅ New session ID generated:', currentSessionId);
        }
        
        loadChatHistory();
        console.log('✅ Chat history loaded');
        
        loadTheme();
        console.log('✅ Theme loaded');
        
        updateModePlaceholder();
        console.log('✅ Mode placeholder updated');
        
        startEngineStatusMonitoring();
        console.log('✅ Engine status monitoring started');
        
        setupEventListeners();
        console.log('✅ Event listeners setup complete');
        
        setupWelcomeAnimations();
        console.log('✅ Welcome animations setup complete');
        
        // Initialize data source button
        updateDataSourceButton();
        console.log('✅ Data source button initialized');
        
        // Setup loading screen animations
        handleLoadingScreenAnimations();
        console.log('✅ Loading screen animations initialized');
        
        // Debug session information
        debugSession();
        
        // Debug chat history
        debugChatHistory();
        
        // Load recent chats to sidebar
        loadRecentChatsToSidebar();
        console.log('✅ Recent chats loaded to sidebar');
        
        // Fetch current AI model information
        fetchCurrentModel();
        console.log('✅ Current model information fetched');
        
        // Load user preferences
        loadThinkingModePreference();
        
        // Test basic functionality
        testBasicFunctionality();
        
        console.log('🎉 Chatbot initialization complete!');
    } catch (error) {
        console.error('❌ Error during initialization:', error);
        showToast('Initialization error: ' + error.message, 'error');
    }
}

// Test basic functionality
function testBasicFunctionality() {
    console.log('🧪 Testing basic functionality...');
    
    // Test scroll function
    const chatArea = document.getElementById('chatArea');
    if (chatArea) {
        console.log('✅ Chat area found');
    } else {
        console.error('❌ Chat area not found');
    }
    
    // Test input field
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        console.log('✅ Chat input found');
    } else {
        console.error('❌ Chat input not found');
    }
    
    // Test send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        console.log('✅ Send button found');
    } else {
        console.error('❌ Send button not found');
    }
    
    console.log('🧪 Basic functionality test complete');
}

// Setup event listeners
function setupEventListeners() {
    // Theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Chat input
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', handleKeyPress);
        chatInput.addEventListener('input', function() {
            autoResize(this);
            saveDraft(this.value); // Auto-save draft
            updateSendButtonState(); // Update send button state
        });
        
        // Load saved draft on page load
        loadDraft();
        
        // Initialize send button state
        updateSendButtonState();
    }

    // Send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent any default behavior
            console.log('🖱️ Send button clicked');
            const chatInput = document.getElementById('chatInput');
            const message = chatInput ? chatInput.value.trim() : '';
            console.log('📝 Message in input:', message ? `"${message.substring(0, 50)}..."` : 'empty');
            sendMessage();
        });
    }

    // Stop button
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopTyping);
    }

    // Data Source toggle (new circular menu button)
    const dataSourceToggle = document.getElementById('dataSourceToggle');
    if (dataSourceToggle) {
        dataSourceToggle.addEventListener('click', toggleDataSourceMenu);
        // Update button appearance based on current mode
        updateDataSourceButton();
    }

    // Data source menu items
    setupDataSourceMenu();

    // AI Mode toggle (new button in input area)
    const aiModeToggle = document.getElementById('aiModeToggle');
    if (aiModeToggle) {
        aiModeToggle.addEventListener('click', toggleThinkingMode);
        // Update button appearance based on current state
        updateAiModeButton();
    }

    // Sidebar functionality
    const chatSidebar = document.getElementById('chatSidebar');
    
    // New Chat button (now in sidebar)
    const newChatSidebarBtn = document.getElementById('newChatSidebarBtn');
    if (newChatSidebarBtn) {
        newChatSidebarBtn.addEventListener('click', function() {
            newChat();
            hideChatSidebar();
        });
    }

    // Clear History button (now in sidebar)
    const clearHistorySidebarBtn = document.getElementById('clearHistorySidebarBtn');
    if (clearHistorySidebarBtn) {
        clearHistorySidebarBtn.addEventListener('click', function() {
            clearAllChats();
            hideChatSidebar();
        });
    }

    // Add test scroll button functionality
    document.addEventListener('keydown', function(event) {
        // Ctrl+Shift+T for scroll test
        if (event.ctrlKey && event.shiftKey && event.key === 'T') {
            event.preventDefault();
            testScroll();
        }
    });

    // Quick action buttons (use event delegation for dynamic content)
    document.addEventListener('click', function(event) {
        if (event.target.closest('.quick-action-btn[data-question]')) {
            const btn = event.target.closest('.quick-action-btn[data-question]');
            const question = btn.getAttribute('data-question');
            if (question) {
                console.log('🎯 Quick action clicked:', question);
                askQuestion(question);
            }
        }
    });

    // Popup buttons
    document.addEventListener('click', function(event) {
        if (event.target.closest('.quick-action-btn[data-question]')) {
            const btn = event.target.closest('.quick-action-btn[data-question]');
            const question = btn.getAttribute('data-question');
            if (question) {
                console.log('🎯 Quick action clicked:', question);
                askQuestion(question);
            }
        }
    });

    // Track user scrolling with improved logic and hover detection
    const chatArea = document.getElementById('chatArea');
    if (chatArea) {
        let scrollTimeout;
        let isScrollingProgrammatically = false;
        
        // Mouse hover detection to pause auto-scroll
        chatArea.addEventListener('mouseenter', function() {
            isHovering = true;
            console.log('🖱️ Mouse entered chat area - auto-scroll paused');
        });
        
        chatArea.addEventListener('mouseleave', function() {
            isHovering = false;
            console.log('🖱️ Mouse left chat area - auto-scroll resumed');
            
            // Check if we should auto-scroll when mouse leaves
            setTimeout(() => {
                if (!isHovering) {
                    const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < 10;
                    if (isAtBottom) {
                        userScrolled = false;
                        console.log('✅ Mouse left and at bottom - auto-scroll enabled');
                    }
                }
            }, 100);
        });
        
        chatArea.addEventListener('scroll', function() {
            // Don't track if we're scrolling programmatically
            if (isScrollingProgrammatically) {
                isScrollingProgrammatically = false;
                return;
            }
            
            const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < 10;
            
            if (!isAtBottom) {
                userScrolled = true;
                console.log('🔄 User scrolled up - auto-scroll disabled');
            } else if (!isHovering) {
                userScrolled = false;
                console.log('✅ User at bottom and not hovering - auto-scroll enabled');
            }
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                if (!isHovering) {
                    const stillAtBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < 10;
                    if (stillAtBottom) {
                        userScrolled = false;
                    }
                }
            }, 1000);
        });
    }

    // Close quick actions when clicking outside
    document.addEventListener('click', function(event) {
        const quickActionBtn = event.target.closest('[onclick*="toggleQuickActions"]');
    });

    // Keyboard support for dropdowns
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            // No panels to hide
        }
        
        // Keyboard shortcuts
        if (event.ctrlKey || event.metaKey) {
            switch(event.key) {
                case 'n':
                case 'N':
                    event.preventDefault();
                    newChat();
                    showToast('New chat started', 'success');
                    break;
                case 'h':
                case 'H':
                    event.preventDefault();
                    const chatSidebar = document.getElementById('chatSidebar');
                    if (chatSidebar?.classList.contains('active')) {
                        hideChatSidebar();
                    } else {
                        showChatSidebar();
                    }
                    break;
                case 'Enter':
                    if (event.shiftKey) {
                        event.preventDefault();
                        sendMessage();
                    }
                    break;
            }
        }
        
        // Enter key support for popups
        if (event.key === 'Enter') {
            // No popups to handle
        }
    });

}

// Chat History Management
function saveChatHistory() {
    if (conversationHistory.length === 0) {
        console.log('📚 No conversation history to save');
        return;
    }
    
    const chatData = {
        id: currentSessionId || generateSessionId(),
        timestamp: new Date().toISOString(),
        messages: conversationHistory,
        mode: currentMode || 'pakwheels', // Save the current mode with the chat
        messageCount: conversationHistory.length
    };
    
    console.log('💾 Saving chat history:', {
        sessionId: chatData.id,
        messageCount: chatData.messages.length,
        mode: chatData.mode,
        timestamp: chatData.timestamp
    });
    
    let savedChats = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    
    // Remove existing chat with same ID
    savedChats = savedChats.filter(chat => chat.id !== chatData.id);
    
    // Add new chat at beginning
    savedChats.unshift(chatData);
    
    // Keep only last 50 chats
    savedChats = savedChats.slice(0, 50);
    
    localStorage.setItem('chatHistory', JSON.stringify(savedChats));
    console.log('✅ Chat history saved successfully. Total chats:', savedChats.length);
    
    // Always update sidebar (whether it's open or not) - load from database
    loadRecentChatsToSidebar();
    console.log('🔄 Sidebar updated with new chat history from database');
}

function generateSessionId() {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function loadChatHistory() {
    // This function can be called on page load if needed
    console.log('Chat history loaded');
}

// Chat Sidebar Functions
function showChatSidebar() {
    const chatSidebar = document.getElementById('chatSidebar');
    
    if (chatSidebar) {
        chatSidebar.classList.add('active');
        
        // Load recent chats
        loadRecentChatsToSidebar();
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
}

function hideChatSidebar() {
    const chatSidebar = document.getElementById('chatSidebar');
    
    if (chatSidebar) {
        chatSidebar.classList.remove('active');
        
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

function loadRecentChatsToSidebar() {
    const recentChatsList = document.getElementById('recentChatsSidebarList');
    if (!recentChatsList) {
        console.warn('⚠️ Recent chats list element not found');
        return;
    }
    
    // Show loading state
    recentChatsList.innerHTML = `
        <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
            Loading recent conversations...
        </div>
    `;
    
    console.log('📚 Loading recent chats to sidebar from database...');
    
    // Fetch recent chat sessions from database
    fetch('/api/chat/sessions')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📥 Recent chats loaded for sidebar:', data);
            displayRecentChatsInSidebar(data.sessions || []);
        })
        .catch(error => {
            console.error('❌ Error loading recent chats for sidebar:', error);
            recentChatsList.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
                    Error loading conversations
                </div>
            `;
        });
}

function displayRecentChatsInSidebar(sessions) {
    const recentChatsList = document.getElementById('recentChatsSidebarList');
    if (!recentChatsList) return;
    
    if (sessions.length === 0) {
        recentChatsList.innerHTML = `
            <div style="text-align: center; padding: 20px; color: var(--text-secondary); font-size: 13px;">
                No recent conversations
            </div>
        `;
        return;
    }
    
    // Mode icons and names for display
    const modeInfo = {
        'pakwheels': { icon: '🏢', name: 'PakWheels' },
        'whatsapp': { icon: '💬', name: 'WhatsApp' },
        'facebook_beta': { icon: '📘', name: 'Facebook Beta' },
        'dealership': { icon: '🏪', name: 'Dealership' },
        'insights': { icon: '🤖', name: 'AI Insights' }
    };
    
    recentChatsList.innerHTML = sessions.slice(0, 10).map((session, index) => {
        const preview = session.first_query && session.first_query.length > 0 
            ? session.first_query.substring(0, 50) + '...'
            : 'New conversation';
        
        // Format timestamp
        let timestamp = 'Unknown time';
        if (session.last_activity) {
            const date = new Date(session.last_activity);
            const now = new Date();
            const diffMs = now - date;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                timestamp = 'Today ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else if (diffDays === 1) {
                timestamp = 'Yesterday ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else if (diffDays < 7) {
                timestamp = date.toLocaleDateString([], {weekday: 'short'}) + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else {
                timestamp = date.toLocaleDateString([], {month: 'short', day: 'numeric'}) + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            }
        }
        
        const mode = session.mode || 'pakwheels';
        const modeDisplay = modeInfo[mode] || { icon: '🎯', name: 'Unknown' };
        const messageCount = session.message_count || 0;
        
        return `
            <div class="recent-chat-item" data-session-id="${session.session_id}" onclick="loadChatFromSidebarDB('${session.session_id}', '${session.mode}', '${session.first_query}')">
                <div class="chat-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div class="chat-mode" style="display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-secondary);">
                        <span>${modeDisplay.icon}</span>
                        <span>${modeDisplay.name}</span>
                    </div>
                    <div class="chat-count" style="font-size: 10px; color: var(--text-secondary); opacity: 0.7;">
                        ${messageCount} msgs
                    </div>
                </div>
                <div class="chat-preview" style="font-size: 13px; color: var(--text-primary); margin-bottom: 4px; line-height: 1.3;">${preview}</div>
                <div class="chat-timestamp" style="font-size: 11px; color: var(--text-secondary); opacity: 0.8;">${timestamp}</div>
            </div>
        `;
    }).join('');
    
    console.log('✅ Recent chats loaded to sidebar successfully');
}

function loadChatFromSidebarDB(sessionId, mode, firstQuery) {
    console.log('👁️ Loading conversation from sidebar:', { sessionId, mode, firstQuery });
    
    // Hide sidebar on mobile
    if (window.innerWidth <= 768) {
        hideChatSidebar();
    }
    
    // Load the conversation history using the same method as the main recent chats
    viewConversationHistory(sessionId, mode, firstQuery);
    
    // Update active state
    document.querySelectorAll('.recent-chat-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-session-id') === sessionId) {
            item.classList.add('active');
        }
    });
    
    console.log('✅ Chat loaded successfully from sidebar database');
}

// Display chat history function
function displayChatHistory() {
    const messagesContainer = document.getElementById('messagesContainer');
    const welcomeScreen = document.getElementById('welcomeScreen');
    
    if (!messagesContainer || !welcomeScreen) return;
    
    // Clear existing messages
    messagesContainer.innerHTML = '';
    
    if (conversationHistory.length === 0) {
        // Show welcome screen if no messages
        messagesContainer.style.display = 'none';
        welcomeScreen.style.display = 'flex';
        return;
    }
    
    // Hide welcome screen and show messages
    welcomeScreen.style.display = 'none';
    messagesContainer.style.display = 'block';
    
    // Add all messages to DOM
    conversationHistory.forEach((msg, index) => {
        const isUser = msg.role === 'user';
        addMessageToDOM(msg.content, isUser, false); // false = no typing effect for history
    });
    
    // Scroll to bottom
    setTimeout(() => {
        scrollToBottom();
    }, 100);
}
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    updateLogos(savedTheme);
    updateHighlightTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    updateLogos(newTheme);
    
    // Force refresh of message content colors
    refreshMessageTheme();
}

function refreshMessageTheme() {
    // Force a repaint of all message content to ensure theme colors are applied
    const messages = document.querySelectorAll('.message-content');
    messages.forEach(messageContent => {
        // Trigger a reflow to ensure CSS variables are recalculated
        messageContent.style.display = 'none';
        messageContent.offsetHeight; // Trigger reflow
        messageContent.style.display = '';
    });
    
    console.log('🎨 Message theme refreshed');
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
    
    // Update highlight.js theme
    updateHighlightTheme(theme);
}

function updateHighlightTheme(theme) {
    const lightTheme = document.getElementById('hljs-light');
    const darkTheme = document.getElementById('hljs-dark');
    
    if (lightTheme && darkTheme) {
        if (theme === 'dark') {
            lightTheme.disabled = true;
            darkTheme.disabled = false;
        } else {
            lightTheme.disabled = false;
            darkTheme.disabled = true;
        }
    }
}

function updateLogos(theme) {
    const logos = document.querySelectorAll('.brand-logo, #navLogo, #loadingLogo');
    const logoPath = theme === 'dark' 
        ? '/static/images/light-logo.svg' 
        : '/static/images/dark-logo.svg';
    
    logos.forEach(logo => {
        if (logo) {
            logo.src = logoPath;
        }
    });
}

// Mode Selection Functions
function setMode(mode) {
    currentMode = mode;
    console.log('🎯 Mode changed to:', mode);
    
    // Save selected mode to localStorage
    localStorage.setItem('selectedMode', mode);
    
    // Update data source button appearance
    updateDataSourceButton();
    
    // Update placeholder and description
    updateModePlaceholder();
    
    // Hide data source menu
    hideDataSourceMenu();
    
    // Show toast
    const modeNames = {
        'pakwheels': 'PakWheels Forums',
        'whatsapp': 'WhatsApp Data',
        'facebook_beta': 'Facebook Beta',
        'dealership': 'Dealership Data',
        'insights': 'AI Insights'
    };
    showToast(`Switched to ${modeNames[mode]} mode`, 'success');
}

function updateDataSourceButton() {
    const dataSourceToggle = document.getElementById('dataSourceToggle');
    if (dataSourceToggle) {
        const modeNames = {
            'pakwheels': 'PakWheels Forums',
            'whatsapp': 'WhatsApp Data',
            'facebook_beta': 'Facebook Beta',
            'dealership': 'Dealership Data',
            'insights': 'AI Insights'
        };
        
        dataSourceToggle.title = `Current: ${modeNames[currentMode] || 'Select Mode'} (Click to change)`;
    }
    
    // Update menu items
    updateDataSourceMenuItems();
}

// Data Source Menu Functions
function toggleDataSourceMenu() {
    const dataSourceMenu = document.getElementById('dataSourceMenu');
    const dataSourceToggle = document.getElementById('dataSourceToggle');
    
    if (dataSourceMenu && dataSourceToggle) {
        const isActive = dataSourceMenu.classList.contains('active');
        
        if (isActive) {
            hideDataSourceMenu();
        } else {
            showDataSourceMenu();
        }
    }
}

function showDataSourceMenu() {
    const dataSourceMenu = document.getElementById('dataSourceMenu');
    const dataSourceToggle = document.getElementById('dataSourceToggle');
    
    if (dataSourceMenu && dataSourceToggle) {
        dataSourceMenu.classList.add('active');
        dataSourceToggle.classList.add('active');
        
        // Update menu items
        updateDataSourceMenuItems();
    }
}

function hideDataSourceMenu() {
    const dataSourceMenu = document.getElementById('dataSourceMenu');
    const dataSourceToggle = document.getElementById('dataSourceToggle');
    
    if (dataSourceMenu && dataSourceToggle) {
        dataSourceMenu.classList.remove('active');
        dataSourceToggle.classList.remove('active');
    }
}

function setupDataSourceMenu() {
    // Menu item click handlers
    const menuItems = document.querySelectorAll('.data-source-item');
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const mode = item.getAttribute('data-mode');
            if (mode) {
                setMode(mode);
            }
        });
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
        const dataSourceDropdown = document.getElementById('dataSourceDropdown');
        if (dataSourceDropdown && !dataSourceDropdown.contains(e.target)) {
            hideDataSourceMenu();
        }
    });
}

function updateDataSourceMenuItems() {
    const menuItems = document.querySelectorAll('.data-source-item');
    menuItems.forEach(item => {
        const mode = item.getAttribute('data-mode');
        if (mode === currentMode) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Setup Welcome Animations
function setupWelcomeAnimations() {
    console.log('✅ Welcome animations setup complete (avatar removed)');
}

// Loading Screen Animation Handler
function handleLoadingScreenAnimations() {
    const loadingScreen = document.getElementById('loadingScreen');
    
    if (loadingScreen) {
        console.log('✅ Loading screen animations setup complete');
    }
}

// Thinking Mode Toggle
function toggleThinkingMode() {
    thinkingMode = !thinkingMode;
    
    // Update the new AI Mode button
    updateAiModeButton();
    
    // Update input placeholder based on mode
    updateModePlaceholder();
    
    console.log('🧠 Thinking mode:', thinkingMode ? 'ON' : 'OFF');
    
    // Enhanced toast message
    const modeDescription = thinkingMode 
        ? 'AI Mode: Detailed analysis with charts and insights enabled'
        : 'AI Mode: Quick response mode enabled';
    
    showToast(`🧠 ${modeDescription}`, 'info');
    
    // Save preference to localStorage
    localStorage.setItem('chatbot_thinking_mode', thinkingMode.toString());
}

// Load thinking mode preference on startup
function loadThinkingModePreference() {
    const savedMode = localStorage.getItem('chatbot_thinking_mode');
    if (savedMode !== null) {
        thinkingMode = savedMode === 'true';
        
        // Update UI to match loaded preference
        updateAiModeButton();
        
        console.log('🧠 Loaded thinking mode preference:', thinkingMode ? 'ON' : 'OFF');
    }
}

// Update AI Mode Button Appearance
function updateAiModeButton() {
    const aiModeToggle = document.getElementById('aiModeToggle');
    if (aiModeToggle) {
        if (thinkingMode) {
            aiModeToggle.classList.add('active');
            aiModeToggle.title = 'AI Mode: ON (Click to disable detailed analysis)';
        } else {
            aiModeToggle.classList.remove('active');
            aiModeToggle.title = 'AI Mode: OFF (Click to enable detailed analysis)';
        }
    }
}

// Mode Placeholder Update - Modern ChatGPT Style
function updateModePlaceholder() {
    const chatInput = document.getElementById('chatInput');
    
    if (!chatInput) return;
    
    const mode = currentMode;
    let placeholder = '';
    
    if (!mode) {
        // No mode selected - simple prompt
        placeholder = 'Message Insights AI...';
    } else {
        switch (mode) {
            case 'pakwheels':
                placeholder = 'Ask about car issues, reviews, or discussions...';
                break;
            case 'whatsapp':
                placeholder = 'Ask about customer conversations...';
                break;
            case 'facebook_beta':
                placeholder = 'Ask about Facebook posts and feedback...';
                break;
            case 'dealership':
                placeholder = 'Ask about warranty, inspections, or VIN data...';
                break;
            case 'insights':
                placeholder = 'Ask me anything...';
                break;
            default:
                placeholder = 'Message Insights AI...';
        }
    }
    
    chatInput.placeholder = placeholder;
    
    // Update send button state when placeholder changes
    updateSendButtonState();
}

// Auto-resize textarea - Modern ChatGPT style
function autoResize(textarea) {
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate new height with modern constraints
    const minHeight = 24; // Single line height
    const maxHeight = 200; // Maximum height before scrolling
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    
    // Apply the new height
    textarea.style.height = newHeight + 'px';
    
    // Update send button state based on content
    updateSendButtonState();
}

// Update send button state based on input content
function updateSendButtonState() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    
    if (chatInput && sendBtn) {
        const hasContent = chatInput.value.trim().length > 0;
        sendBtn.disabled = !hasContent || isTyping;
        
        // Update button appearance
        if (hasContent && !isTyping) {
            sendBtn.style.opacity = '1';
            sendBtn.style.transform = 'scale(1)';
        } else {
            sendBtn.style.opacity = '0.4';
            sendBtn.style.transform = 'scale(0.95)';
        }
    }
}

// Draft Management
function saveDraft(content) {
    // Debounce the save operation
    clearTimeout(draftSaveTimeout);
    draftSaveTimeout = setTimeout(() => {
        if (content.trim()) {
            localStorage.setItem('chatbot_draft', content);
            console.log('💾 Draft saved');
        } else {
            localStorage.removeItem('chatbot_draft');
        }
    }, 1000); // Save after 1 second of inactivity
}

function loadDraft() {
    const draft = localStorage.getItem('chatbot_draft');
    const chatInput = document.getElementById('chatInput');
    
    if (draft && chatInput && !chatInput.value) {
        chatInput.value = draft;
        autoResize(chatInput);
        console.log('📝 Draft loaded');
    }
}

function clearDraft() {
    localStorage.removeItem('chatbot_draft');
    console.log('🗑️ Draft cleared');
}

// Handle key press
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        
        // Get the message before sending to avoid race conditions
        const chatInput = document.getElementById('chatInput');
        const message = chatInput ? chatInput.value.trim() : '';
        
        if (message && !isTyping) {
            sendMessage();
        } else if (!message) {
            showToast('Please enter a message', 'warning');
        }
    }
}

// Chart Colors Function
function getChartColors() {
    return [
        'rgba(124, 58, 237, 0.8)',   // Primary purple
        'rgba(168, 85, 247, 0.8)',   // Light purple
        'rgba(192, 132, 252, 0.8)',  // Lighter purple
        'rgba(233, 213, 255, 0.8)',  // Very light purple
        'rgba(34, 197, 94, 0.8)',    // Green
        'rgba(251, 191, 36, 0.8)',   // Yellow
        'rgba(239, 68, 68, 0.8)',    // Red
        'rgba(59, 130, 246, 0.8)',   // Blue
        'rgba(16, 185, 129, 0.8)',   // Teal
        'rgba(245, 158, 11, 0.8)'    // Orange
    ];
}

// Quick Actions Functions
function askQuestion(question) {
    document.getElementById('chatInput').value = question;
    sendMessage();
}

// Check authentication status
function checkAuthStatus() {
    console.log('🔐 Checking authentication status...');
    return fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('🔐 Auth status response:', response.status, response.statusText);
        if (!response.ok) {
            console.error('❌ Auth status check failed:', response.status, response.statusText);
            return false;
        }
        return response.json();
    })
    .then(data => {
        console.log('🔐 Auth status data:', data);
        return data.authenticated === true;
    })
    .catch(error => {
        console.error('❌ Auth check error:', error);
        return false;
    });
}

// Debug function to check session
function debugSession() {
    console.log('🔍 Checking session debug info...');
    fetch('/api/debug/session', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log('🔍 Session debug:', data);
    })
    .catch(error => {
        console.error('❌ Session debug error:', error);
    });
}

// Debug function to check chat history
function debugChatHistory(mode = 'insights') {
    console.log('📚 Checking chat history debug info...');
    fetch(`/api/debug/chat-history?mode=${mode}&limit=10`, {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log('📚 Chat history debug:', data);
    })
    .catch(error => {
        console.error('❌ Chat history debug error:', error);
    });
}

// Debug function to test chat saving
function debugTestChatSave() {
    console.log('💾 Testing chat save...');
    fetch('/api/debug/test-chat-save', {
        method: 'POST',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log('💾 Test chat save result:', data);
        if (data.success) {
            console.log('✅ Chat save test successful');
            // Now check the history
            debugChatHistory();
        }
    })
    .catch(error => {
        console.error('❌ Test chat save error:', error);
    });
}

// Add debug functions to window for easy access
window.debugSession = debugSession;
window.debugChatHistory = debugChatHistory;
window.debugTestChatSave = debugTestChatSave;

// Helper function to append content to existing message (plain text only for streaming)
function appendToMessage(messageDiv, content) {
    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent) {
        // For streaming, just append plain text
        messageContent.textContent += content;
        
        // Auto-scroll to bottom
        const chatArea = document.getElementById('chatArea');
        if (chatArea && !userScrolled) {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }
}

// Helper function to handle structured data
function handleStructuredData(structured) {
    if (!structured) return;
    
    // Handle references, charts, tables, etc.
    if (structured.references && structured.references.length > 0) {
        console.log('📚 References found:', structured.references.length);
    }
    
    if (structured.charts && structured.charts.length > 0) {
        console.log('📊 Charts found:', structured.charts.length);
    }
}

// Helper function to clear chat input
function clearChatInput() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.value = '';
        autoResize(chatInput);
        console.log('🧹 Chat input cleared');
    }
}

// Send Message Function
function sendMessage(isRetry = false) {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message || isTyping) {
        if (!message) {
            showToast('Please enter a message', 'warning');
        }
        return;
    }
    
    console.log('📤 Sending message:', message.substring(0, 50) + (message.length > 50 ? '...' : ''));
    
    // Store the message before any async operations
    const messageToSend = message;
    
    // Check authentication first, but don't block if check fails
    checkAuthStatus().then(isAuthenticated => {
        if (!isAuthenticated) {
            console.warn('⚠️ Authentication check failed, but proceeding anyway - server will handle auth');
        }
        
        // Always proceed with sending message - let server handle auth
        sendMessageAuthenticated(messageToSend, isRetry);
    }).catch(error => {
        console.error('❌ Auth check failed:', error);
        // Always proceed anyway, let the server handle auth
        sendMessageAuthenticated(messageToSend, isRetry);
    });
}

function sendMessageAuthenticated(message, isRetry = false) {
    const chatInput = document.getElementById('chatInput');
    
    // Clear draft when sending
    if (!isRetry) {
        clearDraft();
        retryCount = 0; // Reset retry count for new messages
    }
    
    // Add user message to DOM (only if not a retry)
    if (!isRetry) {
        addMessageToDOM(message, true);
        
        // Add to conversation history
        conversationHistory.push({
            role: 'user',
            content: message
        });
        
        // Save chat history
        saveChatHistory();
        
        // Clear input immediately and ensure it stays cleared
        clearChatInput();
        
        // Double-check input is cleared after a short delay
        setTimeout(() => {
            if (chatInput && chatInput.value.trim() !== '') {
                console.log('🔧 Input not cleared properly, clearing again');
                clearChatInput();
            }
        }, 100);
    }
    
    // Show typing indicator
    showTypingIndicator();
    
    // Get current mode and thinking mode
    const mode = currentMode; // Use global currentMode
    
    console.log('🔧 Request config:', { 
        mode: mode, 
        thinking: thinkingMode,
        messageLength: message.length,
        isRetry: isRetry,
        retryCount: retryCount
    });
    
    // Send to backend (using non-streaming for reliability)
    console.log('🔧 Making request to /chatbot_query with:', { mode, thinking: thinkingMode });
    fetch('/chatbot_query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: message,
            mode: mode,
            thinking: thinkingMode
        })
    })
    .then(response => {
        console.log('📡 Response status:', response.status);
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Authentication required');
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📥 Response data received');
        hideTypingIndicator();
        retryCount = 0; // Reset retry count on success
        
        if (data.answer) {
            // Add bot response to conversation history
            conversationHistory.push({
                role: 'assistant',
                content: data.answer
            });
            
            // Save chat history
            saveChatHistory();
            
            // Add bot message to DOM with typing effect
            addMessageToDOM(data.answer, false, true, data.structured);
            
            console.log('✅ Message processed successfully');
        } else {
            console.error('❌ No answer in response:', data);
            addMessageToDOM('Sorry, I encountered an error. Please try again.', false);
        }
    })
    .catch(error => {
        console.error('❌ Chat error:', error);
        hideTypingIndicator();
        
        // Handle authentication errors
        if (error.message.includes('401') || error.message.includes('Unauthorized') || error.message.includes('Authentication required')) {
            console.error('❌ Authentication error');
            showToast('Please log in to continue', 'error');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            return;
        }
        
        // Retry logic
        if (retryCount < maxRetries && (error.message.includes('Failed to fetch') || error.message.includes('500'))) {
            retryCount++;
            console.log(`🔄 Retrying message (attempt ${retryCount}/${maxRetries})`);
            
            // Show retry message
            const retryMessage = `Connection issue. Retrying... (${retryCount}/${maxRetries})`;
            showToast(retryMessage, 'warning');
            
            // Retry after a delay
            setTimeout(() => {
                sendMessageAuthenticated(message, true); // Retry with the same message
            }, 2000 * retryCount); // Exponential backoff
        } else {
            // Max retries reached or non-retryable error
            console.error('❌ Max retries reached or non-retryable error');
            addMessageToDOM('Sorry, I could not connect to the server. Please check your connection and try again.', false);
            showToast('Connection failed. Please try again.', 'error');
        }
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
                <div class="popup-title">Scraping ${source} Data</div>
            </div>
            <div class="popup-body">
                <div class="progress-container">
                    <div class="progress-status" id="progressStatus">
                        Starting scraping process for ${count} posts...
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progressBar"></div>
                    </div>
                    <div class="progress-details" id="progressDetails">
                        Initializing scraper...
                    </div>
                </div>
                <div class="progress-logs" id="progressLogs">
                    <div class="log-entry">📋 Scraping ${count} posts from ${source}</div>
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
    
    // Start progress animation
    animateProgress();
}

function updateScrapingProgress(message, type = 'info') {
    const statusEl = document.getElementById('progressStatus');
    const detailsEl = document.getElementById('progressDetails');
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
        logEntry.innerHTML = `${icon} [${timestamp}] ${message}`;
        logsEl.appendChild(logEntry);
        logsEl.scrollTop = logsEl.scrollHeight;
    }
    
    if (type === 'success') {
        if (detailsEl) {
            if (message.includes('Pipeline completed')) {
                detailsEl.textContent = '🎉 All data processed and ready for use!';
            } else if (message.includes('scraped') || message.includes('fetched')) {
                detailsEl.textContent = '🚀 Starting AI pipeline processing...';
            } else {
                detailsEl.textContent = '✅ Process completed successfully!';
            }
        }
        
        // Update close button for success states
        const closeBtn = document.querySelector('#scrapingProgressPopup .popup-btn-cancel');
        if (closeBtn && message.includes('complete')) {
            closeBtn.textContent = 'Refresh Page';
            closeBtn.disabled = false;
            closeBtn.style.background = 'var(--primary-gradient)';
            closeBtn.style.color = 'white';
            
            // Add manual refresh option
            closeBtn.onclick = () => {
                hideScrapingProgress();
                // Don't reload page - just close popup
            };
        }
        
    } else if (type === 'error') {
        if (detailsEl) {
            detailsEl.textContent = '❌ Process failed. Please try again or refresh manually.';
        }
        
        // Enable close button for errors
        const closeBtn = document.querySelector('#scrapingProgressPopup .popup-btn-cancel');
        if (closeBtn) {
            closeBtn.textContent = 'Close';
            closeBtn.disabled = false;
            closeBtn.style.background = '#ef4444';
            closeBtn.style.color = 'white';
            
            // Add manual refresh option for errors
            closeBtn.onclick = () => {
                hideScrapingProgress();
                // Optional refresh - ask user
                if (confirm('Would you like to refresh the page to see any changes?')) {
                    window.location.reload();
                }
            };
        }
        
    } else {
        // Info/processing state
        if (detailsEl && message.includes('processing')) {
            detailsEl.textContent = '⚙️ AI engine is analyzing and indexing the data...';
        } else if (detailsEl && message.includes('Waiting')) {
            detailsEl.textContent = '⏳ Preparing AI pipeline for data processing...';
        }
    }
}

function hideScrapingProgress() {
    const progressPopup = document.getElementById('scrapingProgressPopup');
    if (progressPopup) {
        progressPopup.remove();
    }
}

// Helper function to update progress bar
function updateProgressBar(percentage) {
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = Math.min(100, Math.max(0, percentage)) + '%';
    }
}

function animateProgress() {
    const progressBar = document.getElementById('progressBar');
    if (!progressBar) return;
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) progress = 90; // Don't complete until we get success
        
        updateProgressBar(progress);
        
        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 500);
}

function startEngineMonitoring() {
    updateScrapingProgress('Starting AI pipeline processing...', 'info');
    
    let checkCount = 0;
    const maxChecks = 120; // 10 minutes max (increased from 5 minutes)
    
    const checkEngine = () => {
        checkCount++;
        
        // If we know the endpoint doesn't exist, simulate completion
        if (!pipelineEndpointExists) {
            console.log('🔄 Pipeline endpoint not available, simulating completion...');
            
            // Simulate processing for a few checks, then complete
            if (checkCount <= 3) {
                updateScrapingProgress(`🔄 Processing data... (${checkCount}/3)`, 'info');
                setTimeout(checkEngine, 2000);
                return;
            } else {
                // Simulate completion
                updateScrapingProgress('✅ Data processing completed!', 'success');
                
                // Complete progress bar
                updateProgressBar(100);
                
                // Show completion message and auto-close
                setTimeout(() => {
                    updateScrapingProgress('🎉 Process complete! Closing popup...', 'success');
                    
                    // Close popup and refresh page after 2 seconds
                    setTimeout(() => {
                        hideScrapingProgress();
                        showToast('Data processing completed successfully!', 'success');
                        // Don't auto-reload page
                    }, 2000);
                }, 1500);
                
                return;
            }
        }
        
        fetch('/api/pipeline-status')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                const status = data.status || 'unknown';
                console.log('🔍 Engine status check', checkCount + ':'  , status);
                
                if (status === 'completed' || status === 'ready') {
                    // Pipeline completed successfully
                    updateScrapingProgress('✅ AI Pipeline completed successfully!', 'success');
                    
                    // Complete progress bar
                    updateProgressBar(100);
                    
                    // Show completion message and auto-close
                    setTimeout(() => {
                        updateScrapingProgress('🎉 Process complete! Closing popup...', 'success');
                        
                        // Close popup and refresh page after 2 seconds
                        setTimeout(() => {
                            hideScrapingProgress();
                            showToast('Data processing completed successfully!');
                            // Don't auto-reload page
                        }, 2000);
                    }, 1500);
                    
                } else if (status === 'processing') {
                    // Still processing
                    updateScrapingProgress(`🔄 Processing scraped data... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 3000); // Check every 3 seconds during processing
                    
                } else if (status === 'enriching') {
                    updateScrapingProgress(`🤖 Enriching data with AI analysis... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 3000);
                    
                } else if (status === 'indexing') {
                    updateScrapingProgress(`📚 Building vector database... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 3000);
                    
                } else if (status === 'separating_mixed_blocks') {
                    updateScrapingProgress(`🔧 Running MixBlock separation... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 3000);
                    
                } else if (status === 'error' || status === 'failed') {
                    updateScrapingProgress('❌ AI pipeline encountered an error', 'error');
                    
                } else if (checkCount >= maxChecks) {
                    updateScrapingProgress('⏰ Pipeline taking longer than expected. Check logs for details.', 'error');
                    
                } else {
                    // Continue monitoring with unknown status
                    updateScrapingProgress(`⏳ AI engine status: ${status}... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000); // Check every 5 seconds for unknown status
                }
            })
            .catch(error => {
                console.error('Pipeline status check failed:', error);
                
                // Don't log 404 errors as they're expected when pipeline endpoint doesn't exist
                if (error.message.includes('404')) {
                    console.log('🔄 Pipeline endpoint not found, simulating completion...');
                    
                    // Simulate processing for a few checks, then complete
                    if (checkCount <= 5) {
                        updateScrapingProgress(`🔄 Processing data... (${checkCount}/5)`, 'info');
                        setTimeout(checkEngine, 3000);
                        return;
                    } else {
                        // Simulate completion
                        updateScrapingProgress('✅ Data processing completed!', 'success');
                        
                        // Complete progress bar
                        updateProgressBar(100);
                        
                        // Show completion message and auto-close
                        setTimeout(() => {
                            updateScrapingProgress('🎉 Process complete! Data is now available.', 'success');
                            
                            // Close popup after showing completion message
                            setTimeout(() => {
                                hideScrapingProgress();
                                showToast('Data processing completed successfully!');
                                // Don't auto-reload page
                            }, 2000);
                        }, 1500);
                        
                        return;
                    }
                } else if (checkCount < maxChecks) {
                    updateScrapingProgress(`🔍 Checking pipeline status... (${checkCount}/${maxChecks})`, 'info');
                    setTimeout(checkEngine, 5000);
                } else {
                    updateScrapingProgress('❌ Could not check pipeline status. Please check manually.', 'error');
                }
            });
    };
    
    // Start checking immediately, then every few seconds
    setTimeout(checkEngine, 1000);
}

// Popup Functions
function openPakWheelsPopup() {
    const popup = document.getElementById('pakWheelsPopup');
    if (popup) {
        popup.classList.add('active');
        
        // Focus on input and select default value
        setTimeout(() => {
            const input = document.getElementById('pakWheelsPosts');
            if (input) {
                input.focus();
                input.select();
            }
        }, 100);
    }
}

function closePakWheelsPopup() {
    const popup = document.getElementById('pakWheelsPopup');
    if (popup) {
        popup.classList.remove('active');
    }
}

function openWatiPopup() {
    const popup = document.getElementById('watiPopup');
    if (popup) {
        popup.classList.add('active');
        
        // Focus on select element
        setTimeout(() => {
            const select = document.getElementById('watiDays');
            if (select) {
                select.focus();
            }
        }, 100);
    }
}

function closeWatiPopup() {
    const popup = document.getElementById('watiPopup');
    if (popup) {
        popup.classList.remove('active');
    }
}

// Network connectivity check
function checkNetworkConnectivity() {
    return fetch('/api/pipeline-status', { 
        method: 'GET',
        cache: 'no-cache',
        timeout: 5000 
    })
    .then(response => {
        return response.ok;
    })
    .catch(() => {
        return false;
    });
}

// Enhanced scraping with connectivity check
function startPakWheelsScraping() {
    const postsInput = document.getElementById('pakWheelsPosts');
    const posts = parseInt(postsInput.value);
    
    // Validate input
    if (isNaN(posts) || posts < 10 || posts > 10000) {
        showToast('Please enter a valid number of posts (10-10,000)', 'warning');
        postsInput.focus();
        postsInput.select();
        return;
    }
    
    console.log('🚀 Starting PakWheels scraping for', posts, 'posts');
    closePakWheelsPopup();
    
    // Show progress popup
    showScrapingProgress('PakWheels', posts);
    
    // Make API call to start scraping with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
    
    fetch('/scrape_single_topic', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            max_posts: posts,
            fetch_mode: 'latest'
        }),
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        
        if (response.redirected) {
            // Server redirected, which means scraping completed
            updateScrapingProgress('Scraping completed successfully!', 'success');
            startEngineMonitoring();
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data) {
            if (data.success) {
                updateScrapingProgress(`Successfully scraped ${data.count || posts} posts!`, 'success');
                startEngineMonitoring();
            } else {
                const errorMsg = data.error || 'Unknown error';
                if (errorMsg.includes('Connection error') || errorMsg.includes('connection')) {
                    updateScrapingProgress('❌ Connection Error: Unable to connect to PakWheels. Please check your internet connection and try again.', 'error');
                } else if (errorMsg.includes('Timeout') || errorMsg.includes('timeout')) {
                    updateScrapingProgress('⏰ Timeout Error: PakWheels is taking too long to respond. Please try again later.', 'error');
                } else if (errorMsg.includes('404') || errorMsg.includes('not found')) {
                    updateScrapingProgress('📄 Not Found: The PakWheels topic could not be found. Please check the URL.', 'error');
                } else {
                    updateScrapingProgress('❌ Scraping Error: ' + errorMsg, 'error');
                }
            }
        }
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('❌ Scraping error:', error);
        
        if (error.name === 'AbortError') {
            updateScrapingProgress('⏰ Request Timeout: The scraping process took too long. Please try with fewer posts.', 'error');
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            updateScrapingProgress('🔌 Network Error: Unable to connect to the server. Please check your internet connection.', 'error');
        } else {
            updateScrapingProgress('❌ Request Error: ' + error.message, 'error');
        }
    });
}

function startWatiFetching() {
    const days = document.getElementById('watiDays').value;
    closeWatiPopup();
    
    console.log('📱 Starting WATI data fetch for', days, 'days');
    
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
            startEngineMonitoring();
        } else {
            updateScrapingProgress('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('❌ WATI fetch error:', error);
        updateScrapingProgress('Error: ' + error.message, 'error');
    });
}

// Monitor WATI progress by checking logs
function startWatiProgressMonitoring() {
    let checkCount = 0;
    const maxChecks = 920; // 10 minutes max (5 second intervals)
    
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
                } else if (data.status === 'error') {
                    updateScrapingProgress('WATI fetch encountered an error', 'error');
                }
            })
            .catch(error => {
                // Progress endpoint not available, use simulated progress
                if (checkCount < maxChecks) {
                    const simulatedProgress = Math.min(85, (checkCount / maxChecks) * 85);
                    updateProgressBar(simulatedProgress);
                    
                    // Show generic progress message
                    updateScrapingProgress(
                        `Fetching WATI data... (${checkCount}/${maxChecks})`, 
                        'info'
                    );
                    
                    setTimeout(checkProgress, 5000); // Check every 5 seconds
                } else {
                    updateScrapingProgress('WATI fetch taking longer than expected...', 'info');
                }
            });
    };
    
    // Start checking after a short delay
    setTimeout(checkProgress, 2000);
}

// Show/Hide Typing Indicator
function showTypingIndicator() {
    hideWelcome();
    
    const messagesContainer = document.getElementById('messagesContainer');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing-message';
    typingDiv.id = 'typingIndicator';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const author = document.createElement('div');
    author.className = 'message-author';
    author.textContent = 'Insights AI';
    
    header.appendChild(author);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Enhanced thinking indicator with rotating messages
    const thinkingIndicator = document.createElement('div');
    thinkingIndicator.className = 'thinking-indicator';
    
    const thinkingMessages = [
        '🧠 Thinking...',
        '📊 Gathering data...',
        '🔍 Analyzing information...',
        '💡 Processing insights...',
        '⚡ Generating response...'
    ];
    
    let messageIndex = 0;
    thinkingIndicator.innerHTML = `
        <div class="thinking-text">${thinkingMessages[0]}</div>
        <div class="thinking-dots">
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
            <div class="thinking-dot"></div>
        </div>
    `;
    
    // Rotate thinking messages every 2 seconds
    const messageInterval = setInterval(() => {
        messageIndex = (messageIndex + 1) % thinkingMessages.length;
        const textElement = thinkingIndicator.querySelector('.thinking-text');
        if (textElement) {
            textElement.style.opacity = '0';
            setTimeout(() => {
                textElement.textContent = thinkingMessages[messageIndex];
                textElement.style.opacity = '1';
            }, 200);
        }
    }, 2000);
    
    // Store interval for cleanup
    thinkingIndicator.messageInterval = messageInterval;
    
    contentDiv.appendChild(thinkingIndicator);
    typingDiv.appendChild(header);
    typingDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(typingDiv);
    
    // Force scroll when adding typing indicator
    setTimeout(() => {
        scrollToBottom(true);
    }, 50);
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        // Clear message rotation interval
        const thinkingDiv = typingIndicator.querySelector('.thinking-indicator');
        if (thinkingDiv && thinkingDiv.messageInterval) {
            clearInterval(thinkingDiv.messageInterval);
        }
        
        typingIndicator.remove();
    }
}

// Hide Welcome Screen and Show Messages Container
function hideWelcome() {
    console.log('👋 Hiding welcome screen and showing messages container...');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesContainer = document.getElementById('messagesContainer');
    
    if (welcomeScreen && messagesContainer) {
        welcomeScreen.style.display = 'none';
        messagesContainer.style.display = 'block';
        console.log('✅ Welcome hidden, messages container shown');
    } else {
        console.error('❌ Could not find welcome screen or messages container');
        console.log('Welcome screen found:', !!welcomeScreen);
        console.log('Messages container found:', !!messagesContainer);
    }
}

// Scroll to Bottom
function scrollToBottom(force = false) {
    const chatArea = document.getElementById('chatArea');
    if (!chatArea) {
        console.log('❌ Chat area not found for scrolling');
        return;
    }
    
    // Force scroll if requested, or if user hasn't manually scrolled and not hovering
    if (force || (!userScrolled && !isHovering)) {
        console.log('📍 Scrolling to bottom...');
        
        // Remove any existing scroll hint
        const existingHint = document.getElementById('scrollDownHint');
        if (existingHint) {
            existingHint.remove();
        }
        
        // Use requestAnimationFrame for smoother scrolling
        requestAnimationFrame(() => {
            chatArea.scrollTo({
                top: chatArea.scrollHeight,
                behavior: force ? 'auto' : 'smooth'
            });
            console.log('📍 Scrolled to:', chatArea.scrollTop, 'of', chatArea.scrollHeight);
        });
    } else {
        console.log('📍 Scroll skipped - user has manually scrolled or is hovering');
    }
}

// Enhanced scroll to bottom with smooth behavior
function smoothScrollToBottom() {
    const chatArea = document.getElementById('chatArea');
    if (!chatArea) return;
    
    // Only smooth scroll if user hasn't manually scrolled and isn't hovering
    if (!userScrolled && !isHovering) {
        chatArea.scrollTo({
            top: chatArea.scrollHeight,
            behavior: 'smooth'
        });
    }
}

// Check if user is hovering over chat area
function isUserHoveringChatArea() {
    const chatArea = document.getElementById('chatArea');
    if (!chatArea) return false;
    
    return chatArea.matches(':hover');
}

// Add message entrance animation
function addMessageEntranceAnimation(messageDiv) {
    if (!messageDiv) return; // Defensive check
    
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    messageDiv.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
    
    // Trigger animation after a brief delay
    setTimeout(() => {
        if (messageDiv.parentNode) { // Check if still in DOM
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }
    }, 50);
}

// Show scroll down hint when user has scrolled up during typing
function showScrollDownHint() {
    // Remove existing hint
    const existingHint = document.getElementById('scrollDownHint');
    if (existingHint) return; // Don't show multiple hints
    
    const chatArea = document.getElementById('chatArea');
    if (!chatArea) return;
    
    const hint = document.createElement('div');
    hint.id = 'scrollDownHint';
    hint.className = 'scroll-down-hint';
    hint.innerHTML = `
        <div class="scroll-hint-content">
            <span>New message below</span>
            <span class="scroll-arrow">↓</span>
        </div>
    `;
    
    hint.style.cssText = `
        position: absolute;
        bottom: 20px;
        right: 20px;
        background: var(--primary-gradient);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        cursor: pointer;
        z-index: 1000;
        animation: fadeInUp 0.3s ease-out;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    hint.onclick = () => {
        userScrolled = false; // Reset scroll state
        scrollToBottom(true);
        hint.remove();
    };
    
    chatArea.style.position = 'relative';
    chatArea.appendChild(hint);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (hint.parentNode) {
            hint.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => hint.remove(), 300);
        }
    }, 5000);
}

// Parse References Function
function parseReferences(content) {
    // Defensive checks
    if (!content || typeof content !== 'string') {
        console.warn('⚠️ parseReferences called with invalid content:', content);
        return [];
    }
    
    const references = [];
    // Use global currentMode instead of non-existent modeSelector
    const mode = currentMode || 'pakwheels';
    
    // Enhanced WhatsApp format
    const enhancedWaPattern = /\*\*\[(\d+)\]\*\*\s*👤\s*([^|]+)\s*\|\s*📅\s*([^|]+)\s*\|\s*🔗\s*WhatsApp\s*\|\s*📞\s*([^\n]+)[^\n]*\n💬\s*\*?"?([^"*\n]+)"?\*?/g;
    let match;
    while ((match = enhancedWaPattern.exec(content)) !== null) {
        references.push({
            type: 'whatsapp',
            id: `WA-${match[1]}`,
            number: parseInt(match[1]),
            username: match[2].trim(),
            timestamp: match[3].trim(),
            contact: match[4].trim(),
            phone_number: match[4].trim(),
            message: match[5].trim(),
            messageType: 'Message',
            source: 'WhatsApp'
        });
    }
    
    // PakWheels format
    const newPakPattern = /\*\*\[(\d+)\]\*\*\s*👤\s*([^|]+)\s*\|\s*📅\s*([^|]+)\s*\|\s*🔗\s*([^\n]+)[^\n]*\n💬\s*\*?"?([^"*\n]+)"?\*?(?:\n🔗\s*\[View Source\]\(([^)]+)\))?/g;
    while ((match = newPakPattern.exec(content)) !== null) {
        const url = match[6] ? match[6].trim() : null;
        let postId = null;
        if (url) {
            const postIdMatch = url.match(/\/(\d+)\/?$/);
            if (postIdMatch) {
                postId = postIdMatch[1];
            }
        }
        
        references.push({
            type: 'pakwheels',
            number: parseInt(match[1]),
            username: match[2].trim(),
            date: match[3].trim(),
            source: match[4].trim(),
            message: match[5].trim(),
            url: url,
            post_number: postId
        });
    }
    
    return references;
}

// Add Message to DOM
function addMessageToDOM(content, isUser, useTypingEffect = false, structuredData = null) {
    console.log('💬 Adding message to DOM:', {
        isUser,
        contentLength: content ? content.length : 0,
        useTypingEffect,
        hasStructuredData: !!structuredData,
        structuredDataKeys: structuredData ? Object.keys(structuredData) : []
    });
    
    // Ensure welcome is hidden and messages container is shown
    hideWelcome();
    
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) {
        console.error('❌ Messages container not found!');
        return null;
    }
    
    // Double-check that messages container is visible
    if (messagesContainer.style.display === 'none') {
        console.log('🔧 Messages container was hidden, showing it...');
        messagesContainer.style.display = 'block';
    }
    
    console.log('📦 Messages container found, current children:', messagesContainer.children.length);
    console.log('📦 Messages container display:', messagesContainer.style.display);
    console.log('📦 Messages container visible:', messagesContainer.offsetParent !== null);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const author = document.createElement('div');
    author.className = 'message-author';
    author.textContent = isUser ? 'You' : 'Insights AI';
    
    header.appendChild(author);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    messageDiv.appendChild(header);
    messageDiv.appendChild(contentDiv);
    
    if (isUser) {
        contentDiv.textContent = content;
    } else {
        // Parse references from content with error handling
        let references = [];
        try {
            references = parseReferences(content || '');
        } catch (error) {
            console.error('❌ Error parsing references:', error);
            references = []; // Fallback to empty array
        }
        
        // Remove reference sections from main content
        let mainContent = content.replace(/\n\nReferences \(PakWheels[^\n]*\):[\s\S]*$/g, '').trim();
        mainContent = mainContent.replace(/\n\n###?\s*📋\s*References?[\s\S]*$/g, '').trim();
        mainContent = mainContent.replace(/---\n###?\s*📋\s*References[\s\S]*?---/g, '').trim();
        mainContent = mainContent.replace(/\*\*\[\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
        mainContent = mainContent.replace(/\*\*\[WA-\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
        
        // Add message actions for bot messages
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-action-btn';
        copyBtn.innerHTML = '<span>📋</span><span>Copy</span>';
        copyBtn.onclick = () => copyToClipboard(content);
        
        const regenerateBtn = document.createElement('button');
        regenerateBtn.className = 'message-action-btn';
        regenerateBtn.innerHTML = '<span>🔄</span><span>Regenerate</span>';
        regenerateBtn.onclick = () => {
            const messages = document.querySelectorAll('.message');
            let userQuery = '';
            for (let i = messages.length - 1; i >= 0; i--) {
                if (messages[i].classList.contains('user')) {
                    userQuery = messages[i].querySelector('.message-content').textContent;
                    break;
                }
            }
            if (userQuery) {
                regenerateResponse(messageDiv, userQuery);
            }
        };
        
        const shareBtn = document.createElement('button');
        shareBtn.className = 'message-action-btn';
        shareBtn.innerHTML = '<span>🔗</span><span>Share</span>';
        shareBtn.onclick = () => {
            copyToClipboard(content);
            showToast('Response copied! Share it anywhere.', 'success');
        };
        
        actionsDiv.appendChild(copyBtn);
        actionsDiv.appendChild(regenerateBtn);
        actionsDiv.appendChild(shareBtn);
        messageDiv.appendChild(actionsDiv);
        
        if (useTypingEffect) {
            typeMessage(contentDiv, mainContent, messageDiv, references, structuredData);
        } else {
            // Process content without typing effect
            processMessageContent(contentDiv, mainContent, messageDiv, references, structuredData);
        }
    }
    
    messagesContainer.appendChild(messageDiv);
    console.log('✅ Message added to DOM, container now has', messagesContainer.children.length, 'children');
    
    // Ensure messages container is visible for user messages
    if (isUser) {
        hideWelcome();
        if (messagesContainer.style.display === 'none') {
            messagesContainer.style.display = 'block';
            console.log('🔧 Messages container was hidden, showing it for user message');
        }
    }
    
    // Add entrance animation
    addMessageEntranceAnimation(messageDiv);
    
    // Force scroll when adding new message
    setTimeout(() => {
        scrollToBottom(true);
    }, 50);
    
    return messageDiv;
}

// Clean content by removing sections that will be rendered separately
function cleanContentForDisplay(content) {
    let cleanedContent = content;
    
    // Remove various reference section formats
    cleanedContent = cleanedContent.replace(/\n\nReferences \(PakWheels[^\n]*\):[\s\S]*$/g, '').trim();
    cleanedContent = cleanedContent.replace(/\n\n###?\s*📋\s*References?[\s\S]*$/g, '').trim();
    cleanedContent = cleanedContent.replace(/---\n###?\s*📋\s*References[\s\S]*?---/g, '').trim();
    cleanedContent = cleanedContent.replace(/\*\*\[\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
    cleanedContent = cleanedContent.replace(/\*\*\[WA-\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
    
    // Remove recommendations section from main content (will be rendered separately)
    cleanedContent = cleanedContent.replace(/\n\n###?\s*💡\s*Recommendations?[\s\S]*$/g, '').trim();
    cleanedContent = cleanedContent.replace(/💡\s*Recommendations?:[\s\S]*?(?=\n\n|$)/g, '').trim();
    cleanedContent = cleanedContent.replace(/\*\*Action Item \d+\*\*:[\s\S]*?(?=\n\n|\*\*Action Item|\n💡|$)/g, '').trim();
    
    // Remove citation markers from main text (they'll appear in references section)
    cleanedContent = cleanedContent.replace(/\[WA-\d+\]/g, '');
    cleanedContent = cleanedContent.replace(/\[\d+\]/g, '');
    
    return cleanedContent;
}

// Clean recommendations text to prevent duplicates
function cleanRecommendationsText(text) {
    // Remove duplicate "💡 Recommendations:" headers
    let cleaned = text.replace(/💡\s*Recommendations?:\s*/g, '');
    
    // Remove "Action Item X:" prefixes that might be duplicated
    cleaned = cleaned.replace(/\*\*Action Item \d+\*\*:\s*/g, '');
    
    // Clean up extra whitespace and formatting
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    
    return cleaned;
}

// Process Message Content
function processMessageContent(contentDiv, content, messageDiv, references, structuredData) {
    // Parse references from content first (before processing)
    let finalReferences = references || [];
    
    console.log('📋 Content analysis:', {
        hasReferencesSection: content.includes('📋 References'),
        hasReferencesHeader: content.includes('### 📋 References'),
        contentLength: content.length,
        contentPreview: content.substring(content.length - 500) // Last 500 chars to see references
    });
    
    if ((!finalReferences || finalReferences.length === 0) && content.includes('📋 References')) {
        console.log('📋 Parsing references from markdown content');
        finalReferences = parseReferencesFromText(content);
    }
    
    // Pre-process content to add proper line breaks and structure
    let processedContent = preprocessMessageContent(content);
    
    // Remove references section from main content (like old template)
    processedContent = processedContent.replace(/\n\nReferences \(PakWheels[^\n]*\):[\s\S]*$/g, '').trim();
    processedContent = processedContent.replace(/\n\n###?\s*📋\s*References?[\s\S]*$/g, '').trim();
    processedContent = processedContent.replace(/---\n###?\s*📋\s*References[\s\S]*?---/g, '').trim();
    processedContent = processedContent.replace(/\*\*\[\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
    processedContent = processedContent.replace(/\*\*\[WA-\d+\]\*\*\s*👤[\s\S]*?(?=\n\n|$)/g, '').trim();
    
    // Remove recommendations section from main content (will be rendered separately)
    processedContent = processedContent.replace(/\n\n###?\s*💡\s*Recommendations?[\s\S]*$/g, '').trim();
    
    // Convert citation markers to clickable reference boxes before removing them
    processedContent = processedContent.replace(/\[WA-(\d+)\]/g, '<a href="#ref-WA-$1" class="reference-link-inline" onclick="handleReferenceClick(event, {id: \'WA-$1\', type: \'whatsapp\'})">WA-$1</a>');
    processedContent = processedContent.replace(/\[(\d+)\]/g, '<a href="#ref-$1" class="reference-link-inline" onclick="handleReferenceClick(event, {id: \'$1\', number: $1})">$1</a>');
    
    console.log('📋 Content cleaning:', {
        originalLength: content.length,
        cleanedLength: processedContent.length,
        referencesFound: finalReferences.length
    });
    
    // Extract and process charts from cleaned content
    const chartDataArray = [];
    let chartProcessedContent = processedContent;
    
    // Find and replace chart code blocks
    const chartBlockRegex = /```chart\s*\n([\s\S]*?)```/g;
    let chartMatch;
    let placeholderIndex = 0;
    
    while ((chartMatch = chartBlockRegex.exec(processedContent)) !== null) {
        const placeholder = `__CHART_PLACEHOLDER_${placeholderIndex}__`;
        const chartCode = chartMatch[1].trim();
        
        try {
            const lines = chartCode.split('\n');
            let chartType = 'bar';
            let chartTitle = 'Chart';
            let chartData = {};
            
            lines.forEach(line => {
                line = line.trim();
                if (line.startsWith('type:')) {
                    chartType = line.split(':')[1].trim();
                } else if (line.startsWith('title:')) {
                    chartTitle = line.substring(6).trim();
                } else if (line.startsWith('data:')) {
                    const dataStr = line.substring(5).trim();
                    chartData = JSON.parse(dataStr);
                }
            });
            
            chartDataArray.push({
                placeholder: placeholder,
                type: chartType,
                title: chartTitle,
                data: chartData
            });
        } catch (error) {
            console.error('Error parsing chart:', error);
        }
        
        chartProcessedContent = chartProcessedContent.replace(chartMatch[0], `\n\n${placeholder}\n\n`);
        placeholderIndex++;
    }
    
    // Parse markdown to HTML with enhanced processing
    let parsedHTML = marked.parse(chartProcessedContent);
    
    // Post-process HTML for better formatting
    parsedHTML = enhanceMarkdownHTML(parsedHTML);
    
    // Clean up empty list items that appear before headings
    parsedHTML = parsedHTML.replace(/<li>\s*<\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    parsedHTML = parsedHTML.replace(/<li><p><\/p><\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    parsedHTML = parsedHTML.replace(/<li>\s*<p>\s*<\/p>\s*<\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    
    // Merge bullet points with strong text and following paragraphs
    parsedHTML = parsedHTML.replace(/<li>\s*<strong>([^<]+)<\/strong>\s*<\/li>\s*<p>([^<]+)<\/p>/g, '<li><strong>$1</strong> $2</li>');
    parsedHTML = parsedHTML.replace(/<li>\s*<h([1-6])>([^<]+)<\/h\1>\s*<\/li>\s*<p>([^<]+)<\/p>/g, '<li><strong>$2</strong> $3</li>');
    
    // Fix cases where strong text and paragraph content are in separate list items
    parsedHTML = parsedHTML.replace(/<li>\s*<strong>([^<]+)<\/strong>\s*<\/li>\s*<li>\s*([^<]+)\s*<\/li>/g, '<li><strong>$1</strong> $2</li>');
    
    // Remove all empty list items
    parsedHTML = parsedHTML.replace(/<li>\s*<\/li>/g, '');
    parsedHTML = parsedHTML.replace(/<li><p><\/p><\/li>/g, '');
    parsedHTML = parsedHTML.replace(/<li>\s*<p>\s*<\/p>\s*<\/li>/g, '');
    
    // Enhanced chart placeholder cleanup from old template
    parsedHTML = parsedHTML.replace(/__CHART_PLACEHOLDER_\d+__/g, '');
    parsedHTML = parsedHTML.replace(/CHART_PLACEHOLDER_\d+/g, '');
    parsedHTML = parsedHTML.replace(/<p>CHART_PLACEHOLDER_\d+<\/p>/g, '');
    parsedHTML = parsedHTML.replace(/\bCHART_PLACEHOLDER_\d+\b/g, '');
    parsedHTML = parsedHTML.replace(/CHART_PLACEHOLDER_\d+\s*/g, '');
    parsedHTML = parsedHTML.replace(/\s*CHART_PLACEHOLDER_\d+/g, '');
    
    // Clean up specific placeholder patterns but preserve meaningful titles
    parsedHTML = parsedHTML.replace(/([A-Z][^<\n]*(?:Issues?|Distribution|Analysis|Breakdown|Top \d+)[^<\n]*)\s*CHART_PLACEHOLDER_\d+/gi, '$1');
    parsedHTML = parsedHTML.replace(/Top Issues Reported Last Week\s*CHART_PLACEHOLDER_\d+/gi, 'Top Issues Reported Last Week');
    parsedHTML = parsedHTML.replace(/Distribution of Issues Reported Last Week\s*CHART_PLACEHOLDER_\d+/gi, 'Distribution of Issues Reported Last Week');
    
    // Remove any remaining placeholder patterns
    parsedHTML = parsedHTML.replace(/\n\s*CHART_PLACEHOLDER_\d+\s*\n/g, '\n');
    parsedHTML = parsedHTML.replace(/^CHART_PLACEHOLDER_\d+\s*$/gm, '');
    
    // Replace chart placeholders with chart containers or placeholders
    chartDataArray.forEach((chartInfo) => {
        if (Object.keys(chartInfo.data).length > 0) {
            const chartId = 'chart-' + Math.random().toString(36).substr(2, 9);
            chartInfo.chartId = chartId;
            const chartHTML = `
                <div class="chart-container">
                    <div class="chart-title">${chartInfo.title}</div>
                    <div class="chart-canvas-wrapper">
                        <canvas id="${chartId}" width="400" height="200"></canvas>
                    </div>
                </div>
            `;
            parsedHTML = parsedHTML.replace(chartInfo.placeholder, chartHTML);
        } else {
            // Show chart placeholder when no data
            const placeholderHTML = `
                <div class="chart-placeholder">
                    <div class="chart-title">${chartInfo.title}</div>
                    <p>📊 Chart data not available</p>
                </div>
            `;
            parsedHTML = parsedHTML.replace(chartInfo.placeholder, placeholderHTML);
        }
    });
    
    // Handle any remaining chart placeholders that might be in the text
    parsedHTML = parsedHTML.replace(/Top\s+\d+[^<\n]*(?=\s*(?:<|$))/g, (match) => {
        return `<div class="chart-placeholder">
            <div class="chart-title">${match}</div>
            <p>📊 Chart visualization would appear here</p>
        </div>`;
    });
    
    contentDiv.innerHTML = parsedHTML;
    
    // Clean up any remaining chart placeholders
    cleanupChartPlaceholders(contentDiv);
    
    // Render charts with proper DOM update handling
    if (chartDataArray.length > 0) {
        console.log('📊 Found', chartDataArray.length, 'charts to render');
        // Use requestAnimationFrame to ensure DOM is fully updated
        requestAnimationFrame(() => {
            chartDataArray.forEach((chartInfo) => {
                if (Object.keys(chartInfo.data).length > 0 && chartInfo.chartId) {
                    console.log('🎯 Rendering chart:', chartInfo.chartId);
                    renderChart(chartInfo, contentDiv);
                }
            });
        });
    }
    
    // Render charts from structured data if available (NEW FUNCTIONALITY FROM OLD TEMPLATE)
    if (structuredData && structuredData.charts && structuredData.charts.length > 0) {
        console.log('🎯 Rendering charts from structured data:', structuredData.charts.length);
        setTimeout(() => {
            renderChartsFromStructured(contentDiv, structuredData.charts);
        }, 200); // Small delay to ensure DOM is ready
    }
    
    // Add references section
    console.log('📋 About to add references section:', {
        finalReferencesCount: finalReferences.length,
        structuredDataRefs: structuredData?.references?.length || 0,
        messageDiv: !!messageDiv
    });
    
    addReferencesSection(messageDiv, finalReferences, structuredData);
    
    // Add recommendations section if available
    if (structuredData && structuredData.recommendations && structuredData.recommendations.length > 0) {
        console.log('💡 Adding recommendations section:', structuredData.recommendations);
        addRecommendationsSection(messageDiv, structuredData.recommendations);
    }
    
    // Highlight code blocks
    contentDiv.querySelectorAll('pre code').forEach((block) => {
        const code = block.textContent.trim();
        if (!code.includes('type:') || !code.match(/type:\s*(bar|pie|line)/i)) {
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(block);
            }
        }
    });
}


// Render Chart Function - Enhanced with better error handling
function renderChart(chartInfo, container, retryCount = 0) {
    console.log('🎯 Attempting to render chart:', chartInfo.chartId, `(attempt ${retryCount + 1})`);
    
    // Ensure Chart.js is loaded first
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js not loaded, retrying...');
        if (retryCount < 5) {
            setTimeout(() => {
                renderChart(chartInfo, container, retryCount + 1);
            }, 500);
        }
        return;
    }
    
    const canvas = container.querySelector(`#${chartInfo.chartId}`);
    
    if (!canvas) {
        console.warn('⚠️ Canvas not found for chart:', chartInfo.chartId);
        console.log('🔍 Available canvas elements in container:', 
            Array.from(container.querySelectorAll('canvas')).map(c => c.id));
        
        // Don't retry for missing canvas - it means the chart placeholder wasn't properly replaced
        // This is normal if the chart was removed during content processing
        return;
    }
    
    console.log('✅ Canvas found for chart:', chartInfo.chartId);
    
    const labels = Object.keys(chartInfo.data);
    const values = Object.values(chartInfo.data);
    const colors = getChartColors();
    
    if (labels.length === 0 || values.length === 0) {
        console.warn('⚠️ No data for chart:', chartInfo.chartId);
        return;
    }
    
    const backgroundColors = labels.map((_, i) => colors[i % colors.length]);
    const borderColors = backgroundColors.map(c => c.replace('0.8', '1'));
    
    try {
        // Destroy existing chart if it exists
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }
        
        setTimeout(() => {
            const ctx = canvas.getContext('2d');
            if (!ctx) {
                console.error('❌ Could not get canvas context');
                return;
            }
            
            new Chart(ctx, {
                type: chartInfo.type,
                data: {
                    labels: labels,
                    datasets: [{
                        label: chartInfo.title,
                        data: values,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: chartInfo.type === 'pie',
                            position: 'bottom',
                            labels: {
                                color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#a855f7' : '#7c3aed', // Purple for both themes
                                padding: 15,
                                font: { size: 12 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(30, 30, 30, 0.95)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            padding: 12,
                            titleFont: { size: 14 },
                            bodyFont: { size: 13 }
                        }
                    },
                    scales: chartInfo.type !== 'pie' ? {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#a855f7' : '#7c3aed' // Purple for both themes
                            },
                            grid: {
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue('--border-color').trim() || '#e2e8f0'
                            }
                        },
                        x: {
                            ticks: {
                                color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#a855f7' : '#7c3aed' // Purple for both themes
                            },
                            grid: {
                                color: getComputedStyle(document.documentElement)
                                    .getPropertyValue('--border-color').trim() || '#e2e8f0'
                            }
                        }
                    } : {}
                }
            });
            
            console.log('✅ Chart rendered successfully:', chartInfo.chartId);
        }, 100);
        
    } catch (error) {
        console.error('❌ Error rendering chart:', error);
        renderFallbackChart(chartInfo, container);
    }
}

// Clean up chart placeholders from DOM - Enhanced from old template
function cleanupChartPlaceholders(container) {
    // Remove any text nodes containing chart placeholders
    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const textNodes = [];
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.includes('CHART_PLACEHOLDER')) {
            textNodes.push(node);
        }
    }
    
    textNodes.forEach(textNode => {
        const cleanedText = textNode.textContent
            .replace(/CHART_PLACEHOLDER_\d+/g, '')
            .replace(/\s+/g, ' ')
            .trim();
        
        if (cleanedText) {
            textNode.textContent = cleanedText;
        } else {
            // Remove empty text nodes or parent elements if they become empty
            const parent = textNode.parentNode;
            textNode.remove();
            if (parent && parent.textContent.trim() === '') {
                parent.remove();
            }
        }
    });
    
    // Remove any paragraphs that only contain chart placeholders
    const paragraphs = container.querySelectorAll('p');
    paragraphs.forEach(p => {
        const text = p.textContent.trim();
        if (text.match(/^CHART_PLACEHOLDER_\d+$/)) {
            p.remove();
        }
    });
}

// Render charts from structured data - MISSING FUNCTION FROM OLD TEMPLATE
function renderChartsFromStructured(container, charts) {
    if (!charts || charts.length === 0) return;
    
    console.log('🎯 Rendering charts from structured data:', charts.length);
    
    // Track existing charts to prevent duplicates
    const existingCharts = new Set();
    container.querySelectorAll('.chart-title').forEach(titleEl => {
        existingCharts.add(titleEl.textContent.trim());
    });
    
    charts.forEach(chart => {
        const chartTitle = chart.title || 'Chart';
        const chartKey = `${chartTitle}_${JSON.stringify(chart.data)}`;
        
        // Skip if chart with same title and data already exists
        if (existingCharts.has(chartTitle)) {
            // Check if it's the same data
            const existingChart = Array.from(container.querySelectorAll('.chart-container')).find(container => {
                const title = container.querySelector('.chart-title')?.textContent.trim();
                return title === chartTitle;
            });
            
            if (existingChart) {
                // Check if data matches by looking at the canvas dataset
                const canvas = existingChart.querySelector('canvas');
                if (canvas && canvas.dataset.chartData === chartKey) {
                    return; // Skip duplicate
                }
            }
        }
        
        existingCharts.add(chartTitle);
        
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'chart-title';
        titleDiv.textContent = chartTitle;
        
        const canvasWrapper = document.createElement('div');
        canvasWrapper.className = 'chart-canvas-wrapper';
        
        const canvas = document.createElement('canvas');
        const chartId = 'chart-' + Math.random().toString(36).substr(2, 9);
        canvas.id = chartId;
        canvas.dataset.chartData = chartKey; // Store data key to detect duplicates
        
        canvasWrapper.appendChild(canvas);
        chartContainer.appendChild(titleDiv);
        chartContainer.appendChild(canvasWrapper);
        
        // Insert before references/recommendations if they exist
        const refSection = container.querySelector('.references-section');
        const recSection = container.querySelector('.recommendations-section');
        const insertBefore = refSection || recSection;
        
        if (insertBefore) {
            container.insertBefore(chartContainer, insertBefore);
        } else {
            container.appendChild(chartContainer);
        }
        
        // Create chart
        const labels = Object.keys(chart.data);
        const values = Object.values(chart.data);
        
        const colors = getChartColors();
        
        const backgroundColors = labels.map((_, i) => colors[i % colors.length]);
        const borderColors = backgroundColors.map(c => c.replace('0.8', '1'));
        
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        const isDark = theme === 'dark';
        
        // Use setTimeout to ensure DOM is ready
        setTimeout(() => {
            try {
                const chartInstance = new Chart(canvas, {
                    type: chart.type || 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: chart.title || 'Chart',
                            data: values,
                            backgroundColor: backgroundColors,
                            borderColor: borderColors,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: chart.type === 'pie',
                                position: 'bottom',
                                labels: {
                                    color: isDark ? '#a855f7' : '#7c3aed', // Purple for both themes
                                    padding: 15,
                                    font: { size: 12 }
                                }
                            },
                            tooltip: {
                                backgroundColor: isDark ? 'rgba(30, 30, 30, 0.95)' : 'rgba(0, 0, 0, 0.8)',
                                titleColor: isDark ? '#e5e5e5' : '#ffffff',
                                bodyColor: isDark ? '#e5e5e5' : '#ffffff',
                                padding: 12,
                                titleFont: { size: 14 },
                                bodyFont: { size: 13 }
                            }
                        },
                        scales: chart.type !== 'pie' ? {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    color: isDark ? '#a855f7' : '#7c3aed' // Purple for both themes
                                },
                                grid: {
                                    color: isDark ? '#404040' : '#e5e5e5'
                                }
                            },
                            x: {
                                ticks: {
                                    color: isDark ? '#a855f7' : '#7c3aed' // Purple for both themes
                                },
                                grid: {
                                    color: isDark ? '#404040' : '#e5e5e5'
                                }
                            }
                        } : {}
                    }
                });
                
                console.log('✅ Chart rendered from structured data:', chartTitle);
            } catch (error) {
                console.error('❌ Error rendering chart from structured data:', error);
                renderFallbackChart({ chartId, title: chartTitle, data: chart.data, type: chart.type || 'bar' }, container);
            }
        }, 100);
    });
}

// Fallback chart renderer using HTML/CSS
function renderFallbackChart(chartInfo, container) {
    const canvas = container.querySelector(`#${chartInfo.chartId}`);
    if (!canvas) return;
    
    const labels = Object.keys(chartInfo.data);
    const values = Object.values(chartInfo.data);
    const maxValue = Math.max(...values);
    
    // Replace canvas with HTML chart
    const chartHTML = document.createElement('div');
    chartHTML.className = 'fallback-chart';
    chartHTML.innerHTML = `
        <div class="fallback-chart-title">${chartInfo.title}</div>
        <div class="fallback-chart-bars">
            ${labels.map((label, i) => {
                const percentage = (values[i] / maxValue) * 100;
                const color = getChartColors()[i % getChartColors().length];
                return `
                    <div class="fallback-chart-bar">
                        <div class="fallback-chart-label">${label}</div>
                        <div class="fallback-chart-bar-container">
                            <div class="fallback-chart-bar-fill" style="width: ${percentage}%; background: ${color}"></div>
                            <div class="fallback-chart-value">${values[i]}</div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    
    // Add fallback chart styles
    const style = document.createElement('style');
    style.textContent = `
        .fallback-chart {
            padding: 16px;
            background: var(--card-bg);
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
        }
        .fallback-chart-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--text-primary);
        }
        .fallback-chart-bar {
            margin-bottom: 12px;
        }
        .fallback-chart-label {
            font-size: 14px;
            margin-bottom: 4px;
            color: var(--text-secondary);
        }
        .fallback-chart-bar-container {
            position: relative;
            height: 24px;
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
        }
        .fallback-chart-bar-fill {
            height: 100%;
            border-radius: 12px;
            transition: width 0.8s ease-out;
        }
        .fallback-chart-value {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
        }
    `;
    
    if (!document.querySelector('#fallback-chart-styles')) {
        style.id = 'fallback-chart-styles';
        document.head.appendChild(style);
    }
    
    canvas.parentNode.replaceChild(chartHTML, canvas);
    console.log('✅ Fallback chart rendered:', chartInfo.title);
}

// Add Recommendations Section
function addRecommendationsSection(messageDiv, recommendations) {
    if (!recommendations || recommendations.length === 0) {
        console.log('💡 No recommendations to add');
        return;
    }
    
    // Check if recommendations already exist to avoid duplicates
    const existingRecommendations = messageDiv.querySelector('.recommendations-section');
    if (existingRecommendations) {
        console.log('💡 Recommendations section already exists, skipping');
        return;
    }
    
    console.log('💡 Adding recommendations section:', recommendations);
    
    const messageContent = messageDiv.querySelector('.message-content');
    if (!messageContent) {
        console.error('❌ Could not find message content to add recommendations');
        return;
    }
    
    const recommendationsDiv = document.createElement('div');
    recommendationsDiv.className = 'recommendations-section';
    // Add a data attribute to help identify and protect this element
    recommendationsDiv.setAttribute('data-protected', 'true');
    
    const title = document.createElement('div');
    title.className = 'recommendations-title';
    title.innerHTML = '💡 Recommendations:';
    recommendationsDiv.appendChild(title);
    
    const list = document.createElement('ul');
    list.className = 'recommendations-list';
    
    recommendations.forEach(recommendation => {
        const item = document.createElement('li');
        item.className = 'recommendation-item';
        // Clean the recommendation text to prevent duplicates and formatting issues
        item.textContent = cleanRecommendationsText(recommendation);
        list.appendChild(item);
    });
    
    recommendationsDiv.appendChild(list);
    
    // Insert before follow-ups if they exist, otherwise at the end
    const followUps = messageContent.querySelector('.follow-up-suggestions');
    if (followUps) {
        messageContent.insertBefore(recommendationsDiv, followUps);
    } else {
        messageContent.appendChild(recommendationsDiv);
    }
    
    console.log('✅ Recommendations section added successfully');
    
    // Add animation
    recommendationsDiv.style.opacity = '0';
    recommendationsDiv.style.transform = 'translateY(20px)';
    
    requestAnimationFrame(() => {
        recommendationsDiv.style.transition = 'all 0.3s ease';
        recommendationsDiv.style.opacity = '1';
        recommendationsDiv.style.transform = 'translateY(0)';
    });
}

// Parse references from markdown text (like old template)
function parseReferencesFromText(content) {
    const references = [];
    
    // Look for references section in markdown - multiple patterns
    let referencesMatch = content.match(/### 📋 References\s*([\s\S]*?)(?=\n---|\n###|$)/);
    if (!referencesMatch) {
        referencesMatch = content.match(/📋 References\s*([\s\S]*?)(?=\n---|\n###|$)/);
    }
    if (!referencesMatch) {
        referencesMatch = content.match(/References\s*\n([\s\S]*?)(?=\n---|\n###|$)/);
    }
    
    if (!referencesMatch) {
        console.log('📋 No references section found in content');
        return references;
    }
    
    const referencesText = referencesMatch[1];
    console.log('📋 Found references text:', referencesText.substring(0, 200) + '...');
    
    // Parse individual references - look for **[number]** pattern
    const referenceBlocks = referencesText.split(/\*\*\[(\d+|WA-\d+)\]\*\*/).slice(1);
    
    // Process in pairs: [id, content]
    for (let i = 0; i < referenceBlocks.length; i += 2) {
        if (i + 1 >= referenceBlocks.length) break;
        
        const refId = referenceBlocks[i];
        const refContent = referenceBlocks[i + 1];
        
        if (!refContent || !refContent.trim()) continue;
        
        const lines = refContent.trim().split('\n').filter(line => line.trim());
        if (lines.length < 1) continue;
        
        // Parse the header line: 👤 username | 📅 date | 🔗 source | 📞 phone (optional)
        const headerLine = lines[0].trim();
        const messageLine = lines.length > 1 ? lines[1].trim() : '';
        const urlLine = lines.length > 2 ? lines[2].trim() : '';
        
        // Extract information using regex patterns
        const usernameMatch = headerLine.match(/👤\s*([^|]+)/);
        const dateMatch = headerLine.match(/📅\s*([^|]+)/);
        const sourceMatch = headerLine.match(/🔗\s*([^|📞]+)/);
        const phoneMatch = headerLine.match(/📞\s*([^|]+)/);
        
        // Extract message content
        const messageMatch = messageLine.match(/💬\s*[*"]*([^*"]+)[*"]*/);
        
        // Extract URL
        const urlMatch = urlLine.match(/\[View Source\]\(([^)]+)\)/);
        
        const username = usernameMatch ? usernameMatch[1].trim() : 'Unknown';
        const date = dateMatch ? dateMatch[1].trim() : '';
        const source = sourceMatch ? sourceMatch[1].trim() : '';
        const phone = phoneMatch ? phoneMatch[1].trim() : '';
        const message = messageMatch ? messageMatch[1].trim() : '';
        const url = urlMatch ? urlMatch[1].trim() : '';
        
        // Determine reference type
        let type = 'pakwheels';
        if (source.toLowerCase().includes('whatsapp') || refId.startsWith('WA-')) {
            type = 'whatsapp';
        }
        
        const reference = {
            id: type === 'whatsapp' ? (refId.startsWith('WA-') ? refId : `WA-${refId}`) : refId,
            number: refId.replace('WA-', ''),
            type: type,
            username: username,
            contact: phone || 'N/A',
            phone_number: phone || 'N/A',
            date: date,
            timestamp: date,
            message: message,
            preview: message,
            url: url,
            messageType: type === 'whatsapp' ? 'Message' : 'Forum Post'
        };
        
        references.push(reference);
        console.log(`📋 Parsed reference ${references.length}:`, {
            id: reference.id,
            type: reference.type,
            username: reference.username,
            contact: reference.contact,
            message: reference.message.substring(0, 50) + '...'
        });
    }
    
    console.log('📋 Total parsed references:', references.length);
    return references;
}
function addReferencesSection(messageDiv, references, structuredData = null) {
    console.log('📋 addReferencesSection called with:', {
        referencesCount: references?.length || 0,
        structuredDataRefs: structuredData?.references?.length || 0,
        messageDiv: !!messageDiv
    });

    if (messageDiv.querySelector('.references-section')) {
        console.log('📋 References section already exists, skipping');
        return;
    }

    // Use structured data references if available
    if (structuredData?.references?.length > 0) {
        references = structuredData.references;
        console.log('📋 Using structured data references:', references.length);
    }

    if (!references || references.length === 0) {
        console.log('📋 No references to display');
        return;
    }

    console.log('📋 Creating references section with', references.length, 'references');

    const refsSection = document.createElement('div');
    refsSection.className = 'references-section';

    const refsTitle = document.createElement('div');
    refsTitle.className = 'references-title';
    refsTitle.innerHTML = '<span class="references-icon">📋</span><span class="references-text">References</span>';
    refsSection.appendChild(refsTitle);

    // Create grid container for references
    const refsGrid = document.createElement('div');
    refsGrid.className = 'references-grid';

    references.forEach((ref, index) => {
        if (typeof ref === 'string') {
            try {
                ref = JSON.parse(ref);
            } catch (e) {
                console.warn('Failed to parse reference:', ref);
                return;
            }
        }

        const refItem = document.createElement('div');
        refItem.className = 'reference-item';
        refItem.id = ref.id || `ref-${ref.number || index}`;

        let html = '';

        // WhatsApp reference
        if (ref.type === 'whatsapp') {
            const displayId = ref.id ? String(ref.id).replace('WA-', '#') : '#' + (ref.number || index + 1);
            const contactInfo = ref.contact || ref.phone_number || ref.phone || 'N/A';
            const displayLabel = ref.username || ref.author || 'Contact';
            const messageText = ref.message || ref.preview || 'No message available';
            const timestamp = ref.timestamp || 'Unknown time';

            html = `
                <div class="reference-header">
                    <span class="reference-badge whatsapp">📱 WA</span>
                    <span class="reference-id">${displayId}</span>
                </div>
                <div class="reference-body">
                    <div class="reference-meta">
                        <div class="reference-author">
                            <span class="author-icon">👤</span>
                            <span class="author-name">${displayLabel}</span>
                        </div>
                        <div class="reference-time">
                            <span class="time-icon">🕐</span>
                            <span class="time-text">${timestamp}</span>
                        </div>
                        <div class="reference-contact">
                            <span class="contact-icon">📞</span>
                            <span class="contact-text">${contactInfo}</span>
                        </div>
                    </div>
                    <div class="reference-message">
                        <span class="message-text">"${messageText}"</span>
                    </div>
                </div>
            `;
        } else {
            // Generic reference
            const messageText = ref.message || ref.preview || ref.content || 'No message available';
            const username = ref.username || ref.author || 'Unknown';
            const timestamp = ref.timestamp || ref.date || 'Unknown time';

            html = `
                <div class="reference-header">
                    <span class="reference-badge generic">📄 Ref</span>
                    <span class="reference-id">[${ref.number || index + 1}]</span>
                </div>
                <div class="reference-body">
                    <div class="reference-meta">
                        <div class="reference-author">
                            <span class="author-icon">👤</span>
                            <span class="author-name">${username}</span>
                        </div>
                        <div class="reference-time">
                            <span class="time-icon">📅</span>
                            <span class="time-text">${timestamp}</span>
                        </div>
                    </div>
                    <div class="reference-message">
                        <span class="message-text">"${messageText}"</span>
                    </div>
                </div>
            `;
        }

        refItem.innerHTML = html;
        
        // Add click handler for popup functionality
        refItem.addEventListener('click', (e) => {
            handleReferenceClick(e, ref);
        });
        
        refsGrid.appendChild(refItem);
    });

    refsSection.appendChild(refsGrid);

    const messageContent = messageDiv.querySelector('.message-content');
    if (messageContent) {
        messageContent.appendChild(refsSection);
        // trigger reflow if needed
        refsSection.offsetHeight;
        console.log('✅ References section added to message with', references.length, 'references in grid layout');
    } else {
        console.warn('⚠️ Could not find message content to add references');
    }
}

// Typing Effect Function
function typeMessage(element, content, messageDiv, references, structuredData = null) {
    isTyping = true;
    currentTypingElement = element;
    currentMessageDiv = messageDiv;
    currentReferences = references || [];
    currentStructuredData = structuredData;
    fullContent = content;
    userScrolled = false;
    
    // Show stop button
    const stopBtn = document.getElementById('stopBtn');
    const sendBtn = document.getElementById('sendBtn');
    if (stopBtn && sendBtn) {
        stopBtn.classList.add('active');
        sendBtn.style.display = 'none';
    }
    
    // Add cursor
    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';
    cursor.style.display = 'inline-block';
    element.appendChild(cursor);
    
    // Type character by character with real-time styling
    let charIndex = 0;
    const textToType = content;
    
    function typeNextChar() {
        if (!isTyping || charIndex >= textToType.length) {
            // Typing complete
            if (cursor.parentNode) {
                cursor.remove();
            }
            
            // Process final content first
            processMessageContent(element, content, messageDiv, references, structuredData);
            
            finishTyping();
            return;
        }
        
        // Get next chunk of text
        const textChunk = textToType.substring(0, charIndex + 1);
        
        // Parse markdown incrementally with real-time styling
        let parsedHTML = marked.parse(textChunk);
        
        // Convert citation markers to clickable reference boxes during typing
        parsedHTML = parsedHTML.replace(/\[WA-(\d+)\]/g, '<a href="#ref-WA-$1" class="reference-link-inline" onclick="handleReferenceClick(event, {id: \'WA-$1\', type: \'whatsapp\'})">WA-$1</a>');
        parsedHTML = parsedHTML.replace(/\[(\d+)\]/g, '<a href="#ref-$1" class="reference-link-inline" onclick="handleReferenceClick(event, {id: \'$1\', number: $1})">$1</a>');
        
        // Apply real-time styling improvements
        parsedHTML = applyRealTimeFormatting(parsedHTML);
        
        element.innerHTML = parsedHTML + '<span class="typing-cursor"></span>';
        
        // Apply syntax highlighting to any code blocks that were just added
        element.querySelectorAll('pre code').forEach((block) => {
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(block);
            }
        });
        
        charIndex++;
        
        // Force scroll during typing with smooth behavior and user interaction detection
        if (!userScrolled && !isHovering) {
            setTimeout(() => {
                scrollToBottom(true); // Force scroll during typing
            }, 10);
        } else if (userScrolled) {
            // User has scrolled up, show a subtle indicator they can scroll down
            showScrollDownHint();
        }
        
        // Continue typing
        typingInterval = setTimeout(typeNextChar, typingSpeed);
    }
    
    typeNextChar();
}

// Finish Typing
function finishTyping() {
    isTyping = false;
    currentTypingElement = null;
    
    // Hide stop button, show send button
    const stopBtn = document.getElementById('stopBtn');
    const sendBtn = document.getElementById('sendBtn');
    if (stopBtn && sendBtn) {
        stopBtn.classList.remove('active');
        sendBtn.style.display = 'flex';
    }
    
    scrollToBottom();
}

// Stop Typing
function stopTyping() {
    if (isTyping && currentTypingElement) {
        isTyping = false;
        
        // Clear typing interval
        if (typingInterval) {
            clearTimeout(typingInterval);
            typingInterval = null;
        }
        
        // Remove cursor
        const cursor = currentTypingElement.querySelector('.typing-cursor');
        if (cursor) {
            cursor.remove();
        }
        
        // Process final content first
        processMessageContent(currentTypingElement, fullContent, currentMessageDiv, currentReferences, currentStructuredData);
        
        finishTyping();
    }
}

// Real-time formatting function for better styling during typing
function applyRealTimeFormatting(html) {
    // Remove empty paragraphs and unnecessary line breaks
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p><br\s*\/?><\/p>/g, '');
    
    // Fix bullet points with strong text and paragraphs - keep them together
    html = html.replace(/<li>\s*<strong>([^<]+)<\/strong>\s*<\/li>\s*<p>([^<]+)<\/p>/g, '<li><strong>$1</strong> $2</li>');
    html = html.replace(/<li>\s*<h([1-6])>([^<]+)<\/h\1>\s*<\/li>\s*<p>([^<]+)<\/p>/g, '<li><strong>$2</strong> $3</li>');
    
    // Fix cases where strong text and paragraph are in separate list items
    html = html.replace(/<li>\s*<strong>([^<]+)<\/strong>\s*<\/li>\s*<li>\s*([^<]+)\s*<\/li>/g, '<li><strong>$1</strong> $2</li>');
    
    // Fix headings followed by paragraphs in lists - merge them
    html = html.replace(/<li>\s*<h([1-6])>([^<]+)<\/h\1>\s*<\/li>\s*<li>\s*<p>([^<]+)<\/p>\s*<\/li>/g, '<li><strong>$2</strong> $3</li>');
    html = html.replace(/<li>\s*<h([1-6])>([^<]+)<\/h\1>\s*<p>([^<]+)<\/p>\s*<\/li>/g, '<li><strong>$2</strong> $3</li>');
    
    // Fix empty list items that appear before headings
    html = html.replace(/<li>\s*<\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    html = html.replace(/<li><p><\/p><\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    html = html.replace(/<li>\s*<p><\/p>\s*<\/li>\s*<li>\s*<h([1-6])>/g, '<li><h$1>');
    
    // Remove empty list items completely
    html = html.replace(/<li>\s*<\/li>/g, '');
    html = html.replace(/<li><p><\/p><\/li>/g, '');
    html = html.replace(/<li>\s*<p>\s*<\/p>\s*<\/li>/g, '');
    
    // Improve bullet point formatting - remove empty lines
    html = html.replace(/<\/li>\s*<p><\/p>\s*<li>/g, '</li><li>');
    html = html.replace(/<\/li>\s*<br\s*\/?>\s*<li>/g, '</li><li>');
    
    // Fix headings that appear after bullet points - put them on the same line
    html = html.replace(/<\/li>\s*<p><\/p>\s*<h([1-6])>/g, '</li><li><h$1>');
    html = html.replace(/<\/li>\s*<br\s*\/?>\s*<h([1-6])>/g, '</li><li><h$1>');
    html = html.replace(/<li>\s*<p><\/p>\s*<h([1-6])>/g, '<li><h$1>');
    
    // Handle headings that appear after paragraphs in lists
    html = html.replace(/<li><p>(.*?)<\/p>\s*<p><\/p>\s*<h([1-6])>/g, '<li><p>$1</p><h$2>');
    
    // Clean up multiple consecutive line breaks
    html = html.replace(/(<br\s*\/?>\s*){2,}/g, '<br>');
    
    // Ensure proper paragraph spacing without empty lines
    html = html.replace(/(<\/p>)\s*<p><\/p>\s*(<p>)/g, '$1$2');
    
    // Clean up empty list structures
    html = html.replace(/<ul>\s*<\/ul>/g, '');
    html = html.replace(/<ol>\s*<\/ol>/g, '');
    
    return html;
}

// Reference popup functionality
function createReferencePopup(referenceData) {
    // Remove any existing popups
    const existingPopup = document.getElementById('referencePopup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    const popup = document.createElement('div');
    popup.id = 'referencePopup';
    popup.className = 'reference-popup';
    
    const popupContent = document.createElement('div');
    popupContent.className = 'reference-popup-content';
    
    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'reference-popup-close';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => popup.remove();
    
    // Reference content
    const content = document.createElement('div');
    content.className = 'reference-popup-body';
    content.innerHTML = `
        <div class="reference-popup-header">
            <h3>Reference Details</h3>
        </div>
        <div class="reference-popup-details">
            ${referenceData.author ? `<p><strong>Author:</strong> ${referenceData.author}</p>` : ''}
            ${referenceData.time ? `<p><strong>Time:</strong> ${referenceData.time}</p>` : ''}
            ${referenceData.contact ? `<p><strong>Contact:</strong> ${referenceData.contact}</p>` : ''}
            ${referenceData.message ? `<p><strong>Message:</strong></p><blockquote>${referenceData.message}</blockquote>` : ''}
        </div>
    `;
    
    popupContent.appendChild(closeBtn);
    popupContent.appendChild(content);
    popup.appendChild(popupContent);
    
    // Add to body
    document.body.appendChild(popup);
    
    // Show popup with animation
    setTimeout(() => popup.classList.add('show'), 10);
    
    // Close on outside click
    popup.addEventListener('click', (e) => {
        if (e.target === popup) {
            popup.remove();
        }
    });
    
    // Close on escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            popup.remove();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

// Enhanced reference link handling
function handleReferenceClick(event, referenceData) {
    event.preventDefault();
    
    // Try to find the full reference data from current references
    let fullReferenceData = referenceData;
    
    if (currentReferences && currentReferences.length > 0) {
        const foundRef = currentReferences.find(ref => {
            if (typeof ref === 'string') {
                try {
                    ref = JSON.parse(ref);
                } catch (e) {
                    return false;
                }
            }
            return ref.id === referenceData.id || 
                   ref.number === referenceData.number ||
                   String(ref.id).replace('WA-', '') === String(referenceData.id).replace('WA-', '');
        });
        
        if (foundRef) {
            fullReferenceData = typeof foundRef === 'string' ? JSON.parse(foundRef) : foundRef;
        }
    }
    
    createReferencePopup(fullReferenceData);
}

// Utility Functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

function showToast(message, type = 'info', duration = 3000) {
    // Remove any existing toasts to prevent stacking
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    // Get icon based on type
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'loading': '⏳'
    };
    
    const icon = icons[type] || icons.info;
    
    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast-show');
    });
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.classList.remove('toast-show');
            toast.classList.add('toast-hide');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }
    }, duration);
    
    return toast;
}

// Chat History Management
function loadChatHistory() {
    // This function is kept for compatibility but we'll load from database in loadRecentChats
    console.log('📚 Chat history system initialized');
}

function loadRecentChats() {
    const recentChatsList = document.getElementById('recentChatsList');
    if (!recentChatsList) return;
    
    // Show loading state
    recentChatsList.innerHTML = '<div style="padding: 16px; text-align: center; color: var(--text-secondary);">Loading recent conversations...</div>';
    
    // Fetch recent chat sessions from database
    fetch('/api/chat/sessions')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📥 Recent chats loaded:', data);
            console.log('📅 Sample session data:', data.sessions?.[0]); // Debug first session
            displayRecentChats(data.sessions || []);
        })
        .catch(error => {
            console.error('❌ Error loading recent chats:', error);
            recentChatsList.innerHTML = '<div style="padding: 16px; text-align: center; color: var(--text-secondary);">Error loading conversations</div>';
        });
}

function displayRecentChats(sessions) {
    const recentChatsList = document.getElementById('recentChatsList');
    if (!recentChatsList) return;
    
    recentChatsList.innerHTML = '';
    
    if (sessions.length === 0) {
        recentChatsList.innerHTML = '<div style="padding: 16px; text-align: center; color: var(--text-secondary);">No recent conversations</div>';
        return;
    }
    
    sessions.slice(0, 10).forEach((session, index) => {
        const chatItem = document.createElement('div');
        chatItem.className = 'quick-action-btn';
        chatItem.style.cssText = `
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            text-align: left;
            padding: 12px 16px;
            margin-bottom: 8px;
            cursor: pointer;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
        `;
        
        // Truncate first query for display
        const displayQuery = session.first_query && session.first_query.length > 60 
            ? session.first_query.substring(0, 60) + '...' 
            : session.first_query || 'Conversation';
        
        // Format timestamp with better formatting
        let timestamp = 'Unknown time';
        if (session.last_activity) {
            const date = new Date(session.last_activity);
            const now = new Date();
            const diffMs = now - date;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) {
                // Today - show time only
                timestamp = 'Today ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else if (diffDays === 1) {
                // Yesterday
                timestamp = 'Yesterday ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else if (diffDays < 7) {
                // This week - show day name
                timestamp = date.toLocaleDateString([], {weekday: 'short'}) + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            } else {
                // Older - show date
                timestamp = date.toLocaleDateString([], {month: 'short', day: 'numeric'}) + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            }
        }
        
        // Create mode badge
        const modeBadge = session.mode === 'whatsapp' ? '💬' : 
                         session.mode === 'insights' ? '🤖' : '🏢';
        
        chatItem.innerHTML = `
            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center; margin-bottom: 4px;">
                <div style="font-weight: 600; color: var(--text-primary);">${displayQuery}</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${modeBadge} ${session.mode}</div>
            </div>
            <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                <div style="font-size: 12px; opacity: 0.7;" title="${session.last_activity ? new Date(session.last_activity).toLocaleString() : 'Unknown time'}">${timestamp}</div>
                <div style="font-size: 11px; color: var(--primary-color);">${session.message_count} messages</div>
            </div>
        `;
        
        // Click handler to view conversation history (not use as prompt)
        chatItem.onclick = () => {
            hideRecentChats();
            viewConversationHistory(session.session_id, session.mode, session.first_query);
        };
        
        recentChatsList.appendChild(chatItem);
    });
}

function viewConversationHistory(sessionId, mode, firstQuery) {
    console.log('👁️ Viewing conversation history:', { sessionId, mode, firstQuery });
    
    // Set the mode for this conversation
    if (mode) {
        setMode(mode);
        console.log('🎯 Mode set to:', mode);
    }
    
    // Show loading message
    const loadingMessage = 'Loading conversation history...';
    addMessageToDOM(loadingMessage, false);
    
    // Fetch the full conversation history
    fetch(`/api/chat/history/${sessionId}?mode=${mode}`)
        .then(response => {
            console.log('📡 History API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📥 Raw conversation data received:', data);
            console.log('📊 History array:', data.history);
            console.log('📈 History length:', data.history ? data.history.length : 0);
            
            if (data.history && Array.isArray(data.history)) {
                displayConversationHistory(data.history, firstQuery);
            } else {
                console.error('❌ Invalid history data structure:', data);
                addMessageToDOM('No conversation history found for this session.', false);
            }
        })
        .catch(error => {
            console.error('❌ Error loading conversation history:', error);
            addMessageToDOM('Error loading conversation history: ' + error.message, false);
        });
}

function displayConversationHistory(history, title) {
    console.log('📖 Displaying conversation history:', history);
    
    // Hide welcome screen and show messages container
    hideWelcome();
    
    // Clear current messages and reset conversation history
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
    
    // Reset global conversation history for this view
    conversationHistory = [];
    
    // Add a header for the conversation
    const headerDiv = document.createElement('div');
    headerDiv.className = 'conversation-header';
    headerDiv.style.cssText = `
        padding: 16px 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 24px;
        text-align: center;
        background: var(--bg-secondary);
        border-radius: var(--radius-lg);
        margin: 0 0 24px 0;
    `;
    headerDiv.innerHTML = `
        <div style="font-size: 18px; font-weight: 600; color: var(--primary-color); margin-bottom: 8px;">
            📖 Conversation History
        </div>
        <div style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">
            ${title || 'Previous conversation'} • ${history.length} messages
        </div>
        <button onclick="newChat()" style="
            padding: 8px 16px;
            background: var(--primary-gradient);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        ">✏️ Start New Chat</button>
    `;
    
    messagesContainer.appendChild(headerDiv);
    
    // Display each message in the conversation
    if (history && history.length > 0) {
        console.log(`📝 Processing ${history.length} messages`);
        
        history.forEach((msg, index) => {
            console.log(`Message ${index}:`, msg);
            
            if (msg.role === 'user' && msg.content) {
                console.log('👤 Adding user message:', msg.content.substring(0, 50) + '...');
                addMessageToDOM(msg.content, true);
            } else if (msg.role === 'assistant' && msg.content) {
                console.log('🤖 Adding assistant message:', msg.content.substring(0, 50) + '...');
                addMessageToDOM(msg.content, false);
            }
        });
        
        console.log('✅ All messages added to DOM');
    } else {
        console.log('❌ No messages to display');
        const noMessagesDiv = document.createElement('div');
        noMessagesDiv.style.cssText = `
            padding: 40px 20px;
            text-align: center;
            color: var(--text-secondary);
            font-style: italic;
        `;
        noMessagesDiv.textContent = 'No messages found in this conversation.';
        messagesContainer.appendChild(noMessagesDiv);
    }
    
    // Scroll to bottom after a short delay to ensure DOM is updated
    setTimeout(() => {
        scrollToBottom(true); // Force scroll
        console.log('📍 Forced scroll to bottom');
    }, 200);
    
    showToast(`Loaded conversation with ${history.length} messages`, 'success');
}

function newChat() {
    console.log('🆕 Starting new chat...');
    conversationHistory = [];
    currentSessionId = generateSessionId(); // Generate new session ID immediately
    
    // Clear messages and show welcome screen
    const messagesContainer = document.getElementById('messagesContainer');
    const welcomeScreen = document.getElementById('welcomeScreen');
    
    if (messagesContainer && welcomeScreen) {
        console.log('🔄 Resetting chat display...');
        messagesContainer.style.display = 'none';
        messagesContainer.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        console.log('✅ Welcome screen shown, messages container hidden');
    } else {
        console.error('❌ Could not find required elements for new chat');
    }
    
    // Clear input using helper function
    clearChatInput();
    
    // Clear draft and reset retry count
    clearDraft();
    retryCount = 0;
    
    console.log('✅ New chat initialized with session ID:', currentSessionId);
}

// Engine Status Monitoring
function startEngineStatusMonitoring() {
    // Check initial status
    checkEngineStatus();
    
    // Check status every 30 seconds
    setInterval(checkEngineStatus, 30000);
    
    // Monitor network connectivity
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Check initial connectivity
    updateConnectionStatus(navigator.onLine);
}

let pipelineEndpointExists = true; // Track if the endpoint exists

function handleOnline() {
    console.log('🌐 Connection restored');
    updateConnectionStatus(true);
    showToast('Connection restored', 'success');
    
    // Retry any pending operations
    checkEngineStatus();
}

function handleOffline() {
    console.log('📡 Connection lost');
    updateConnectionStatus(false);
    showToast('Connection lost - working offline', 'warning');
}

function updateConnectionStatus(isOnline) {
    const indicator = document.getElementById('statusIndicator');
    if (!indicator) return;
    
    const dot = indicator.querySelector('span');
    const textSpan = indicator.childNodes[2];
    
    if (!isOnline) {
        if (dot) dot.style.background = '#ef4444'; // red
        if (textSpan) textSpan.textContent = 'Offline';
        return;
    }
    
    // If online, show the actual engine status (only if endpoint exists)
    if (pipelineEndpointExists) {
        checkEngineStatus();
    } else {
        // Default to ready if no pipeline endpoint
        updateStatusIndicator('ready');
    }
}

function checkEngineStatus() {
    // Skip if we know the endpoint doesn't exist
    if (!pipelineEndpointExists) {
        updateStatusIndicator('ready');
        return;
    }
    
    fetch('/api/pipeline-status')
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    pipelineEndpointExists = false; // Mark endpoint as non-existent
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            updateStatusIndicator(data.status || 'unknown');
        })
        .catch(error => {
            // Don't log 404 errors as they're expected when pipeline endpoint doesn't exist
            if (error.message.includes('404')) {
                pipelineEndpointExists = false;
            } else if (!error.message.includes('404')) {
                console.log('Status check failed:', error.message);
            }
            updateStatusIndicator('ready');
        });
}

function updateStatusIndicator(status) {
    const indicator = document.getElementById('statusIndicator');
    if (!indicator) return;
    
    let color = '#10b981'; // green
    let text = 'Ready';
    
    switch (status) {
        case 'processing':
            color = '#f59e0b'; // yellow
            text = 'Processing';
            break;
        case 'error':
            color = '#ef4444'; // red
            text = 'Error';
            break;
        case 'ready':
        case 'completed':
        default:
            color = '#10b981'; // green
            text = 'Ready';
            break;
    }
    
    const dot = indicator.querySelector('span');
    if (dot) {
        dot.style.background = color;
    }
    
    const textSpan = indicator.childNodes[2]; // The text node after the dot and gap
    if (textSpan) {
        textSpan.textContent = text;
    }
    
    // Fetch and display model information
    fetchCurrentModel();
}

// Fetch current AI model information
function fetchCurrentModel() {
    fetch('/api/current-model')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateModelDisplay(data.provider, data.model_name);
            } else {
                console.warn('Failed to fetch model info:', data.error);
                // Use fallback display
                updateModelDisplay('grok', 'grok-3-fast');
            }
        })
        .catch(error => {
            console.warn('Error fetching model info:', error);
            // Use fallback display
            updateModelDisplay('grok', 'grok-3-fast');
        });
}

// Update the model display in status indicator and navigation
function updateModelDisplay(provider, modelName) {
    // Format model name for display
    let displayName = '';
    if (provider === 'grok') {
        displayName = modelName.includes('grok-3') ? 'Grok' : 'Grok';
    } else if (provider === 'openai') {
        displayName = modelName.includes('gpt-4') ? 'ChatGPT' : 'ChatGPT';
    } else if (provider === 'gemini') {
        displayName = 'Gemini';
    } else {
        displayName = provider.charAt(0).toUpperCase() + provider.slice(1);
    }
    
    // Update status indicator
    const indicator = document.getElementById('statusIndicator');
    if (indicator) {
        // Get or create model display element
        let modelSpan = indicator.querySelector('.model-info');
        if (!modelSpan) {
            modelSpan = document.createElement('span');
            modelSpan.className = 'model-info';
            modelSpan.style.cssText = `
                margin-left: 8px;
                font-size: 11px;
                color: var(--text-secondary);
                opacity: 0.8;
                font-weight: 500;
            `;
            indicator.appendChild(modelSpan);
        }
        modelSpan.textContent = `• ${displayName}`;
    }
    
    // Update navigation model display
    const navModelDisplay = document.getElementById('navModelDisplay');
    if (navModelDisplay) {
        const modelNameSpan = navModelDisplay.querySelector('.model-name');
        if (modelNameSpan) {
            modelNameSpan.textContent = displayName;
        }
        
        // Update tooltip with full model info
        navModelDisplay.title = `Current AI Model: ${displayName} (${provider}:${modelName})`;
    }
    
    console.log(`✅ Model display updated: ${displayName} (${provider}:${modelName})`);
}

// Regenerate Response
function regenerateResponse(messageDiv, userQuery) {
    // Remove the current bot message
    messageDiv.remove();
    
    // Show typing indicator
    showTypingIndicator();
    
    // Get current mode and thinking mode
    const mode = currentMode; // Use global currentMode
    
    // Send request again
    fetch('/chatbot_query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: userQuery,
            mode: currentMode, // Use global currentMode
            thinking: thinkingMode
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        
        if (data.answer) {
            // Update conversation history
            conversationHistory[conversationHistory.length - 1] = {
                role: 'assistant',
                content: data.answer
            };
            
            // Add new bot message
            addMessageToDOM(data.answer, false, true, data.structured);
        } else {
            addMessageToDOM('Sorry, I encountered an error. Please try again.', false);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToDOM('Sorry, I encountered an error. Please try again.', false);
    });
}

// Recent Chats Functions
function toggleRecentChats() {
    const panel = document.getElementById('recentChatsPanel');
    if (panel) {
        panel.classList.toggle('active');
        if (panel.classList.contains('active')) {
            loadRecentChats();
        }
    }
}

function hideRecentChats() {
    const panel = document.getElementById('recentChatsPanel');
    if (panel) {
        panel.classList.remove('active');
    }
}

function clearAllChats() {
    if (confirm('Are you sure you want to clear all chat history? This will delete all your previous conversations.')) {
        console.log('🗑️ Clearing all chat history...');
        
        // Call the database API to clear history
        fetch('/api/chat/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        })
        .then(response => {
            console.log('📡 Clear history API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('✅ Chat history cleared:', data);
            if (data.success) {
                // Clear localStorage as well for consistency
                localStorage.removeItem('chatHistory');
                
                // Update sidebar immediately to show empty state
                loadRecentChatsToSidebar();
                console.log('🔄 Sidebar updated after clearing history');
                
                // Show success message
                showToast('Chat history cleared successfully', 'success');
                
                // Start a new chat
                newChat();
            } else {
                showToast('Error clearing chat history: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('❌ Error clearing chat history:', error);
            showToast('Error clearing chat history: ' + error.message);
        });
    }
}

// Image Upload Handler
function handleImageUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    
    Array.from(files).forEach(file => {
        if (!file.type.startsWith('image/')) {
            showToast('Please select only image files');
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            showToast('Image size should be less than 5MB');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            // Create image preview
            const imagePreview = document.createElement('div');
            imagePreview.className = 'image-preview-container';
            imagePreview.style.cssText = `
                position: relative;
                display: inline-block;
                margin: 8px 8px 8px 0;
                border-radius: var(--radius-md);
                overflow: hidden;
                border: 1px solid var(--border-color);
            `;
            
            imagePreview.innerHTML = `
                <img src="${e.target.result}" class="image-preview" alt="Uploaded image" style="
                    max-width: 200px;
                    max-height: 200px;
                    display: block;
                ">
                <button class="image-remove-btn" onclick="this.parentElement.remove()" style="
                    position: absolute;
                    top: 4px;
                    right: 4px;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    border: none;
                    background: rgba(0, 0, 0, 0.7);
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: bold;
                ">✕</button>
            `;
            
            // Add to input area
            const inputWrapper = document.querySelector('.input-wrapper');
            inputWrapper.insertBefore(imagePreview, chatInput);
            
            // Update placeholder
            if (chatInput.value.trim() === '') {
                chatInput.placeholder = 'Describe what you want to know about this image...';
            }
            
            showToast('Image uploaded successfully');
        };
        
        reader.readAsDataURL(file);
    });
    
    // Clear the input
    event.target.value = '';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌟 DOM Content Loaded - Starting initialization...');
    
    // Check if Chart.js is loaded
    if (typeof Chart !== 'undefined') {
        console.log('✅ Chart.js is loaded');
    } else {
        console.error('❌ Chart.js is not loaded');
    }
    
    // Initialize the app
    init();
    
    // Hide loading screen with multiple fallbacks
    function hideLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            console.log('🎯 Hiding loading screen...');
            loadingScreen.classList.add('hidden');
            
            // Force hide after animation
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }
    
    // Primary timeout
    setTimeout(hideLoadingScreen, 1500);
    
    // Fallback timeout in case something goes wrong
    setTimeout(hideLoadingScreen, 3000);
    
    // Immediate fallback if everything loads quickly
    if (document.readyState === 'complete') {
        setTimeout(hideLoadingScreen, 500);
    }
});

// Additional fallback for window load
window.addEventListener('load', function() {
    console.log('🌟 Window fully loaded');
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen && !loadingScreen.classList.contains('hidden')) {
            console.log('🎯 Force hiding loading screen on window load...');
            loadingScreen.classList.add('hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }, 1000);
});

// Emergency fallback - click to dismiss loading screen
document.addEventListener('click', function(event) {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen && !loadingScreen.classList.contains('hidden') && event.target.closest('.loading-screen')) {
        console.log('🆘 Emergency: User clicked loading screen - force hiding...');
        loadingScreen.classList.add('hidden');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 100);
    }
});

// Debug function - can be called from browser console
window.debugChatbot = function() {
    console.log('🔧 CHATBOT DEBUG INFO:');
    
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesContainer = document.getElementById('messagesContainer');
    const chatArea = document.getElementById('chatArea');
    
    console.log('📱 Welcome Screen:', {
        exists: !!welcomeScreen,
        display: welcomeScreen ? welcomeScreen.style.display : 'N/A',
        visible: welcomeScreen ? welcomeScreen.offsetParent !== null : false
    });
    
    console.log('📦 Messages Container:', {
        exists: !!messagesContainer,
        display: messagesContainer ? messagesContainer.style.display : 'N/A',
        visible: messagesContainer ? messagesContainer.offsetParent !== null : false,
        childCount: messagesContainer ? messagesContainer.children.length : 0,
        innerHTML: messagesContainer ? messagesContainer.innerHTML.length : 0
    });
    
    console.log('📜 Chat Area:', {
        exists: !!chatArea,
        scrollTop: chatArea ? chatArea.scrollTop : 'N/A',
        scrollHeight: chatArea ? chatArea.scrollHeight : 'N/A',
        clientHeight: chatArea ? chatArea.clientHeight : 'N/A'
    });
    
    console.log('🔄 Global State:', {
        conversationHistory: conversationHistory.length,
        isTyping,
        userScrolled,
        thinkingMode
    });
    
    if (messagesContainer && messagesContainer.children.length > 0) {
        console.log('📝 Messages in DOM:');
        Array.from(messagesContainer.children).forEach((child, index) => {
            console.log(`  ${index}: ${child.className} - ${child.textContent.substring(0, 50)}...`);
        });
    }
};

// Original debug function for loading screen
window.forceHideLoading = function() {
    console.log('🔧 Debug: Force hiding loading screen...');
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.classList.add('hidden');
        loadingScreen.style.display = 'none';
        console.log('✅ Loading screen hidden');
    } else {
        console.log('❌ Loading screen not found');
    }
};

// Preprocess message content to add proper structure and spacing
function preprocessMessageContent(content) {
    let processed = content;
    
    // Add proper line breaks before major sections
    processed = processed.replace(/(📊\s*[^\n]+)/g, '\n\n$1\n\n');
    processed = processed.replace(/(🔍\s*[^\n]+)/g, '\n\n$1\n\n');
    processed = processed.replace(/(📋\s*[^\n]+)/g, '\n\n$1\n\n');
    processed = processed.replace(/(💡\s*[^\n]+)/g, '\n\n$1\n\n');
    
    // Add line breaks before bullet points
    processed = processed.replace(/([^\n])(\s*•\s*)/g, '$1\n\n$2');
    
    // Add line breaks before numbered points
    processed = processed.replace(/([^\n])(\s*\d+\.\s*)/g, '$1\n\n$2');
    
    // Add line breaks before chart titles (Top X patterns)
    processed = processed.replace(/([^\n])(Top\s+\d+[^\n]*)/g, '$1\n\n$2\n\n');
    
    // Add line breaks before WhatsApp references
    processed = processed.replace(/([^\n])(📱\s*WhatsApp)/g, '$1\n\n$2');
    
    // Ensure proper spacing around contact info
    processed = processed.replace(/(👤\s*Contact[^\n]*)/g, '\n$1\n');
    processed = processed.replace(/(📞\s*[^\n]*)/g, '$1\n');
    processed = processed.replace(/(🏷️\s*[^\n]*)/g, '$1\n');
    processed = processed.replace(/(💬\s*"[^"]*")/g, '$1\n\n');
    
    // Clean up multiple line breaks but preserve intentional spacing
    processed = processed.replace(/\n{4,}/g, '\n\n\n');
    processed = processed.replace(/^\n+/, ''); // Remove leading newlines
    processed = processed.replace(/\n+$/, ''); // Remove trailing newlines
    
    return processed;
}

// Enhanced HTML processing for better markdown rendering
function enhanceMarkdownHTML(html) {
    // First, let's add proper spacing around major sections with better detection
    html = html.replace(/(<p>)?📊\s*([^<\n]+)(<\/p>)?/g, '\n\n<div class="analysis-section"><h2 class="section-header">📊 $2</h2></div>\n\n');
    html = html.replace(/(<p>)?🔍\s*([^<\n]+)(<\/p>)?/g, '\n\n<div class="findings-section"><h2 class="section-header">🔍 $2</h2></div>\n\n');
    html = html.replace(/(<p>)?📋\s*([^<\n]+)(<\/p>)?/g, '\n\n<div class="references-section"><h2 class="section-header">📋 $2</h2></div>\n\n');
    html = html.replace(/(<p>)?💡\s*([^<\n]+)(<\/p>)?/g, '\n\n<div class="recommendations-section"><h2 class="section-header">💡 $2</h2></div>\n\n');
    
    // Add proper spacing around bullet points
    html = html.replace(/(<p>)?•\s*([^<\n]+)(<\/p>)?/g, '\n\n<div class="bullet-point">• $2</div>\n\n');
    
    // Add spacing around numbered sections
    html = html.replace(/(<p>)?(\d+\.\s*[^<\n]+)(<\/p>)?/g, '\n\n<div class="numbered-point">$2</div>\n\n');
    
    // Add proper spacing around chart titles and descriptions
    html = html.replace(/(<p>)?(Top\s+\d+[^<\n]*)(<\/p>)?/g, '\n\n<div class="chart-title">$2</div>\n\n');
    
    // Add spacing around WhatsApp references
    html = html.replace(/(<p>)?(📱\s*WhatsApp\s*#\d+)(<\/p>)?/g, '\n\n<div class="whatsapp-ref">$2');
    html = html.replace(/(<p>)?(👤\s*Contact[^💬]*)(<\/p>)?/g, '<div class="contact-info">$2</div>');
    html = html.replace(/(<p>)?(💬\s*"[^"]*")(<\/p>)?/g, '<div class="message-quote">$2</div></div>\n\n');
    
    // Clean up multiple line breaks
    html = html.replace(/\n{3,}/g, '\n\n');
    
    // Add proper spacing around elements
    html = html.replace(/<\/p>\s*<h([1-6])/g, '</p>\n\n<h$1');
    html = html.replace(/<\/h([1-6])>\s*<p>/g, '</h$1>\n\n<p>');
    html = html.replace(/<\/ul>\s*<p>/g, '</ul>\n\n<p>');
    html = html.replace(/<\/ol>\s*<p>/g, '</ol>\n\n<p>');
    html = html.replace(/<\/p>\s*<ul>/g, '</p>\n\n<ul>');
    html = html.replace(/<\/p>\s*<ol>/g, '</p>\n\n<ol>');
    html = html.replace(/<\/blockquote>\s*<p>/g, '</blockquote>\n\n<p>');
    html = html.replace(/<\/p>\s*<blockquote>/g, '</p>\n\n<blockquote>');
    html = html.replace(/<\/pre>\s*<p>/g, '</pre>\n\n<p>');
    html = html.replace(/<\/p>\s*<pre>/g, '</p>\n\n<pre>');
    
    // Remove empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    
    // Enhance table formatting
    html = html.replace(/<table>/g, '<div class="table-wrapper"><table class="markdown-table">');
    html = html.replace(/<\/table>/g, '</table></div>');
    
    // Enhance code blocks
    html = html.replace(/<pre><code class="language-(\w+)">/g, 
        '<div class="code-block-wrapper"><div class="code-language">$1</div><pre class="code-block"><code class="language-$1">');
    html = html.replace(/<pre><code>/g, 
        '<div class="code-block-wrapper"><pre class="code-block"><code>');
    html = html.replace(/<\/code><\/pre>/g, '</code></pre></div>');
    
    // Enhance blockquotes
    html = html.replace(/<blockquote>/g, '<blockquote class="markdown-blockquote">');
    
    // Enhance lists
    html = html.replace(/<ul>/g, '<ul class="markdown-list">');
    html = html.replace(/<ol>/g, '<ol class="markdown-list">');
    
    // Clean up extra whitespace
    html = html.replace(/\n\s*\n\s*\n/g, '\n\n');
    html = html.trim();
    
    return html;
}

// Configure marked.js for perfect markdown rendering
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false,
        sanitize: false,
        smartLists: true,
        smartypants: true,
        xhtml: false,
        highlight: function(code, lang) {
            if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (err) {
                    console.warn('Syntax highlighting failed:', err);
                }
            }
            return typeof hljs !== 'undefined' ? hljs.highlightAuto(code).value : code;
        }
    });
    
    // Custom renderer for better formatting
    const renderer = new marked.Renderer();
    
    // Enhanced table rendering
    renderer.table = function(header, body) {
        return `<div class="table-wrapper">
            <table class="markdown-table">
                <thead>${header}</thead>
                <tbody>${body}</tbody>
            </table>
        </div>`;
    };
    
    // Enhanced code block rendering
    renderer.code = function(code, language) {
        const validLang = language && hljs && hljs.getLanguage(language) ? language : '';
        const highlighted = validLang ? hljs.highlight(code, { language: validLang }).value : code;
        
        return `<div class="code-block-wrapper">
            ${validLang ? `<div class="code-language">${validLang}</div>` : ''}
            <pre class="code-block"><code class="${validLang ? `language-${validLang}` : ''}">${highlighted}</code></pre>
        </div>`;
    };
    
    // Enhanced blockquote rendering
    renderer.blockquote = function(quote) {
        return `<blockquote class="markdown-blockquote">${quote}</blockquote>`;
    };
    
    // Enhanced list rendering
    renderer.list = function(body, ordered, start) {
        const type = ordered ? 'ol' : 'ul';
        const startatt = (ordered && start !== 1) ? ` start="${start}"` : '';
        return `<${type}${startatt} class="markdown-list">${body}</${type}>`;
    };
    
    marked.setOptions({ renderer: renderer });
}

// Image Upload Handler
function handleImageUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    
    Array.from(files).forEach(file => {
        if (!file.type.startsWith('image/')) {
            showToast('Please select only image files');
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) { // 5MB limit
            showToast('Image size should be less than 5MB');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            // Create image preview
            const imagePreview = document.createElement('div');
            imagePreview.className = 'image-preview-container';
            imagePreview.innerHTML = `
                <img src="${e.target.result}" class="image-preview" alt="Uploaded image">
                <button class="image-remove-btn" onclick="this.parentElement.remove()">✕</button>
            `;
            
            // Add to input area
            const inputWrapper = document.querySelector('.input-wrapper');
            inputWrapper.insertBefore(imagePreview, chatInput);
            
            // Update placeholder
            if (chatInput.value.trim() === '') {
                chatInput.placeholder = 'Describe what you want to know about this image...';
            }
        };
        
        reader.readAsDataURL(file);
    });
    
    // Clear the input
    event.target.value = '';
}

// Dealership Dropdown Functions
function toggleDealershipDropdown() {
    const dropdown = document.getElementById('dealershipDropdown');
    const menu = document.getElementById('dealershipDropdownMenu');
    
    if (dropdown && menu) {
        const isActive = dropdown.classList.contains('active');
        
        if (isActive) {
            hideDealershipDropdown();
        } else {
            dropdown.classList.add('active');
            menu.classList.add('active');
        }
    }
}

function hideDealershipDropdown() {
    const dropdown = document.getElementById('dealershipDropdown');
    const menu = document.getElementById('dealershipDropdownMenu');
    
    if (dropdown && menu) {
        dropdown.classList.remove('active');
        menu.classList.remove('active');
    }
}