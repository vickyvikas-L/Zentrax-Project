# Windows Automation with SmolLM2

This module provides natural language Windows automation using **SmolLM2** via **Ollama**.

## Overview

The Windows Automation system converts natural language commands into executable Windows operations:

```
User: "open chrome"  →  {"action": "open_app", "target": "chrome.exe"}  →  Chrome opens
```

## Quick Start

### 1. Install Ollama

Download and install from: https://ollama.ai/download

Or via winget:
```powershell
winget install Ollama.Ollama
```

### 2. Pull SmolLM2 Model

```bash
ollama serve  # Start the server (in a separate terminal)
ollama pull smollm2
```

### 3. Install Dependencies

```bash
pip install requests pyautogui
```

### 4. Run the Automation

```bash
python windows_automation.py
```

## Usage

### Interactive Mode

```bash
python windows_automation.py
```

This starts an interactive session where you can type natural language commands:

```
🎤 You: open chrome
✅ Opened chrome.exe

🎤 You: take a screenshot
✅ Screenshot saved to C:/Users/.../screenshot_20251211_143022.png

🎤 You: search for pdf files
✅ Searching for '*.pdf' in C:/Users/...
```

### Programmatic Usage

```python
from windows_automation import WindowsAutomation

# Initialize
auto = WindowsAutomation()

# Check if system is ready
if auto.check_status():
    # Run commands
    auto.run("open chrome")
    auto.run("take a screenshot")
    auto.run("create a folder called Projects on desktop")
```

### Generate Without Executing

```python
from windows_command_generator import WindowsCommandGenerator

generator = WindowsCommandGenerator()
command = generator.generate_command("open the downloads folder")
print(command)
# Output: {"action": "open_folder", "path": "C:/Users/Username/Downloads"}
```

### Execute Predefined Commands

```python
from command_executor import CommandExecutor

executor = CommandExecutor()
success, message = executor.execute({
    "action": "open_app",
    "target": "notepad.exe"
})
```

## Supported Actions

| Action | Description | Example Command |
|--------|-------------|-----------------|
| `open_app` | Open an application | "open chrome", "launch notepad" |
| `open_file` | Open a file | "open report.docx" |
| `open_folder` | Open a folder | "open downloads folder" |
| `search` | Search for files | "find pdf files", "search for *.txt" |
| `create_file` | Create a new file | "create a file called notes.txt" |
| `create_folder` | Create a new folder | "create Projects folder on desktop" |
| `delete` | Delete file/folder | "delete temp folder" |
| `move` | Move file/folder | "move report.docx to Documents" |
| `rename` | Rename file/folder | "rename file to new_name.txt" |
| `copy` | Copy file/folder | "copy file to backup folder" |
| `maximize_window` | Maximize window | "maximize this window" |
| `minimize_window` | Minimize window | "minimize window" |
| `close_window` | Close window | "close this window" |
| `switch_window` | Switch windows | "switch to chrome" |
| `run_command` | Run shell command | "run ipconfig" |
| `open_control_panel` | Open Control Panel | "open control panel" |
| `open_settings` | Open Windows Settings | "open wifi settings" |
| `task_manager` | Open Task Manager | "open task manager" |
| `keyboard_action` | Keyboard shortcuts | "press ctrl+c" |
| `mouse_action` | Mouse actions | "click at 100,200" |
| `volume_up` | Increase volume | "turn up the volume" |
| `volume_down` | Decrease volume | "lower the volume" |
| `mute` | Toggle mute | "mute audio" |
| `screenshot` | Take screenshot | "take a screenshot" |
| `lock_screen` | Lock computer | "lock the screen" |
| `shutdown` | Shutdown PC | "shutdown computer" |
| `restart` | Restart PC | "restart computer" |
| `sleep` | Sleep mode | "put computer to sleep" |

## Command Structure

All commands follow this JSON structure:

```json
{
  "action": "action_name",
  "target": "app_or_window_name",
  "path": "file_or_folder_path",
  "extra": {
    "additional": "parameters"
  }
}
```

## Files

| File | Description |
|------|-------------|
| `windows_command_generator.py` | LLM-based command generator using SmolLM2 |
| `command_executor.py` | Executes structured JSON commands |
| `windows_automation.py` | Unified interface combining both |
| `setup_ollama.ps1` | PowerShell setup script |
| `setup_ollama.bat` | Batch setup script |

## Configuration

### Using a Different Model

```python
auto = WindowsAutomation(model_name="llama2")  # or any Ollama model
```

### Custom Ollama URL

```python
auto = WindowsAutomation(ollama_url="http://192.168.1.100:11434/api/generate")
```

## Troubleshooting

### Ollama not running
```
❌ Error: Cannot connect to Ollama. Make sure Ollama is running.
```
**Solution:** Start Ollama with `ollama serve`

### Model not found
```
⚠️ Model 'smollm2' not found.
```
**Solution:** Pull the model with `ollama pull smollm2`

### pyautogui not working
Some actions (window control, volume, keyboard) require pyautogui:
```bash
pip install pyautogui
```

## Integration with Zentrax

This module can be integrated with the main Zentrax voice/gesture control system. Add to `main.py`:

```python
from windows_automation import WindowsAutomation

class VoiceGestureControl:
    def __init__(self, ...):
        # ... existing code ...
        self.win_auto = WindowsAutomation()
    
    def process_voice_command(self, command):
        # Try Windows automation for unrecognized commands
        if command not in self.voice_commands:
            success, msg = self.win_auto.run(command)
            if success:
                print(f"✅ {msg}")
                return
        # ... rest of processing
```
