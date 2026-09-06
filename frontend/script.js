// ========================================
// ZENTRAX - Frontend Controller
// ========================================

// WebSocket Connection
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

// State
let isAwake = false;
let currentMode = 'voice';
let commandHistory = [];

// DOM Elements
const elements = {
    // Connection
    connectionStatus: document.getElementById('connectionStatus'),
    timeDisplay: document.getElementById('timeDisplay'),

    // System Status
    batteryValue: document.getElementById('batteryValue'),
    batteryBar: document.getElementById('batteryBar'),
    cpuValue: document.getElementById('cpuValue'),
    cpuBar: document.getElementById('cpuBar'),
    ramValue: document.getElementById('ramValue'),
    ramBar: document.getElementById('ramBar'),
    diskValue: document.getElementById('diskValue'),
    diskBar: document.getElementById('diskBar'),

    // Assistant
    assistantState: document.getElementById('assistantState'),
    visualizer: document.querySelector('.visualizer'),
    visualizerContainer: document.getElementById('visualizerContainer'),
    listeningText: document.getElementById('listeningText'),
    responseDisplay: document.getElementById('responseDisplay'),
    responseText: document.getElementById('responseText'),
    wakeBtn: document.getElementById('wakeBtn'),

    // Mode Buttons
    voiceModeBtn: document.getElementById('voiceModeBtn'),
    gestureModeBtn: document.getElementById('gestureModeBtn'),
    gameModeBtn: document.getElementById('gameModeBtn'),

    // History
    historyList: document.getElementById('historyList'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn')
};

// ========================================
// WebSocket Connection
// ========================================
function initWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
            updateConnectionStatus(true);
            addToHistory('system', 'Connected to Zentrax backend');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleBackendMessage(data);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus(false);
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
            updateConnectionStatus(false);

            // Attempt reconnection
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                const delay = Math.min(3000 * reconnectAttempts, 15000);
                console.log(`Reconnecting in ${delay / 1000}s... (attempt ${reconnectAttempts})`);
                setTimeout(initWebSocket, delay);
            }
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus(false);
        setTimeout(initWebSocket, 5000);
    }
}

function sendCommand(command, params = {}) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command, params }));
        console.log('Sent:', command, params);
    } else {
        console.warn('WebSocket not connected');
        showResponse('Not connected to backend');
    }
}

// ========================================
// Backend Message Handler
// ========================================
function handleBackendMessage(data) {
    console.log('Received:', data);

    switch (data.type) {
        case 'status':
            updateAssistantStatus(data.status, data.mode);
            break;

        case 'system_info':
            updateSystemInfo(data);
            break;

        case 'log':
            addToHistory(data.category || 'system', data.message);
            break;

        case 'command':
            addToHistory('voice', data.command);
            showResponse(data.response || `Executed: ${data.command}`);
            break;

        case 'gesture':
            addToHistory('gesture', data.gesture);
            break;

        case 'response':
            showResponse(data.message);
            break;

        case 'error':
            showResponse(data.message, true);
            break;
    }
}

// ========================================
// UI Update Functions
// ========================================
function updateConnectionStatus(connected) {
    const dot = elements.connectionStatus.querySelector('.connection-dot');
    const text = elements.connectionStatus.querySelector('span:last-child');

    dot.className = 'connection-dot ' + (connected ? 'connected' : 'disconnected');
    text.textContent = connected ? 'Connected' : 'Disconnected';
}

function updateAssistantStatus(status, mode = null) {
    isAwake = status === 'awake';

    elements.assistantState.textContent = isAwake ? 'Awake' : 'Sleeping';
    elements.assistantState.className = 'assistant-state ' + (isAwake ? 'awake' : '');

    elements.wakeBtn.classList.toggle('active', isAwake);
    elements.wakeBtn.querySelector('.wake-text').textContent = isAwake ? 'Listening...' : 'Tap to Speak';

    elements.listeningText.textContent = isAwake
        ? 'Listening for your commands...'
        : 'Say "Hey Zentrax" to wake me up';

    elements.visualizer.classList.toggle('listening', isAwake);

    if (mode) {
        currentMode = mode;
        updateModeButtons();
    }
}

function updateModeButtons() {
    const buttons = [elements.voiceModeBtn, elements.gestureModeBtn, elements.gameModeBtn];
    buttons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === currentMode);
    });
}

function updateSystemInfo(data) {
    if (data.battery !== undefined) {
        elements.batteryValue.textContent = `${data.battery}%`;
        elements.batteryBar.style.width = `${data.battery}%`;

        // Change color based on level
        if (data.battery <= 20) {
            elements.batteryBar.style.background = 'var(--accent-danger)';
        } else if (data.battery <= 40) {
            elements.batteryBar.style.background = 'var(--accent-warning)';
        } else {
            elements.batteryBar.style.background = 'var(--accent-success)';
        }
    }

    if (data.cpu !== undefined) {
        elements.cpuValue.textContent = `${data.cpu}%`;
        elements.cpuBar.style.width = `${data.cpu}%`;
    }

    if (data.ram !== undefined) {
        elements.ramValue.textContent = `${data.ram}%`;
        elements.ramBar.style.width = `${data.ram}%`;
    }

    if (data.disk !== undefined) {
        elements.diskValue.textContent = `${data.disk}%`;
        elements.diskBar.style.width = `${data.disk}%`;
    }
}

function showResponse(message, isError = false) {
    elements.responseText.textContent = message;
    elements.responseDisplay.style.borderColor = isError
        ? 'var(--accent-danger)'
        : 'var(--border-color)';
}

// ========================================
// Command History
// ========================================
function addToHistory(type, message) {
    // Remove empty state if exists
    const emptyState = elements.historyList.querySelector('.history-empty');
    if (emptyState) {
        emptyState.remove();
    }

    // Create history item
    const item = document.createElement('div');
    item.className = 'history-item';

    const typeIcons = {
        voice: '🎤',
        gesture: '✋',
        system: '⚙️'
    };

    const time = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });

    item.innerHTML = `
        <div class="history-type ${type}">${typeIcons[type] || '📋'}</div>
        <div class="history-content">
            <div class="history-command">${escapeHtml(message)}</div>
            <div class="history-time">${time}</div>
        </div>
    `;

    // Add to top of list
    elements.historyList.insertBefore(item, elements.historyList.firstChild);

    // Keep history limited
    while (elements.historyList.children.length > 50) {
        elements.historyList.removeChild(elements.historyList.lastChild);
    }

    // Store in array
    commandHistory.unshift({ type, message, time: Date.now() });
    if (commandHistory.length > 50) commandHistory.pop();
}

function clearHistory() {
    elements.historyList.innerHTML = `
        <div class="history-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
            </svg>
            <p>No commands yet</p>
            <span>Your command history will appear here</span>
        </div>
    `;
    commandHistory = [];
}

// ========================================
// Quick Actions
// ========================================
function handleQuickAction(action) {
    const actions = {
        screenshot: () => sendCommand('execute', { command: 'take screenshot' }),
        volume_up: () => sendCommand('execute', { command: 'volume up' }),
        volume_down: () => sendCommand('execute', { command: 'volume down' }),
        mute: () => sendCommand('execute', { command: 'mute' }),
        brightness_up: () => sendCommand('execute', { command: 'brightness up' }),
        lock: () => sendCommand('execute', { command: 'lock screen' })
    };

    if (actions[action]) {
        actions[action]();
        addToHistory('system', `Quick action: ${action.replace('_', ' ')}`);
    }
}

// ========================================
// Command Categories Toggle
// ========================================
function initCategoryToggles() {
    document.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', () => {
            header.classList.toggle('active');
            const commands = header.nextElementSibling;
            commands.classList.toggle('active');
        });
    });
}

// ========================================
// Utility Functions
// ========================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateClock() {
    const now = new Date();
    elements.timeDisplay.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// Simulate system info (replace with actual data from backend)
function simulateSystemInfo() {
    updateSystemInfo({
        battery: Math.floor(Math.random() * 30) + 70,
        cpu: Math.floor(Math.random() * 40) + 10,
        ram: Math.floor(Math.random() * 30) + 40,
        disk: Math.floor(Math.random() * 20) + 50
    });
}

// ========================================
// Event Listeners
// ========================================
function initEventListeners() {
    // Wake Button
    elements.wakeBtn.addEventListener('click', () => {
        if (isAwake) {
            sendCommand('sleep');
        } else {
            sendCommand('wake');
        }
    });

    // Mode Buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            sendCommand('switch_mode', { mode });
            currentMode = mode;
            updateModeButtons();
            addToHistory('system', `Switched to ${mode} mode`);
        });
    });

    // Quick Actions
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            handleQuickAction(btn.dataset.action);
        });
    });

    // Clear History
    elements.clearHistoryBtn.addEventListener('click', clearHistory);

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+W - Wake/Sleep
        if (e.ctrlKey && e.key === 'w') {
            e.preventDefault();
            elements.wakeBtn.click();
        }

        // Ctrl+1 - Voice Mode
        if (e.ctrlKey && e.key === '1') {
            e.preventDefault();
            elements.voiceModeBtn.click();
        }

        // Ctrl+2 - Gesture Mode
        if (e.ctrlKey && e.key === '2') {
            e.preventDefault();
            elements.gestureModeBtn.click();
        }

        // Ctrl+3 - Game Mode
        if (e.ctrlKey && e.key === '3') {
            e.preventDefault();
            elements.gameModeBtn.click();
        }
    });

    // Page Visibility
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && (!ws || ws.readyState !== WebSocket.OPEN)) {
            initWebSocket();
        }
    });
}

// ========================================
// Initialization
// ========================================
window.addEventListener('load', () => {
    console.log('Zentrax UI initializing...');

    // Initialize components
    initEventListeners();
    initCategoryToggles();
    initWebSocket();

    // Start clock
    updateClock();
    setInterval(updateClock, 1000);

    // System info will come from backend via WebSocket
    // Fallback to simulation if not connected after 3 seconds
    setTimeout(() => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.log('Backend not connected, using simulated system info');
            simulateSystemInfo();
            setInterval(simulateSystemInfo, 5000);
        }
    }, 3000);

    // Show startup message
    addToHistory('system', 'Zentrax UI initialized');
    addToHistory('system', 'Keyboard: Ctrl+W (wake), Ctrl+1/2/3 (modes)');
});
