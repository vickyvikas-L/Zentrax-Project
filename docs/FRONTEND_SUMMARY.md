# 🌐 Zentrax Web UI Documentation

The Zentrax Web UI is a modern, real-time dashboard for monitoring and controlling your AI assistant.

---

## ✨ Features

### 📊 System Monitoring
- **CPU Usage** - Real-time processor utilization
- **RAM Usage** - Memory consumption with visual bars
- **Battery Status** - Charge level and charging state
- **Disk Space** - Storage utilization

### 📜 Command History
- Recent voice commands with timestamps
- Color-coded by command type
- Scrollable history panel

### 🎙️ Voice Visualizer
- Real-time audio waveform display
- Visual feedback when speaking
- Connection status indicator

### ✋ Gesture Panel
- Current detected gesture
- Gesture recognition status
- Mode switching controls

---

## 🚀 Quick Start

### Automatic (Recommended)
```powershell
# The unified launcher starts everything
python run.py
```

This automatically:
1. Starts the backend
2. Starts the WebSocket server
3. Starts the frontend HTTP server
4. Opens the browser to http://localhost:8080

### Manual Start
```powershell
# Terminal 1: Start WebSocket server
python -c "from src.core.websocket_server import start_server; import asyncio; asyncio.run(start_server())"

# Terminal 2: Start frontend
cd frontend
python -m http.server 8080

# Open browser
start http://localhost:8080
```

---

## 📁 File Structure

```
frontend/
├── index.html      # Main dashboard layout
├── style.css       # Modern styling with animations
├── script.js       # WebSocket logic & UI updates
├── guide.html      # Visual user guide
└── README.md       # Frontend-specific documentation
```

---

## 🔌 WebSocket Communication

### Connection
The UI connects to `ws://localhost:8765` automatically.

### Message Types

**Received from Backend:**
```javascript
// System info update
{
  "type": "system_info",
  "cpu": 23.5,
  "ram": 67.2,
  "battery": 85,
  "disk": 45.3
}

// Voice command detected
{
  "type": "voice_command",
  "command": "open chrome",
  "timestamp": "2025-12-14T10:30:00"
}

// Gesture detected
{
  "type": "gesture",
  "gesture": "thumbs_up"
}

// Status update
{
  "type": "status",
  "mode": "voice",
  "listening": true
}
```

**Sent to Backend:**
```javascript
// Wake/sleep command
{ "action": "wake" }
{ "action": "sleep" }

// Mode switch
{ "action": "switch_mode", "mode": "voice" }
{ "action": "switch_mode", "mode": "gesture" }

// Manual command
{ "action": "command", "command": "open chrome" }
```

---

## 🎨 UI Components

### Status Panel
- Connection status (green = connected)
- Current mode display
- Wake/sleep state

### System Stats
- Circular progress indicators
- Color-coded thresholds:
  - 🟢 Green: < 60%
  - 🟡 Yellow: 60-80%
  - 🔴 Red: > 80%

### Command Log
- Timestamp for each entry
- Command text with icon
- Result/response display

---

## ⚙️ Configuration

### Change WebSocket Port
Edit `frontend/script.js`:
```javascript
const WS_URL = 'ws://localhost:8765';  // Change port here
```

Also update `config/zentrax_config.json`:
```json
{
  "server": {
    "websocket_port": 8765
  }
}
```

### Change HTTP Port
```powershell
python run.py --port 3000
```

---

## 🛠️ Troubleshooting

### UI Shows "Disconnected"
1. Ensure WebSocket server is running
2. Check port 8765 is not blocked
3. Verify backend is started

### System Stats Not Updating
1. Check `psutil` is installed: `pip install psutil`
2. Verify WebSocket messages in browser console (F12)

### Blank Page
1. Check browser console for errors (F12)
2. Ensure all frontend files exist
3. Try hard refresh (Ctrl+Shift+R)

---

## 📱 Responsive Design

The UI adapts to different screen sizes:

| Screen | Layout |
|--------|--------|
| Desktop (>1200px) | Three-column layout |
| Tablet (768-1200px) | Two-column layout |
| Mobile (<768px) | Single-column stacked |

---

## 🔧 Customization

### Change Colors
Edit `frontend/style.css`:
```css
:root {
  --primary-color: #00d4ff;    /* Cyan accent */
  --secondary-color: #7c3aed;  /* Purple accent */
  --background: #0a0a0f;       /* Dark background */
  --panel-bg: rgba(20, 20, 30, 0.9);
}
```

### Add Custom Panel
1. Add HTML in `index.html`
2. Style in `style.css`
3. Add WebSocket handler in `script.js`

---

## 🚀 Next Steps

After the UI is running:
1. Say "Hey Zentrax" to wake the assistant
2. Watch commands appear in the history panel
3. Monitor system stats in real-time
4. Use gesture mode with your webcam
