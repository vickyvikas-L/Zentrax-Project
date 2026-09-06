# 🌐 Zentrax Web UI

A modern, real-time dashboard for the Zentrax AI assistant.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **System Monitoring** | Live CPU, RAM, battery, disk stats |
| 📜 **Command History** | Recent voice commands with timestamps |
| 🎙️ **Voice Visualizer** | Real-time audio waveform |
| ✋ **Gesture Status** | Current detected gesture |
| 🔌 **Auto-Reconnect** | Reconnects if connection drops |

---

## 🚀 Quick Start

### Automatic (Recommended)
```powershell
# From project root
python run.py
```

This starts everything and opens the browser automatically!

### Manual Start
```powershell
# Start frontend server
cd frontend
python -m http.server 8080

# Open browser
start http://localhost:8080
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `index.html` | Main dashboard layout |
| `style.css` | Modern styling & animations |
| `script.js` | WebSocket & UI logic |
| `guide.html` | Visual user guide |

---

## 🎨 UI Panels

### System Status
- CPU usage percentage
- RAM utilization
- Battery level & charging
- Disk space usage

### Command History
- Timestamped entries
- Color-coded by type
- Scrollable log

### Voice Visualizer
- Audio waveform bars
- Active when listening
- Green = connected

---

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

### Received Messages
```javascript
// System stats
{ "type": "system_info", "cpu": 23, "ram": 67, "battery": 85, "disk": 45 }

// Voice command
{ "type": "voice_command", "command": "open chrome" }

// Gesture detected
{ "type": "gesture", "gesture": "thumbs_up" }
```

### Send Commands
```javascript
// Wake Zentrax
ws.send(JSON.stringify({ action: "wake" }));

// Switch mode
ws.send(JSON.stringify({ action: "switch_mode", mode: "gesture" }));
```

---

## ⚙️ Configuration

### Change Ports

**WebSocket Port** (`script.js`):
```javascript
const WS_URL = 'ws://localhost:8765';
```

**HTTP Port**:
```powershell
python run.py --port 3000
```

---

## 🎨 Customization

### Colors (`style.css`)
```css
:root {
  --primary-color: #00d4ff;    /* Accent color */
  --background: #0a0a0f;       /* Dark background */
  --panel-bg: rgba(20, 20, 30, 0.9);
}
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Disconnected" | Start backend with `python run.py` |
| Stats not updating | Install `psutil`: `pip install psutil` |
| Blank page | Check browser console (F12) |

---

## 📱 Responsive

- **Desktop**: Three-column layout
- **Tablet**: Two-column layout  
- **Mobile**: Single-column stacked

---

<p align="center">
  Part of the <strong>Zentrax</strong> AI Assistant
</p>
