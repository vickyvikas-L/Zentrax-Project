# 🤖 Zentrax — AI-Powered Voice & Gesture Desktop Controller

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows" alt="Windows">
  <img src="https://img.shields.io/badge/AI-Zentrax-red?style=for-the-badge" alt="Zentrax">
  <img src="https://img.shields.io/badge/Inspired_By-FRIDAY-gold?style=for-the-badge" alt="FRIDAY">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker" alt="Docker">
</p>

<p align="center">
  <strong>"Good morning. What would you like me to do today?"</strong>
</p>

**Zentrax** is your personal AI assistant inspired by Iron Man's FRIDAY. It controls your entire Windows PC using natural voice commands and hand gestures. Just say "Hey Zentrax" and speak naturally - Zentrax will understand and execute your commands, responding with a friendly voice!

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **FRIDAY-like AI** | Talks back to you! Voice responses with personality |
| 🎤 **Voice Control** | Speak naturally - "Open Chrome", "What's my battery?", "Play next song" |
| 🖐️ **Gesture Control** | Control your PC with hand gestures via webcam |
| 🧠 **Smart AI** | SmolLM2 LLM understands natural language variations |
| 📊 **Real-time Monitoring** | Live CPU, RAM, battery, disk stats in the UI |
| 🌐 **Modern Web UI** | Beautiful dashboard with system status & command history |
| 🐳 **Docker Support** | One-command Ollama setup with GPU auto-detection |
| 🔊 **Voice Responses** | Zentrax speaks back with time-appropriate greetings |
| 📝 **Centralized Logging** | Color-coded logs with icons for easy debugging |
| ⚙️ **JSON Configuration** | Easily customize all settings via config file |

---

## 🎬 Demo Commands

```
"Hey Zentrax"                         → Zentrax wakes up with a greeting
"Open Chrome"                         → Opens Google Chrome
"What's my battery percentage?"       → "Battery is at 85 percent, charging"
"Search for Python tutorials"         → Opens browser with Google search
"Play next song"                      → Skips to next media track
"Turn up the brightness"              → Increases screen brightness
"Show me running processes"           → Lists top 10 processes
"Take a screenshot"                   → Captures screen
"What time is it?"                    → "The time is 3:45 PM"
"Thank you Zentrax"                   → "You're welcome!"
"Goodbye"                             → "See you later!" (goes to sleep)
```

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Docker Setup](#-docker-setup)
- [Usage Guide](#-usage-guide)
- [Voice Commands](#-voice-commands)
- [Gesture Controls](#-gesture-controls)
- [Configuration](#️-configuration)
- [Web UI](#-web-ui)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🚀 Quick Start

### One Command to Run Everything

```powershell
# Clone and setup
git clone https://github.com/harish00506/Zentrax.git
cd Zentrax
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run Zentrax!
python run.py
```

Or simply double-click **`Zentrax.bat`**!

### What Happens

1. ✅ Backend starts (voice & gesture recognition)
2. ✅ WebSocket server starts (real-time UI updates)
3. ✅ Frontend HTTP server starts
4. ✅ Browser opens to the dashboard
5. ✅ Zentrax greets you!

---

## 💻 Requirements

### Minimum Requirements
| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 |
| **Python** | 3.10 or higher |
| **RAM** | 4GB minimum (8GB recommended) |
| **Microphone** | Any USB or built-in |
| **Speakers** | For voice responses |

### Optional (Recommended)
| Optional | Purpose |
|----------|---------|
| **Webcam** | Gesture control |
| **Ollama** | Smarter AI responses |
| **NVIDIA GPU** | Faster Whisper transcription |
| **Docker** | Easy Ollama deployment |

---

## 📥 Installation

### Step 1: Clone & Setup Environment

```powershell
git clone https://github.com/harish00506/Zentrax.git
cd Zentrax
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `pyttsx3` - Text-to-speech (Zentrax's voice)
- `mediapipe` - Gesture recognition
- `pyautogui` - Desktop automation
- `openai-whisper` - Speech recognition
- `SpeechRecognition` - Audio capture
- `psutil` - System monitoring
- `websockets` - Real-time UI updates
- `colorama` - Colored terminal output
- `pywin32` - Windows integration

### Step 3: Install PyAudio (Windows)

PyAudio is required for microphone access:

```powershell
# Method A - Using pipwin (Recommended)
pip install pipwin
pipwin install pyaudio

# Method B - Direct wheel
pip install PyAudio
```

### Step 4: Install Ollama (Optional but Recommended)

For smarter AI responses, install Ollama:

**Option A - Native Installation:**
```powershell
.\scripts\setup_ollama.ps1
```

**Option B - Docker (Recommended):**
```powershell
.\docker\start.ps1
```

---

## 🐳 Docker Setup

### One Command Docker Launch

```powershell
# Windows Batch
docker\start.bat

# PowerShell (with options)
.\docker\start.ps1
```

### Features
- ✅ Auto-detects NVIDIA GPU
- ✅ Falls back to CPU if no GPU
- ✅ Downloads SmolLM2 model automatically
- ✅ Persists data in Docker volume

### Docker Commands

```powershell
.\docker\start.ps1              # Start with auto GPU detection
.\docker\start.ps1 -CPU         # Force CPU mode
.\docker\start.ps1 -Stop        # Stop containers
.\docker\start.ps1 -Logs        # View container logs
.\docker\start.ps1 -Shell       # Open container shell
```

### Manual Docker Setup

```powershell
# GPU version (NVIDIA)
docker-compose -f docker/docker-compose.yml up -d

# CPU version
docker-compose -f docker/docker-compose.cpu.yml up -d
```

---

## 📖 Usage Guide

### Command-Line Options

```powershell
python run.py                    # Start with UI and browser
python run.py --headless         # Run without camera window
python run.py --no-browser       # Don't auto-open browser
python run.py --port 3000        # Use custom frontend port

# PowerShell launcher
.\Zentrax.ps1 -Headless -Port 3000
```

### Components Started

| Component | Description | URL |
|-----------|-------------|-----|
| 🤖 **Backend** | Voice & gesture recognition | Terminal output |
| 🌐 **Frontend** | Modern dashboard UI | http://localhost:8080 |
| 🔌 **WebSocket** | Real-time communication | ws://localhost:8765 |
| 🧠 **Ollama** | AI language model | http://localhost:11434 |

### Wake Phrase

Say **"Zentrax"** or any of these:
- "Hey Zentrax"
- "Hi Zentrax"
- "OK Zentrax"
- "Hello"

---

## 🎤 Voice Commands

### Application Control

| Say This | What Happens |
|----------|--------------|
| "Open Chrome" | Opens Google Chrome |
| "Open Notepad" | Opens Notepad |
| "Open VS Code" | Opens Visual Studio Code |
| "Close window" | Closes current window |
| "Minimize" / "Maximize" | Window controls |
| "Switch window" | Alt+Tab |
| "Show desktop" | Minimize all |

### System Information

| Say This | Zentrax Responds |
|----------|------------------|
| "What is battery percentage?" | "Battery is at 85 percent, charging" |
| "What time is it?" | "The time is 3:45 PM" |
| "CPU usage" | "CPU usage is at 23 percent" |
| "Memory status" | "Memory usage is at 67 percent" |
| "Disk space" | "Disk space is at 45 percent used" |
| "WiFi status" | "Connected to MyWiFi" |

### Media Control

| Say This | What Happens |
|----------|--------------|
| "Play" / "Pause" | Toggle play/pause |
| "Next song" / "Skip" | Next track |
| "Previous song" | Previous track |
| "Volume up/down" | Adjust volume |
| "Mute" | Toggle mute |

### File & Web

| Say This | What Happens |
|----------|--------------|
| "Open my documents" | Opens Documents folder |
| "Search for PDFs" | Finds PDF files |
| "Google machine learning" | Web search |
| "Take a screenshot" | Captures screen |

### System Control

| Say This | What Happens |
|----------|--------------|
| "Turn up brightness" | Increase brightness |
| "Lock screen" | Lock computer |
| "Shutdown" / "Restart" | Power control |

---

## 🖐️ Gesture Controls

| Gesture | Action |
|---------|--------|
| ✋ **Open Palm** | Scroll Up |
| ✊ **Closed Fist** | Scroll Down |
| 👍 **Thumbs Up** | Volume Up |
| 👎 **Thumbs Down** | Volume Down |
| 👈 **Swipe Left** | Previous Tab |
| 👉 **Swipe Right** | Next Tab |
| 🤏 **Pinch** | Zoom In/Out |
| ☝️ **Pointing** | Move Cursor |

Press **Q** in the camera window to exit.

---

## ⚙️ Configuration

### JSON Configuration File

Zentrax uses a JSON config file at `config/zentrax_config.json`:

```json
{
  "voice": {
    "wake_phrase": "zentrax",
    "speech_engine": "google",
    "whisper_model": "base"
  },
  "tts": {
    "enabled": true,
    "speed": 175,
    "voice_type": "female"
  },
  "gesture": {
    "enabled": true,
    "sensitivity": 0.7
  },
  "server": {
    "websocket_port": 8765,
    "http_port": 8080
  },
  "llm": {
    "provider": "ollama",
    "model": "smollm2",
    "ollama_url": "http://localhost:11434"
  }
}
```

### Customization Options

**Change Wake Phrase:**
```json
"voice": { "wake_phrase": "jarvis" }
```

**Disable Voice Responses:**
```json
"tts": { "enabled": false }
```

**Change Voice Speed:**
```json
"tts": { "speed": 200 }  // 100-250
```

**Use Different AI Model:**
```json
"llm": { "model": "llama3.2" }
```

---

## 🌐 Web UI

The modern dashboard shows:

| Panel | Information |
|-------|-------------|
| 📊 **System Status** | Live CPU, RAM, battery, disk usage |
| 📜 **Command History** | Recent voice commands with timestamps |
| 🎙️ **Voice Visualizer** | Real-time audio waveform |
| ✋ **Gesture Status** | Current detected gesture |
| 🔌 **Connection Status** | WebSocket connection state |

### Accessing the UI

- **Auto-opens** when running `python run.py`
- **Manual**: http://localhost:8080
- **Custom port**: `python run.py --port 3000`

---

## 📁 Project Structure

```
Zentrax/
├── run.py                        # 🚀 Unified launcher (start here!)
├── main.py                       # Core voice/gesture controller
├── Zentrax.bat                   # Windows batch launcher
├── Zentrax.ps1                   # PowerShell launcher
├── requirements.txt              # Python dependencies
│
├── src/                          # Source code
│   ├── assistant/                # AI Assistant
│   │   ├── friday_assistant.py   # FRIDAY personality & voice
│   │   └── whisper_handler.py    # Whisper speech recognition
│   │
│   ├── commands/                 # Command processing
│   │   ├── command_executor.py   # Execute Windows commands
│   │   ├── windows_command_generator.py  # AI command generation
│   │   └── windows_automation.py # CLI testing tool
│   │
│   └── core/                     # Core utilities
│       ├── config.py             # ⚙️ JSON configuration manager
│       ├── logger.py             # 📝 Colored logging system
│       ├── websocket_server.py   # 🔌 Real-time WebSocket
│       ├── data_collection.py    # Training data collection
│       └── train_models.py       # Model training
│
├── frontend/                     # Web UI
│   ├── index.html                # Dashboard layout
│   ├── style.css                 # Modern styling
│   └── script.js                 # WebSocket & UI logic
│
├── docker/                       # 🐳 Docker configuration
│   ├── start.bat                 # One-command launcher (Windows)
│   ├── start.ps1                 # PowerShell launcher with options
│   ├── docker-compose.yml        # GPU version
│   ├── docker-compose.cpu.yml    # CPU version
│   └── Dockerfile.ollama         # Ollama image
│
├── scripts/                      # Utility scripts
│   ├── build.bat                 # Build Windows EXE
│   ├── build_app.py              # PyInstaller build
│   ├── setup_ollama.ps1          # Ollama setup
│   ├── setup_ollama_docker.bat   # Docker Ollama setup
│   └── start_ui.bat              # Start frontend only
│
├── config/                       # Configuration
│   ├── zentrax_config.json       # App settings (auto-created)
│   ├── zentrax.spec              # PyInstaller spec
│   └── installer.iss             # Inno Setup installer
│
├── docs/                         # Documentation
│   ├── OLLAMA_DOCKER.md          # Docker setup guide
│   ├── WHISPER_SETUP.md          # Whisper installation
│   ├── WINDOWS_AUTOMATION.md     # Automation details
│   └── FRONTEND_SUMMARY.md       # UI documentation
│
└── training_data/                # Training data
    ├── gestures/                 # Gesture samples
    └── voice_commands/           # Voice command samples
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"No microphone found"** | Check Windows audio settings, reinstall PyAudio |
| **"Ollama connection failed"** | Run `.\docker\start.ps1` or install Ollama natively |
| **"ModuleNotFoundError"** | Run `pip install -r requirements.txt` |
| **Voice not recognized** | Speak clearly after wake phrase, check mic volume |
| **Camera not working** | Close other apps using camera, check permissions |

### Check Logs

Zentrax uses colored logging:
- 🟢 **Green**: Success / Info
- 🔵 **Blue**: Voice commands
- 🟣 **Purple**: Gestures
- 🟡 **Yellow**: Warnings
- 🔴 **Red**: Errors

### Reset Configuration

Delete `config/zentrax_config.json` to reset to defaults.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Ideas for Contributions
- 🐧 Add Linux/macOS support
- 🎨 Create UI themes
- 🗣️ Add more voice commands
- ✋ Improve gesture recognition
- 🌍 Add multilingual support

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [SmolLM2](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B) - Lightweight language model
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [MediaPipe](https://mediapipe.dev) - Hand gesture detection
- [PyAutoGUI](https://pyautogui.readthedocs.io) - Desktop automation

---

<p align="center">
  <strong>🤖 "I am Zentrax. How may I assist you today?"</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/harish00506">harish00506</a>
</p>
